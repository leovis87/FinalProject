# app/core/socket_io.py
import asyncio
import json
import os
import sys
import socketio
import traceback
import random
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from random import randint

from langgraph.types import Command

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHS_DIR = os.path.join(BASE_DIR, "graphs")


def _import_debate_app():
    original_sys_path = list(sys.path)
    original_schemas = sys.modules.get("schemas")
    original_nodes = sys.modules.get("nodes")
    try:
        if GRAPHS_DIR not in sys.path:
            sys.path.insert(0, GRAPHS_DIR)
        from graphs.graph import debate_app as _debate_app
        return _debate_app
    finally:
        sys.path = original_sys_path
        if original_schemas is None:
            sys.modules.pop("schemas", None)
        else:
            sys.modules["schemas"] = original_schemas
        if original_nodes is None:
            sys.modules.pop("nodes", None)
        else:
            sys.modules["nodes"] = original_nodes


debate_app = _import_debate_app()
from core.database import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.debate_room import DebateRoom
from models.debate_message import DebateMessage
from models.debate_participant import DebateParticipant
from models.enums import DebateStatus, DebateRole, DebateResult, DebateDecisionBy
from schemas.debate import DebateResultUpsertRequest, DebateResultItem
from services.debate import debate_service

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
sio_app = socketio.ASGIApp(sio)

_room_states: Dict[str, dict] = {}
_room_locks: Dict[str, asyncio.Lock] = {}
_active_users: Dict[str, set] = {}
_sid_to_room: Dict[str, str] = {}
_sid_to_user: Dict[str, str] = {}
_turn_timers: Dict[str, asyncio.Task] = {}
_selection_timers: Dict[str, asyncio.Task] = {}

TURN_TIMEOUT_SEC = int(os.getenv("TURN_TIMEOUT_SEC", "90"))
SELECTION_TIMEOUT_SEC = int(os.getenv("SELECTION_TIMEOUT_SEC", "20"))


def _get_lock(room_id: str) -> asyncio.Lock:
    if room_id not in _room_locks:
        _room_locks[room_id] = asyncio.Lock()
    return _room_locks[room_id]


def _cancel_turn_timer(room_id: str) -> None:
    task = _turn_timers.pop(room_id, None)
    current = asyncio.current_task()
    if task and task is not current and not task.done():
        task.cancel()


def _start_turn_timer(room_state: dict, room_id_str: str) -> None:
    if TURN_TIMEOUT_SEC <= 0:
        room_state["turn_deadline"] = None
        return
    if room_state.get("is_finished"):
        room_state["turn_deadline"] = None
        return
    expected = _next_speaker(room_state)
    if not expected:
        room_state["turn_deadline"] = None
        return

    _cancel_turn_timer(room_id_str)
    expected_user_id = str(expected["user_id"])
    round_number = room_state.get("current_round")
    room_state["turn_deadline"] = datetime.now(timezone.utc) + timedelta(seconds=TURN_TIMEOUT_SEC)

    async def _timeout():
        try:
            await asyncio.sleep(TURN_TIMEOUT_SEC)
        except asyncio.CancelledError:
            return
        async with _get_lock(room_id_str):
            current_state = _room_states.get(room_id_str)
            if not current_state or current_state.get("is_finished"):
                return
            current_expected = _next_speaker(current_state)
            if not current_expected:
                return
            if str(current_expected["user_id"]) != expected_user_id:
                return
            if current_state.get("current_round") != round_number:
                return
            await _emit_system_message(current_state, "Moderator: 발언 시간이 종료되었습니다.")
            await _complete_turn(current_state, room_id_str, expected_user_id, reason="timeout")

    _turn_timers[room_id_str] = asyncio.create_task(_timeout())


def _cancel_selection_timer(room_id: str) -> None:
    task = _selection_timers.pop(room_id, None)
    current = asyncio.current_task()
    if task and task is not current and not task.done():
        task.cancel()


def _debug_payload(level: str, tag: str, room_id: Optional[str], user_id: Optional[str], detail: str) -> dict:
    return {
        "level": level,
        "tag": tag,
        "room_id": room_id,
        "user_id": user_id,
        "detail": detail,
        "ts": datetime.utcnow().isoformat(),
    }


def _debug_print(payload: dict, state: Optional[str] = None) -> None:
    room_id = payload.get("room_id")
    user_id = payload.get("user_id")
    detail = payload.get("detail")
    tag = payload.get("tag")
    state_text = state if state is not None else "-"
    print(f"[SOCKET][room={room_id}][user={user_id}][state={state_text}] {tag} {detail}")


async def _emit_debug(payload: dict, room_id: Optional[str], sid: Optional[str] = None) -> None:
    try:
        if room_id:
            await sio.emit("debug", payload, room=f"debate_{room_id}")
        elif sid:
            await sio.emit("debug", payload, to=sid)
    except Exception:
        traceback.print_exc()


async def _emit_error(message: str, room_id: Optional[str], sid: Optional[str] = None) -> None:
    payload = {"message": message}
    try:
        if sid:
            await sio.emit("error", payload, to=sid)
        elif room_id:
            await sio.emit("error", payload, room=f"debate_{room_id}")
    except Exception:
        traceback.print_exc()


async def _save_message(room_state: dict, message: dict) -> None:
    content = message.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(_to_json_safe(content), ensure_ascii=False)

    user_id = message.get("user_id")
    try:
        user_id = int(user_id) if user_id is not None else None
    except (TypeError, ValueError):
        user_id = None

    try:
        async with AsyncSessionLocal() as db:
            db_message = DebateMessage(
                debate_room_id=int(room_state["room_id"]),
                user_id=user_id,
                role=str(message.get("role", "system")),
                display_type=message.get("display_type"),
                content=content,
                turn=message.get("turn"),
            )
            db.add(db_message)
            await db.commit()
    except Exception:
        traceback.print_exc()

def _role_value(role) -> str:
    if isinstance(role, DebateRole):
        return role.value
    return str(role)


def _to_json_safe(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat(timespec="seconds")
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _sorted_participants(participants: List[DebateParticipant]) -> List[dict]:
    normalized = []
    for p in participants:
        role = _role_value(p.role)
        normalized.append(
            {
                "user_id": str(p.user_id),
                "user_name": p.nickname if hasattr(p, "nickname") else f"User_{p.user_id}",
                "side": role,
                "joined_at": getattr(p, "joined_at", None),
            }
        )
    normalized.sort(key=lambda x: (x["joined_at"] or datetime.min, int(x["user_id"])))
    return normalized


def _participants_payload(participants: List[DebateParticipant]) -> List[dict]:
    payload = []
    for p in participants:
        payload.append(
            {
                "user_id": int(p.user_id) if p.user_id is not None else p.user_id,
                "role": _role_value(p.role),
                "turn_order": getattr(p, "turn_order", None),
                "nickname": p.nickname if hasattr(p, "nickname") else f"User_{p.user_id}",
            }
        )
    return payload


def _build_room_state(room: DebateRoom, participants: List[DebateParticipant]) -> dict:
    ordered = _sorted_participants(participants)
    pro_users = [u for u in ordered if u["side"] == "pro"]
    con_users = [u for u in ordered if u["side"] == "con"]
    join_order = [u["user_id"] for u in ordered]
    join_index = {user_id: idx for idx, user_id in enumerate(join_order)}

    return {
        "room_id": str(room.debate_room_id),
        "topic": room.topic,
        "level": room.level.value if hasattr(room.level, "value") else str(room.level),
        "participants": ordered,
        "participant_map": {u["user_id"]: u for u in ordered},
        "pro_users": pro_users,
        "con_users": con_users,
        "join_order": join_order,
        "join_index": join_index,
        "current_round": 0,
        "turn_order": [],
        "turn_index": 0,
        "representative": {"pro": None, "con": None},
        "per_round_spoken_set": {},
        "round_messages": {},
        "messages": [],
        "dialogue_messages": [],
        "last_spoken": {u["user_id"]: 0 for u in ordered},
        "global_spoken_seq": 0,
        "topic_analysis": None,
        "is_finished": False,
        "draft_buffers": {},
        "selection_active": False,
        "selection_round": None,
        "selection_deadline": None,
        "selection_requests": {"pro": set(), "con": set()},
    }


def _graph_base_state(room_state: dict, include_premium: bool = False) -> dict:
    return {
        "room_id": int(room_state["room_id"]),
        "topic": room_state["topic"],
        "level": room_state.get("level"),
        "topic_analysis": room_state.get("topic_analysis"),
        "pro_users": [
            {
                "user_id": u["user_id"],
                "user_name": u["user_name"],
                "is_premium": include_premium,
            }
            for u in room_state["pro_users"]
        ],
        "con_users": [
            {
                "user_id": u["user_id"],
                "user_name": u["user_name"],
                "is_premium": include_premium,
            }
            for u in room_state["con_users"]
        ],
        "max_turns": 4,
        "current_turn": max(room_state.get("current_round", 1), 1),
        "messages": list(room_state.get("dialogue_messages", [])),
        "summary_history": [],
        "referee_warnings": [],
        "moderator_report": None,
        "premium_feedbacks": {},
        "latest_pro_message": "",
        "latest_con_message": "",
        "user_input": "",
        "needs_search": False,
        "search_result": "",
        "final_response": "",
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }


def _format_topic_analysis_parts(topic_analysis) -> Optional[dict]:
    if not topic_analysis:
        return None
    if hasattr(topic_analysis, "model_dump"):
        data = topic_analysis.model_dump()
    elif hasattr(topic_analysis, "dict"):
        data = topic_analysis.dict()
    elif isinstance(topic_analysis, dict):
        data = topic_analysis
    else:
        return {"summary": str(topic_analysis), "pro": "", "con": ""}

    description = data.get("description", "")
    pro_args = data.get("pro_args", [])
    con_args = data.get("con_args", [])
    return {
        "summary": description,
        "pro": "\n".join([f"- {item}" for item in pro_args if item]),
        "con": "\n".join([f"- {item}" for item in con_args if item]),
    }


def _format_moderator_report(report) -> str:
    if not report:
        return "Final evaluation is not available."
    if hasattr(report, "model_dump"):
        data = report.model_dump()
    elif hasattr(report, "dict"):
        data = report.dict()
    elif isinstance(report, dict):
        data = report
    else:
        return str(report)

    pro_eval = data.get("pro_eval", {}) or {}
    con_eval = data.get("con_eval", {}) or {}
    lines = [
        "Final summary:",
        f"PRO summary: {data.get('general_summary', '')}",
        "",
        f"PRO score: {pro_eval.get('total_score', 'N/A')}",
        f"CON score: {con_eval.get('total_score', 'N/A')}",
    ]
    if data.get("best_player"):
        lines.append(f"Best player: {data['best_player']}")
    return "\n".join(lines)


def _parse_total_score(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_result_payload(room_state: dict, report_data: Optional[dict]) -> Optional[DebateResultUpsertRequest]:
    if not report_data:
        return None

    pro_eval = report_data.get("pro_eval") or {}
    con_eval = report_data.get("con_eval") or {}
    pro_score = _parse_total_score(pro_eval.get("total_score"))
    con_score = _parse_total_score(con_eval.get("total_score"))

    if pro_score is None or con_score is None:
        return None

    if pro_score > con_score:
        pro_result = DebateResult.WIN
        con_result = DebateResult.LOSE
    elif pro_score < con_score:
        pro_result = DebateResult.LOSE
        con_result = DebateResult.WIN
    else:
        pro_result = DebateResult.DRAW
        con_result = DebateResult.DRAW

    results = []
    for participant in room_state.get("participants", []):
        side = participant.get("side")
        if side == "pro":
            result = pro_result
        elif side == "con":
            result = con_result
        else:
            continue
        try:
            user_id = int(participant.get("user_id"))
        except (TypeError, ValueError):
            continue
        results.append(DebateResultItem(user_id=user_id, result=result))

    if not results:
        return None

    return DebateResultUpsertRequest(
        results=results,
        result_reason=report_data.get("general_summary") or "",
        decided_by=DebateDecisionBy.AI
    )


def _choose_representative(users: List[dict], room_state: dict) -> Optional[dict]:
    spoken = room_state["per_round_spoken_set"].get(room_state["current_round"], set())
    candidates = [u for u in users if u["user_id"] not in spoken]
    if not candidates:
        return None
    join_index = room_state["join_index"]
    last_spoken = room_state["last_spoken"]
    candidates.sort(key=lambda u: (last_spoken.get(u["user_id"], 0), join_index[u["user_id"]]))
    return candidates[0]


def _prepare_round(room_state: dict, round_number: int) -> None:
    room_state["current_round"] = round_number
    room_state["turn_index"] = 0
    room_state["per_round_spoken_set"][round_number] = set()
    room_state["round_messages"][round_number] = []
    room_state["draft_buffers"] = {}


def _set_round(room_state: dict, round_number: int) -> List[str]:
    _prepare_round(room_state, round_number)
    room_state["selection_active"] = False
    room_state["selection_round"] = None
    room_state["selection_deadline"] = None
    room_state["selection_requests"] = {"pro": set(), "con": set()}
    skipped = []

    if round_number in (2, 3):
        rep_pro = _choose_representative(room_state["pro_users"], room_state)
        rep_con = _choose_representative(room_state["con_users"], room_state)
        room_state["representative"] = {
            "pro": rep_pro["user_id"] if rep_pro else None,
            "con": rep_con["user_id"] if rep_con else None,
        }
        turn_order = []
        if rep_pro:
            turn_order.append(rep_pro)
        else:
            skipped.append("PRO")
        if rep_con:
            turn_order.append(rep_con)
        else:
            skipped.append("CON")
        room_state["turn_order"] = turn_order
        return skipped

    room_state["representative"] = {"pro": None, "con": None}
    room_state["turn_order"] = list(room_state["participants"])
    return skipped


def _needs_selection(room_state: dict, round_number: int) -> bool:
    if round_number not in (2, 3):
        return False
    if SELECTION_TIMEOUT_SEC <= 0:
        return False
    return len(room_state.get("pro_users", [])) > 1 or len(room_state.get("con_users", [])) > 1


def _start_selection_phase(room_state: dict, room_id_str: str, round_number: int) -> None:
    _cancel_turn_timer(room_id_str)
    _cancel_selection_timer(room_id_str)
    _prepare_round(room_state, round_number)
    room_state["representative"] = {"pro": None, "con": None}
    room_state["turn_order"] = []
    room_state["turn_deadline"] = None
    room_state["selection_active"] = True
    room_state["selection_round"] = round_number
    room_state["selection_deadline"] = datetime.now(timezone.utc) + timedelta(seconds=SELECTION_TIMEOUT_SEC)
    room_state["selection_requests"] = {"pro": set(), "con": set()}

    async def _timeout():
        try:
            await asyncio.sleep(SELECTION_TIMEOUT_SEC)
        except asyncio.CancelledError:
            return
        async with _get_lock(room_id_str):
            current_state = _room_states.get(room_id_str)
            if not current_state or current_state.get("is_finished"):
                return
            if not current_state.get("selection_active"):
                return
            if current_state.get("selection_round") != round_number:
                return
            await _finalize_selection(current_state, room_id_str)

    _selection_timers[room_id_str] = asyncio.create_task(_timeout())


def _pick_representative_from_requests(room_state: dict, side: str) -> Optional[dict]:
    requests = room_state.get("selection_requests", {}).get(side, set())
    candidates = [
        u for u in room_state.get(f"{side}_users", [])
        if str(u["user_id"]) in requests
    ]
    if candidates:
        return random.choice(candidates)
    return _choose_representative(room_state.get(f"{side}_users", []), room_state)


async def _finalize_selection(room_state: dict, room_id_str: str) -> None:
    _cancel_selection_timer(room_id_str)
    room_state["selection_active"] = False
    room_state["selection_deadline"] = None
    room_state["selection_round"] = None

    rep_pro = _pick_representative_from_requests(room_state, "pro")
    rep_con = _pick_representative_from_requests(room_state, "con")

    room_state["representative"] = {
        "pro": rep_pro["user_id"] if rep_pro else None,
        "con": rep_con["user_id"] if rep_con else None,
    }

    skipped = []
    turn_order = []
    if rep_pro:
        turn_order.append(rep_pro)
    else:
        skipped.append("PRO")
    if rep_con:
        turn_order.append(rep_con)
    else:
        skipped.append("CON")

    room_state["turn_order"] = turn_order
    room_state["turn_index"] = 0
    room_state["selection_requests"] = {"pro": set(), "con": set()}

    if skipped:
        for side in skipped:
            await _emit_system_message(room_state, f"Moderator: {side} has no available speaker. Skipping.")

    _start_turn_timer(room_state, room_id_str)
    await sio.emit(
        "debate_update",
        {
            "messages": [],
            "replace_messages": False,
            **_round_payload(room_state),
        },
        room=f"debate_{room_id_str}",
    )


def _round_status(round_number: int) -> DebateStatus:
    mapping = {
        1: DebateStatus.IN_PROGRESS_INTRO,
        2: DebateStatus.IN_PROGRESS_REBUTTAL,
        3: DebateStatus.IN_PROGRESS_REREBUTTAL,
        4: DebateStatus.IN_PROGRESS_CONCLUSION,
    }
    return mapping.get(round_number, DebateStatus.FINISHED)


def _next_speaker(room_state: dict) -> Optional[dict]:
    order = room_state.get("turn_order", [])
    idx = room_state.get("turn_index", 0)
    if idx < len(order):
        return order[idx]
    return None


def _round_payload(room_state: dict) -> dict:
    expected = _next_speaker(room_state)
    payload = {
        "current_round": room_state.get("current_round"),
        "turn_index": room_state.get("turn_index"),
        "turn_total": len(room_state.get("turn_order", [])),
        "next_speaker": expected,
        "turn_deadline": room_state.get("turn_deadline"),
        "selection_active": room_state.get("selection_active", False),
        "selection_deadline": room_state.get("selection_deadline"),
        "selection_round": room_state.get("selection_round"),
    }
    return _to_json_safe(payload)


def _message_payload(message: dict, room_state: dict, replace: bool = False) -> dict:
    payload = {"messages": [message], "replace_messages": replace}
    payload.update(_round_payload(room_state))
    return payload


def _participant_for(room_state: dict, user_id: str) -> Optional[dict]:
    return room_state.get("participant_map", {}).get(str(user_id))


def _graph_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id, "is_stream": False}}


def _make_system_message(room_state: dict, content: str) -> dict:
    return {
        "turn": room_state.get("current_round", 0),
        "role": "ai",
        "user_name": "Moderator",
        "content": content,
    }


def _sids_for_user(room_id_str: str, user_id: str) -> List[str]:
    targets = []
    for sid, room_id in _sid_to_room.items():
        if room_id != room_id_str:
            continue
        if str(_sid_to_user.get(sid)) == str(user_id):
            targets.append(sid)
    return targets


def _filter_messages_for_user(messages: List[dict], user_id: Optional[str]) -> List[dict]:
    if not messages:
        return []
    filtered = []
    for message in messages:
        if message.get("display_type") == "report_user":
            if user_id is None or str(message.get("user_id")) != str(user_id):
                continue
        filtered.append(message)
    return filtered


async def _get_personal_feedbacks(room_state: dict) -> Dict[str, dict]:
    state = _graph_base_state(room_state, include_premium=True)
    state["messages"] = list(room_state.get("dialogue_messages", []))
    config = _graph_config(f"debate_{room_state['room_id']}_personal")

    feedbacks: Dict[str, dict] = {}

    try:
        pro_result = await debate_app.ainvoke(Command(update=state, goto="pro_feedback"), config)
        if isinstance(pro_result, dict):
            feedbacks.update(pro_result.get("premium_feedbacks", {}) or {})
    except Exception:
        traceback.print_exc()

    try:
        con_result = await debate_app.ainvoke(Command(update=state, goto="con_feedback"), config)
        if isinstance(con_result, dict):
            feedbacks.update(con_result.get("premium_feedbacks", {}) or {})
    except Exception:
        traceback.print_exc()

    return _to_json_safe(feedbacks) or {}


async def _emit_personal_feedback(room_state: dict, user_id: str, report: dict) -> None:
    message = {
        "turn": room_state.get("current_round", 0),
        "role": "ai",
        "user_id": str(user_id),
        "user_name": "Moderator",
        "content": report,
        "display_type": "report_user",
    }
    room_state["messages"].append(message)
    await _save_message(room_state, message)

    room_id_str = str(room_state["room_id"])
    for sid in _sids_for_user(room_id_str, str(user_id)):
        await sio.emit(
            "debate_update",
            _message_payload(message, room_state, replace=False),
            to=sid,
        )


async def _emit_system_message(room_state: dict, content: str) -> None:
    message = _make_system_message(room_state, content)
    room_state["messages"].append(message)
    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_state['room_id']}",
    )


def _make_loading_message(room_state: dict, content: str) -> dict:
    return {
        "turn": room_state.get("current_round", 0),
        "role": "ai",
        "user_name": "Moderator",
        "content": content,
        "display_type": "loading",
    }


async def _emit_loading_message(room_state: dict, content: str) -> None:
    message = _make_loading_message(room_state, content)
    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_state['room_id']}",
    )


async def _emit_loading_end(room_state: dict) -> None:
    message = {
        "turn": room_state.get("current_round", 0),
        "role": "ai",
        "user_name": "Moderator",
        "content": "",
        "display_type": "loading_end",
    }
    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_state['room_id']}",
    )


async def _run_topic_summary(room_state: dict) -> Optional[dict]:
    state = _graph_base_state(room_state)
    config = _graph_config(f"debate_{room_state['room_id']}_topic")
    result = await debate_app.ainvoke(Command(update=state, goto="analyze_topic"), config)
    return result.get("topic_analysis") if isinstance(result, dict) else None


async def _run_round_summary(room_state: dict, round_number: int) -> str:
    state = _graph_base_state(room_state)
    state["current_turn"] = round_number
    state["messages"] = list(room_state["round_messages"].get(round_number, []))
    config = _graph_config(f"debate_{room_state['room_id']}_summary_{round_number}")
    result = await debate_app.ainvoke(Command(update=state, goto="summary"), config)
    summary_history = []
    if isinstance(result, dict):
        summary_history = result.get("summary_history", [])
    if summary_history:
        return summary_history[-1]
    return f"[Round {round_number}] Summary unavailable."


def _parse_round_summary(summary_text: str) -> Optional[dict]:
    if not summary_text:
        return None
    lines = [line.strip() for line in summary_text.splitlines() if line.strip()]
    pro_text = ""
    con_text = ""
    for line in lines:
        if not pro_text:
            match = re.search(r"(?:🔵\s*)?찬성\s*[:：]\s*(.+)", line)
            if match:
                pro_text = match.group(1).strip()
                continue
        if not con_text:
            match = re.search(r"(?:🔴\s*)?반대\s*[:：]\s*(.+)", line)
            if match:
                con_text = match.group(1).strip()
                continue
    if not pro_text and not con_text:
        return None
    return {"pro": pro_text, "con": con_text}


def _split_summary_lines(text: str) -> List[str]:
    if not text:
        return []
    lines = []
    for raw in text.splitlines():
        cleaned = raw.strip()
        if not cleaned:
            continue
        if cleaned.startswith("- "):
            cleaned = cleaned[2:].strip()
        elif cleaned.startswith("• "):
            cleaned = cleaned[2:].strip()
        lines.append(cleaned)
    return lines


async def _complete_turn(
    room_state: dict,
    room_id_str: str,
    user_id: str,
    sid: Optional[str] = None,
    reason: str = "manual",
) -> None:
    expected = _next_speaker(room_state)
    if expected and str(expected["user_id"]) != str(user_id):
        await sio.emit("debate_error", {"message": "Not your turn."}, to=sid)
        return

    _cancel_turn_timer(room_id_str)

    buffer = room_state.get("draft_buffers", {}).pop(str(user_id), [])
    combined = " ".join([chunk.strip() for chunk in buffer if chunk.strip()]).strip()
    if not combined:
        combined = "발언 없음"

    participant = _participant_for(room_state, str(user_id))
    role = participant["side"] if participant else "user"
    user_name = participant["user_name"] if participant else f"User_{user_id}"

    message = {
        "turn": room_state["current_round"],
        "role": role,
        "user_id": str(user_id),
        "user_name": user_name,
        "content": combined,
    }

    room_state["messages"].append(message)
    room_state["dialogue_messages"].append(message)
    room_state["round_messages"].setdefault(room_state["current_round"], []).append(message)
    await _save_message(room_state, message)

    room_state["turn_index"] += 1
    room_state["global_spoken_seq"] += 1
    room_state["last_spoken"][str(user_id)] = room_state["global_spoken_seq"]
    room_state["per_round_spoken_set"][room_state["current_round"]].add(str(user_id))

    has_next_turn = room_state["turn_index"] < len(room_state["turn_order"])
    if has_next_turn:
        _start_turn_timer(room_state, room_id_str)

    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_id_str}",
    )

    if has_next_turn:
        return

    round_number = room_state["current_round"]

    try:
        await _emit_loading_message(room_state, "AI가 입력중입니다")
        summary_text = await _run_round_summary(room_state, round_number)
        parts = _parse_round_summary(summary_text)
        if not parts:
            await _emit_system_message(room_state, summary_text)
        else:
            pro_lines = _split_summary_lines(parts.get("pro", ""))
            con_lines = _split_summary_lines(parts.get("con", ""))
            await _emit_system_message(
                room_state,
                {
                    "round": round_number,
                    "title": f"{round_number}라운드 요약",
                    "pro_items": pro_lines,
                    "con_items": con_lines,
                },
                "summary_round",
            )
    except Exception:
        traceback.print_exc()
    finally:
        await _emit_loading_end(room_state)

    if round_number >= 4:
        await _finalize_debate(room_state, room_id_str, sid=sid)
        return

    next_round = round_number + 1

    if _needs_selection(room_state, next_round):
        _start_selection_phase(room_state, room_id_str, next_round)
        await _emit_system_message(room_state, "Moderator: 발언 신청을 시작합니다.")

        async with AsyncSessionLocal() as db:
            room = await db.get(DebateRoom, int(room_id_str))
            if room:
                room.status = _round_status(next_round)
                await db.commit()

        await sio.emit(
            "debate_update",
            {
                "messages": [],
                "replace_messages": False,
                **_round_payload(room_state),
            },
            room=f"debate_{room_id_str}",
        )
        return

    skipped = _set_round(room_state, next_round)
    if skipped:
        for side in skipped:
            await _emit_system_message(room_state, f"Moderator: {side} has no available speaker. Skipping.")

    async with AsyncSessionLocal() as db:
        room = await db.get(DebateRoom, int(room_id_str))
        if room:
            room.status = _round_status(next_round)
            await db.commit()

    _start_turn_timer(room_state, room_id_str)
    await sio.emit(
        "debate_update",
        {
            "messages": [],
            "replace_messages": False,
            **_round_payload(room_state),
        },
        room=f"debate_{room_id_str}",
    )


# 1. 기존의 _format_moderator_report는 삭제하고 이 함수를 추가하세요.
async def _get_final_report_data(room_state: dict) -> Optional[dict]:
    """사회자 최종 리포트 객체를 생성하고 JSON safe한 dict로 반환합니다."""
    state = _graph_base_state(room_state)
    state["messages"] = list(room_state.get("dialogue_messages", []))
    config = _graph_config(f"debate_{room_state['room_id']}_final")
    
    # LangGraph 실행 (moderator_shared 노드로 이동)
    result = await debate_app.ainvoke(Command(update=state, goto="moderator_shared"), config)
    report = result.get("moderator_report") if isinstance(result, dict) else None
    
    # Pydantic 모델이나 객체를 JSON으로 보낼 수 있게 dict로 변환
    return _to_json_safe(report)

# 2. 시스템 메시지에 display_type을 넣을 수 있도록 수정하세요.
async def _finalize_debate(room_state: dict, room_id_str: str, sid: Optional[str] = None) -> None:
    _cancel_turn_timer(room_id_str)
    _cancel_selection_timer(room_id_str)
    room_state["turn_deadline"] = None
    room_state["selection_active"] = False
    room_state["selection_deadline"] = None
    room_state["selection_round"] = None
    report_data = None
    try:
        await _emit_loading_message(room_state, "AI가 입력중입니다")
        report_data = await _get_final_report_data(room_state)
        if report_data:
            await _emit_system_message(room_state, report_data.get("general_summary", ""), "report_summary")
            await _emit_system_message(room_state, report_data.get("pro_eval", {}), "report_pro")
            await _emit_system_message(room_state, report_data.get("con_eval", {}), "report_con")
            if report_data.get("best_player"):
                await _emit_system_message(room_state, report_data["best_player"], "report_mvp")
    except Exception:
        traceback.print_exc()
        await _emit_error("Final report failed.", room_id_str, sid=sid)
    finally:
        await _emit_loading_end(room_state)

    try:
        personal_feedbacks = await _get_personal_feedbacks(room_state)
        if personal_feedbacks:
            for user_id, report in personal_feedbacks.items():
                if not isinstance(report, dict):
                    report = {"message": str(report)}
                await _emit_personal_feedback(room_state, user_id, report)
    except Exception:
        traceback.print_exc()

    saved_result = False
    payload = _build_result_payload(room_state, report_data)
    if payload:
        try:
            async with AsyncSessionLocal() as db:
                await debate_service.set_debate_results(db, int(room_id_str), payload)
            saved_result = True
        except Exception:
            traceback.print_exc()
            await _emit_error("Final result save failed.", room_id_str, sid=sid)

    if not saved_result:
        async with AsyncSessionLocal() as db:
            room = await db.get(DebateRoom, int(room_id_str))
            if room:
                room.status = DebateStatus.FINISHED
                if not room.finished_at:
                    room.finished_at = datetime.utcnow()
                await db.commit()

    room_state["is_finished"] = True
    await sio.emit("debate_ended", {"room_id": room_id_str}, room=f"debate_{room_id_str}")


async def _emit_system_message(room_state: dict, content: str, display_type: str = "moderator") -> None:
    message = {
        "turn": room_state.get("current_round", 0),
        "role": "ai",
        "user_name": "Moderator",
        "content": content,
        "display_type": display_type  # 프론트에서 '찢어서' 보게 해주는 핵심 키
    }
    room_state["messages"].append(message)
    await _save_message(room_state, message)
    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_state['room_id']}",
    )


async def _close_room_if_empty(room_id_str: str, room_state: Optional[dict]) -> None:
    active_count = len(_active_users.get(room_id_str, set()))
    if active_count > 0:
        return

    if room_state and room_state.get("is_finished"):
        return

    _cancel_turn_timer(room_id_str)
    _cancel_selection_timer(room_id_str)

    if room_state:
        room_state["is_finished"] = True
        room_state["turn_deadline"] = None
        room_state["selection_active"] = False
        room_state["selection_deadline"] = None
        room_state["selection_round"] = None

    async with AsyncSessionLocal() as db:
        room = await db.get(DebateRoom, int(room_id_str))
        if room and room.status != DebateStatus.FINISHED:
            room.status = DebateStatus.FINISHED
            if not room.finished_at:
                room.finished_at = datetime.utcnow()
            await db.commit()

    await sio.emit("debate_ended", {"room_id": room_id_str}, room=f"debate_{room_id_str}")


@sio.event
async def connect(sid, environ):
    payload = _debug_payload("info", "CONNECT", None, None, f"sid={sid}")
    _debug_print(payload)
    await _emit_debug(payload, None, sid=sid)


@sio.on("join_debate")
async def handle_join(sid, data):
    room_id = str(data.get("room_id"))
    user_id = data.get("user_id")
    await sio.enter_room(sid, f"debate_{room_id}")
    _sid_to_room[sid] = room_id
    if user_id is not None:
        _sid_to_user[sid] = str(user_id)
        _active_users.setdefault(room_id, set()).add(str(user_id))

    side = None
    participant_count = 0
    active_count = len(_active_users.get(room_id, set()))
    participants = []
    try:
        async with AsyncSessionLocal() as db:
            part_stmt = (
                select(DebateParticipant)
                .options(selectinload(DebateParticipant.user))
                .where(DebateParticipant.debate_room_id == int(room_id))
            )
            part_result = await db.execute(part_stmt)
            participants = part_result.scalars().all()
            participant_count = len(participants)
            if user_id is not None:
                for p in participants:
                    if str(p.user_id) == str(user_id):
                        side = _role_value(p.role)
                        break
    except Exception:
        traceback.print_exc()
        await _emit_error("Failed to load participants.", room_id, sid=sid)

    payload = _debug_payload(
        "info",
        "JOIN",
        room_id,
        str(user_id) if user_id is not None else None,
        f"side={side} total_count={participant_count} active_count={active_count}",
    )
    _debug_print(payload)
    await _emit_debug(payload, room_id, sid=sid)

    if participants:
        await sio.emit("participants_update", {"participants": _participants_payload(participants)}, room=f"debate_{room_id}")

    if room_id in _room_states:
        room_state = _room_states[room_id]
        safe_messages = _filter_messages_for_user(
            list(room_state.get("messages", [])),
            str(user_id) if user_id is not None else None,
        )
        await sio.emit(
            "debate_update",
            {
                "messages": safe_messages,
                "replace_messages": True,
                **_round_payload(room_state),
            },
            to=sid,
        )


@sio.on("start_debate")
async def handle_start(sid, data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    if not room_id or not user_id:
        return

    room_id_str = str(room_id)
    lock = _get_lock(room_id_str)

    async with lock:
        payload = _debug_payload("info", "START", room_id_str, str(user_id), "start_debate received")
        _debug_print(payload)
        await _emit_debug(payload, room_id_str, sid=sid)

        async with AsyncSessionLocal() as db:
            try:
                room = await db.get(DebateRoom, int(room_id))
                if not room:
                    await sio.emit("debate_error", {"message": "Room not found."}, to=sid)
                    await _emit_error("Room not found.", room_id_str, sid=sid)
                    reject_payload = _debug_payload(
                        "warn", "START", room_id_str, str(user_id), "room not found"
                    )
                    _debug_print(reject_payload)
                    await _emit_debug(reject_payload, room_id_str, sid=sid)
                    return

                if room.creator_id != int(user_id):
                    await sio.emit("debate_error", {"message": "Only the creator can start."}, to=sid)
                    await _emit_error("Only the creator can start.", room_id_str, sid=sid)
                    reject_payload = _debug_payload(
                        "warn", "START", room_id_str, str(user_id), "not creator"
                    )
                    _debug_print(reject_payload)
                    await _emit_debug(reject_payload, room_id_str, sid=sid)
                    return

                if room.status != DebateStatus.WAITING:
                    await sio.emit("debate_error", {"message": "Room already started."}, to=sid)
                    await _emit_error("Room already started.", room_id_str, sid=sid)
                    reject_payload = _debug_payload(
                        "warn", "START", room_id_str, str(user_id), f"status={room.status}"
                    )
                    _debug_print(reject_payload, state=str(room.status))
                    await _emit_debug(reject_payload, room_id_str, sid=sid)
                    return

                part_stmt = (
                    select(DebateParticipant)
                    .options(selectinload(DebateParticipant.user))
                    .where(DebateParticipant.debate_room_id == int(room_id))
                )
                part_result = await db.execute(part_stmt)
                participants = part_result.scalars().all()
                if not participants:
                    await sio.emit("debate_error", {"message": "No participants."}, to=sid)
                    await _emit_error("No participants.", room_id_str, sid=sid)
                    reject_payload = _debug_payload(
                        "warn", "START", room_id_str, str(user_id), "participants=0"
                    )
                    _debug_print(reject_payload)
                    await _emit_debug(reject_payload, room_id_str, sid=sid)
                    return

                if len(participants) < 2:
                    await sio.emit("debate_error", {"message": "Not enough participants."}, to=sid)
                    await _emit_error("Not enough participants.", room_id_str, sid=sid)
                    reject_payload = _debug_payload(
                        "warn",
                        "START",
                        room_id_str,
                        str(user_id),
                        f"participants={len(participants)}",
                    )
                    _debug_print(reject_payload)
                    await _emit_debug(reject_payload, room_id_str, sid=sid)
                    return

                room_state = _build_room_state(room, participants)
                _room_states[room_id_str] = room_state
                start_msgs = [
                    "여러분의 멋진 생각을 들려줄 토론의 문이 열렸습니다.\n준비한 만큼 당당하게 이야기를 시작해 볼까요?",
                    "기다리던 토론 시간입니다!\n반짝이는 아이디어와 날카로운 논리가 가득한 시간, 지금 바로 시작합니다.",
                    "토론 시작!\n친구의 생각에 귀를 기울이며 논리적인 대화를 나누어 보아요.",
                    "생각의 힘을 기르는 토론의 장이 마련되었습니다.\n서로 다른 의견이 만나 어떤 결론을 만들어낼지 기대하며 시작해 보겠습니다."
                ]
                num_msg = randint(0, len(start_msgs) - 1)
                await _emit_system_message(room_state, start_msgs[num_msg])

                # Topic summary at debate start (LLM).
                try:
                    await _emit_loading_message(room_state, "AI가 입력중입니다")
                    graph_payload = _debug_payload("info", "GRAPH", room_id_str, str(user_id), "topic_summary start")
                    _debug_print(graph_payload, state=str(room.status))
                    await _emit_debug(graph_payload, room_id_str, sid=sid)
                    topic_analysis = await _run_topic_summary(room_state)
                    room_state["topic_analysis"] = topic_analysis
                    parts = _format_topic_analysis_parts(topic_analysis)
                    if not parts:
                        await _emit_system_message(room_state, "Topic summary is not available.")
                    else:
                        pro_lines = _split_summary_lines(parts.get("pro", ""))
                        con_lines = _split_summary_lines(parts.get("con", ""))
                        await _emit_system_message(
                            room_state,
                            {
                                "title": "토론 주제 요약",
                                "summary": parts.get("summary", ""),
                                "pro_items": pro_lines,
                                "con_items": con_lines,
                            },
                            "summary_topic",
                        )
                    graph_payload = _debug_payload("info", "GRAPH", room_id_str, str(user_id), "topic_summary done")
                    _debug_print(graph_payload, state=str(room.status))
                    await _emit_debug(graph_payload, room_id_str, sid=sid)
                except Exception:
                    traceback.print_exc()
                    await _emit_error("Topic summary failed.", room_id_str, sid=sid)
                finally:
                    await _emit_loading_end(room_state)

                _set_round(room_state, 1)
                previous_status = room.status
                room.status = _round_status(1)
                room.started_at = datetime.utcnow()
                await db.commit()
                state_payload = _debug_payload(
                    "info",
                    "STATE",
                    room_id_str,
                    str(user_id),
                    f"{previous_status} -> {room.status}",
                )
                _debug_print(state_payload, state=str(room.status))
                await _emit_debug(state_payload, room_id_str, sid=sid)

                _start_turn_timer(room_state, room_id_str)
                await sio.emit(
                    "debate_update",
                    {
                        "messages": [],
                        "replace_messages": False,
                        **_round_payload(room_state),
                    },
                    room=f"debate_{room_id_str}",
                )
                await sio.emit("debate_started", {"room_id": room_id}, room=f"debate_{room_id_str}")
            except Exception:
                print("Error while starting debate")
                traceback.print_exc()
                await _emit_error("Failed to start debate.", room_id_str, sid=sid)


@sio.on("end_debate")
async def handle_end(sid, data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    if not room_id or not user_id:
        return

    room_id_str = str(room_id)
    lock = _get_lock(room_id_str)

    async with lock:
        payload = _debug_payload("info", "END", room_id_str, str(user_id), "end_debate received")
        _debug_print(payload)
        await _emit_debug(payload, room_id_str, sid=sid)

        async with AsyncSessionLocal() as db:
            try:
                room = await db.get(DebateRoom, int(room_id))
                if not room:
                    await sio.emit("debate_error", {"message": "토론방을 찾을 수 없습니다.."}, to=sid)
                    await _emit_error("Room not found.", room_id_str, sid=sid)
                    return

                if room.creator_id != int(user_id):
                    await sio.emit("debate_error", {"message": "방장이 토론을 종료 할 수 있습니다."}, to=sid)
                    await _emit_error("Only the creator can end the debate.", room_id_str, sid=sid)
                    return

                if room.status == DebateStatus.FINISHED:
                    await sio.emit("debate_ended", {"room_id": room_id_str}, room=f"debate_{room_id_str}")
                    return

                room_state = _room_states.get(room_id_str)
                if room_state:
                    await _emit_system_message(room_state, "방장에 의해 토론이 종료되었습니다.")
                    await _finalize_debate(room_state, room_id_str, sid=sid)
                else:
                    room.status = DebateStatus.FINISHED
                    if not room.finished_at:
                        room.finished_at = datetime.utcnow()
                    await db.commit()
                    await sio.emit("debate_ended", {"room_id": room_id_str}, room=f"debate_{room_id_str}")
            except Exception:
                traceback.print_exc()
                await _emit_error("Failed to end debate.", room_id_str, sid=sid)


@sio.on("end_speaking")
async def handle_end_speaking(sid, data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    if not room_id or not user_id:
        return

    room_id_str = str(room_id)
    lock = _get_lock(room_id_str)

    async with lock:
        room_state = _room_states.get(room_id_str)
        if not room_state:
            await sio.emit("debate_error", {"message": "Room state not ready."}, to=sid)
            return

        if room_state.get("is_finished"):
            await sio.emit("debate_error", {"message": "Debate has ended."}, to=sid)
            return

        if room_state.get("selection_active"):
            await sio.emit("debate_error", {"message": "Selection in progress."}, to=sid)
            return

        if room_state.get("current_round", 0) == 0:
            await sio.emit("debate_error", {"message": "Debate has not started."}, to=sid)
            return

        expected = _next_speaker(room_state)
        if not expected or str(expected["user_id"]) != str(user_id):
            await sio.emit("debate_error", {"message": "Not your turn."}, to=sid)
            return

        await _complete_turn(room_state, room_id_str, str(user_id), sid=sid, reason="manual")


@sio.on("raise_hand")
async def handle_raise_hand(sid, data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    if not room_id or not user_id:
        return

    room_id_str = str(room_id)
    lock = _get_lock(room_id_str)

    async with lock:
        room_state = _room_states.get(room_id_str)
        if not room_state:
            await sio.emit("debate_error", {"message": "Room state not ready."}, to=sid)
            return

        if room_state.get("is_finished"):
            await sio.emit("debate_error", {"message": "Debate has ended."}, to=sid)
            return

        if not room_state.get("selection_active"):
            await sio.emit("debate_error", {"message": "Selection is not active."}, to=sid)
            return

        participant = _participant_for(room_state, str(user_id))
        if not participant:
            await sio.emit("debate_error", {"message": "You are not a participant."}, to=sid)
            return

        side = participant.get("side")
        if side not in ("pro", "con"):
            await sio.emit("debate_error", {"message": "Observers cannot request to speak."}, to=sid)
            return

        room_state.setdefault("selection_requests", {"pro": set(), "con": set()})
        room_state["selection_requests"].setdefault(side, set()).add(str(user_id))


@sio.on("send_message")
async def handle_message(sid, data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    content = data.get("content")

    if not room_id or not user_id:
        return
    if not content:
        return
    content = content.strip()
    if not content:
        return

    room_id_str = str(room_id)
    lock = _get_lock(room_id_str)

    async with lock:
        room_state = _room_states.get(room_id_str)
        if not room_state:
            await sio.emit("debate_error", {"message": "Room state not ready."}, to=sid)
            return

        if room_state.get("is_finished"):
            await sio.emit("debate_error", {"message": "Debate has ended."}, to=sid)
            return

        if room_state.get("selection_active"):
            await sio.emit("debate_error", {"message": "Selection in progress."}, to=sid)
            return

        if room_state.get("current_round", 0) == 0:
            await sio.emit("debate_error", {"message": "Debate has not started."}, to=sid)
            return

        participant = _participant_for(room_state, str(user_id))
        if not participant:
            await sio.emit("debate_error", {"message": "You are not a participant."}, to=sid)
            return

        # 발언권 체크
        expected = _next_speaker(room_state)
        if expected and expected["user_id"] != str(user_id):
            await sio.emit("debate_error", {
                "message": f"Not your turn. Next speaker: {expected['user_name']}.",
                "next_speaker": expected,
            }, to=sid)
            return

        role = participant["side"]
        room_state.setdefault("draft_buffers", {})
        room_state["draft_buffers"].setdefault(str(user_id), []).append(content)

        draft_message = {
            "turn": room_state["current_round"],
            "role": role,
            "user_id": str(user_id),
            "user_name": data.get("user_name") or participant["user_name"],
            "content": content,
            "display_type": "draft",
        }

        await sio.emit(
            "debate_update",
            _message_payload(draft_message, room_state, replace=False),
            room=f"debate_{room_id_str}",
        )

@sio.on("leave_debate")
async def handle_leave_debate(sid, data):
    room_id = str(data.get("room_id")) if data else None
    user_id = str(data.get("user_id")) if data and data.get("user_id") is not None else None

    mapped_room = _sid_to_room.pop(sid, None)
    mapped_user = _sid_to_user.pop(sid, None)
    if mapped_room:
        room_id = mapped_room
    if mapped_user:
        user_id = mapped_user

    if room_id:
        await sio.leave_room(sid, f"debate_{room_id}")

    if room_id and user_id:
        if room_id in _active_users:
            _active_users[room_id].discard(user_id)

        active_count = len(_active_users.get(room_id, set()))
        side = None
        total_count = None
        room_state = _room_states.get(room_id)
        if room_state:
            participant = _participant_for(room_state, user_id)
            if participant:
                side = participant.get("side")
            total_count = len(room_state.get("participants", []))
        payload = _debug_payload(
            "info",
            "LEAVE",
            room_id,
            user_id,
            f"side={side} total_count={total_count} active_count={active_count}",
        )
        _debug_print(payload)
        await _emit_debug(payload, room_id, sid=sid)
        await _close_room_if_empty(room_id, room_state)

@sio.event
async def disconnect(sid):
    room_id = _sid_to_room.pop(sid, None)
    user_id = _sid_to_user.pop(sid, None)
    if room_id and user_id:
        if room_id in _active_users:
            _active_users[room_id].discard(user_id)
        active_count = len(_active_users.get(room_id, set()))
        side = None
        total_count = None
        room_state = _room_states.get(room_id)
        if room_state:
            participant = _participant_for(room_state, str(user_id))
            if participant:
                side = participant.get("side")
            total_count = len(room_state.get("participants", []))
        payload = _debug_payload(
            "info",
            "LEAVE",
            room_id,
            user_id,
            f"side={side} total_count={total_count} active_count={active_count}",
        )
        _debug_print(payload)
        await _emit_debug(payload, room_id, sid=sid)
        await _close_room_if_empty(room_id, room_state)
    payload = _debug_payload("info", "DISCONNECT", None, None, f"sid={sid}")
    _debug_print(payload)
    await _emit_debug(payload, None, sid=sid)
