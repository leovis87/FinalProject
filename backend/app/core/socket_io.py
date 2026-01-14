# app/core/socket_io.py
import asyncio
import os
import sys
import socketio
import traceback
from datetime import datetime
from typing import Dict, List, Optional

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
from models.debate_participant import DebateParticipant
from models.enums import DebateStatus, DebateRole

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
sio_app = socketio.ASGIApp(sio)

_room_states: Dict[str, dict] = {}
_room_locks: Dict[str, asyncio.Lock] = {}
_active_users: Dict[str, set] = {}
_sid_to_room: Dict[str, str] = {}
_sid_to_user: Dict[str, str] = {}


def _get_lock(room_id: str) -> asyncio.Lock:
    if room_id not in _room_locks:
        _room_locks[room_id] = asyncio.Lock()
    return _room_locks[room_id]


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


def _role_value(role) -> str:
    if isinstance(role, DebateRole):
        return role.value
    return str(role)


def _to_json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
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


def _build_room_state(room: DebateRoom, participants: List[DebateParticipant]) -> dict:
    ordered = _sorted_participants(participants)
    pro_users = [u for u in ordered if u["side"] == "pro"]
    con_users = [u for u in ordered if u["side"] == "con"]
    join_order = [u["user_id"] for u in ordered]
    join_index = {user_id: idx for idx, user_id in enumerate(join_order)}

    return {
        "room_id": str(room.debate_room_id),
        "topic": room.topic,
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
    }


def _graph_base_state(room_state: dict) -> dict:
    return {
        "room_id": int(room_state["room_id"]),
        "topic": room_state["topic"],
        "topic_analysis": room_state.get("topic_analysis"),
        "pro_users": [
            {
                "user_id": u["user_id"],
                "user_name": u["user_name"],
                "is_premium": False,
            }
            for u in room_state["pro_users"]
        ],
        "con_users": [
            {
                "user_id": u["user_id"],
                "user_name": u["user_name"],
                "is_premium": False,
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


def _format_topic_analysis(topic_analysis) -> str:
    if not topic_analysis:
        return "Topic summary is not available."
    if hasattr(topic_analysis, "model_dump"):
        data = topic_analysis.model_dump()
    elif hasattr(topic_analysis, "dict"):
        data = topic_analysis.dict()
    elif isinstance(topic_analysis, dict):
        data = topic_analysis
    else:
        return str(topic_analysis)

    description = data.get("description", "")
    pro_args = data.get("pro_args", [])
    con_args = data.get("con_args", [])
    return (
        f"Topic summary: {description}\n"
        f"Pro points: {', '.join(pro_args)}\n"
        f"Con points: {', '.join(con_args)}"
    )


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


def _choose_representative(users: List[dict], room_state: dict) -> Optional[dict]:
    spoken = room_state["per_round_spoken_set"].get(room_state["current_round"], set())
    candidates = [u for u in users if u["user_id"] not in spoken]
    if not candidates:
        return None
    join_index = room_state["join_index"]
    last_spoken = room_state["last_spoken"]
    candidates.sort(key=lambda u: (last_spoken.get(u["user_id"], 0), join_index[u["user_id"]]))
    return candidates[0]


def _set_round(room_state: dict, round_number: int) -> List[str]:
    room_state["current_round"] = round_number
    room_state["turn_index"] = 0
    room_state["per_round_spoken_set"][round_number] = set()
    room_state["round_messages"][round_number] = []
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


async def _emit_system_message(room_state: dict, content: str) -> None:
    message = _make_system_message(room_state, content)
    room_state["messages"].append(message)
    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_state['room_id']}",
    )


def _run_topic_summary(room_state: dict) -> Optional[dict]:
    state = _graph_base_state(room_state)
    config = _graph_config(f"debate_{room_state['room_id']}_topic")
    result = debate_app.invoke(Command(update=state, goto="analyze_topic"), config)
    return result.get("topic_analysis") if isinstance(result, dict) else None


def _run_round_summary(room_state: dict, round_number: int) -> str:
    state = _graph_base_state(room_state)
    state["current_turn"] = round_number
    state["messages"] = list(room_state["round_messages"].get(round_number, []))
    config = _graph_config(f"debate_{room_state['room_id']}_summary_{round_number}")
    result = debate_app.invoke(Command(update=state, goto="summary"), config)
    summary_history = []
    if isinstance(result, dict):
        summary_history = result.get("summary_history", [])
    if summary_history:
        return summary_history[-1]
    return f"[Round {round_number}] Summary unavailable."


# 1. 기존의 _format_moderator_report는 삭제하고 이 함수를 추가하세요.
def _get_final_report_data(room_state: dict) -> Optional[dict]:
    """사회자 최종 리포트 객체를 생성하고 JSON safe한 dict로 반환합니다."""
    state = _graph_base_state(room_state)
    state["messages"] = list(room_state.get("dialogue_messages", []))
    config = _graph_config(f"debate_{room_state['room_id']}_final")
    
    # LangGraph 실행 (moderator_shared 노드로 이동)
    result = debate_app.invoke(Command(update=state, goto="moderator_shared"), config)
    report = result.get("moderator_report") if isinstance(result, dict) else None
    
    # Pydantic 모델이나 객체를 JSON으로 보낼 수 있게 dict로 변환
    return _to_json_safe(report)

# 2. 시스템 메시지에 display_type을 넣을 수 있도록 수정하세요.
async def _emit_system_message(room_state: dict, content: str, display_type: str = "moderator") -> None:
    message = {
        "turn": room_state.get("current_round", 0),
        "role": "ai",
        "user_name": "Moderator",
        "content": content,
        "display_type": display_type  # 프론트에서 '찢어서' 보게 해주는 핵심 키
    }
    room_state["messages"].append(message)
    await sio.emit(
        "debate_update",
        _message_payload(message, room_state, replace=False),
        room=f"debate_{room_state['room_id']}",
    )


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

    if room_id in _room_states:
        room_state = _room_states[room_id]
        if room_state.get("messages"):
            await sio.emit(
                "debate_update",
                {
                    "messages": list(room_state["messages"]),
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
                await _emit_system_message(room_state, "Debate started. Round 1 begins.")

                # Topic summary at debate start (LLM).
                try:
                    graph_payload = _debug_payload("info", "GRAPH", room_id_str, str(user_id), "topic_summary start")
                    _debug_print(graph_payload, state=str(room.status))
                    await _emit_debug(graph_payload, room_id_str, sid=sid)
                    topic_analysis = _run_topic_summary(room_state)
                    room_state["topic_analysis"] = topic_analysis
                    topic_text = _format_topic_analysis(topic_analysis)
                    await _emit_system_message(room_state, topic_text)
                    graph_payload = _debug_payload("info", "GRAPH", room_id_str, str(user_id), "topic_summary done")
                    _debug_print(graph_payload, state=str(room.status))
                    await _emit_debug(graph_payload, room_id_str, sid=sid)
                except Exception:
                    traceback.print_exc()
                    await _emit_error("Topic summary failed.", room_id_str, sid=sid)

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


@sio.on("send_message")
async def handle_message(sid, data):
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    content = data.get("content")

    if not room_id or not user_id or not content:
        return

    room_id_str = str(room_id)
    lock = _get_lock(room_id_str)

    async with lock:
        room_state = _room_states.get(room_id_str)
        if not room_state:
            await sio.emit("debate_error", {"message": "Room state not ready."}, to=sid)
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

        # 메시지 데이터 생성
        role = participant["side"]
        message = {
            "turn": room_state["current_round"],
            "role": role,
            "user_id": str(user_id),
            "user_name": data.get("user_name") or participant["user_name"],
            "content": content,
        }

        # 상태 기록
        room_state["messages"].append(message)
        room_state["dialogue_messages"].append(message)
        room_state["round_messages"].setdefault(room_state["current_round"], []).append(message)
        
        # 차례 인덱스 증가 (먼저 증가시켜야 next_speaker가 올바르게 전송됨)
        room_state["turn_index"] += 1
        room_state["global_spoken_seq"] += 1
        room_state["last_spoken"][str(user_id)] = room_state["global_spoken_seq"]
        room_state["per_round_spoken_set"][room_state["current_round"]].add(str(user_id))

        # 발언 업데이트 전송
        await sio.emit(
            "debate_update",
            _message_payload(message, room_state, replace=False),
            room=f"debate_{room_id_str}",
        )

        # 라운드 종료 여부 확인 (발언할 사람이 남았으면 함수 종료)
        if room_state["turn_index"] < len(room_state["turn_order"]):
            return

        # --- 라운드가 종료된 시점 (Round Completed) ---
        round_number = room_state["current_round"]
        
        # 1. 라운드 요약 생성
        try:
            summary_text = _run_round_summary(room_state, round_number)
            await _emit_system_message(room_state, summary_text)
        except Exception:
            traceback.print_exc()

        # 2. 최종 판결 (4라운드 종료 시)
        if round_number >= 4:
            try:
                # 위에서 정의한 헬퍼 함수 호출
                report_data = _get_final_report_data(room_state)
                
                if report_data:
                    # 데이터를 각각의 display_type으로 찢어서 4번 전송
                    await _emit_system_message(room_state, report_data.get("general_summary", ""), "report_summary")
                    await _emit_system_message(room_state, report_data.get("pro_eval", {}), "report_pro")
                    await _emit_system_message(room_state, report_data.get("con_eval", {}), "report_con")
                    if report_data.get("best_player"):
                        await _emit_system_message(room_state, report_data["best_player"], "report_mvp")

            except Exception:
                traceback.print_exc()
                await _emit_error("Final report failed.", room_id_str, sid=sid)
            
            # 방 상태를 종료로 변경
            async with AsyncSessionLocal() as db:
                room = await db.get(DebateRoom, int(room_id_str))
                if room:
                    room.status = DebateStatus.FINISHED
                    await db.commit()
            return

        # 3. 다음 라운드 이동 로직 (1~3 라운드 종료 시)
        # ⭐ [해결] 여기서 next_round 변수를 명확히 정의함
        next_round = round_number + 1
        
        # 새로운 라운드 세팅 (_set_round 함수 활용)
        skipped = _set_round(room_state, next_round)
        if skipped:
            for side in skipped:
                await _emit_system_message(room_state, f"Moderator: {side} has no available speaker. Skipping.")

        # DB 라운드 상태 업데이트
        async with AsyncSessionLocal() as db:
            room = await db.get(DebateRoom, int(room_id_str))
            if room:
                room.status = _round_status(next_round)
                await db.commit()

        # 클라이언트에 다음 라운드 정보 전송
        await sio.emit(
            "debate_update",
            {
                "messages": [],
                "replace_messages": False,
                **_round_payload(room_state),
            },
            room=f"debate_{room_id_str}",
        )


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
    payload = _debug_payload("info", "DISCONNECT", None, None, f"sid={sid}")
    _debug_print(payload)
    await _emit_debug(payload, None, sid=sid)