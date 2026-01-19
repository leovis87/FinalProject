from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from pathlib import Path
from random import choice
import json

from models.debate_room import DebateRoom
from models.debate_participant import DebateParticipant
from models.debate_message import DebateMessage
from models.user import User
from models.enums import DebateStatus, BadgeType, DebateRole, DebateLevel, DebateCategory
from schemas.debate import DebateRoomCreate, DebateResultUpsertRequest
from rag.indexer import load_topics_csv

class DebateService:
    async def create_debate_room(self, db: AsyncSession, debate_create: DebateRoomCreate, creator_id: int) -> DebateRoom:
        """토론방 생성 및 개설자 참가 처리"""
        debate_data = debate_create.model_dump()
        creator_role = debate_data.pop('creator_role')
        
        new_debate = DebateRoom(
            creator_id=creator_id,
            **debate_data
        )

        db.add(new_debate)
        await db.flush()

        new_participant = DebateParticipant(
            debate_room_id=new_debate.debate_room_id,
            user_id=creator_id,
            role=creator_role,
            turn_order=1
        )
        db.add(new_participant)

        await db.commit()
        
        return await self.get_debate_room_details(db, new_debate.debate_room_id)
    
    async def get_all_debate_rooms(self, db: AsyncSession):
        """모든 토론방 조회 (최신순)"""
        query = select(DebateRoom).options(
            selectinload(DebateRoom.participants).joinedload(DebateParticipant.user)
        ).where(
            DebateRoom.status != DebateStatus.FINISHED
        ).order_by(desc(DebateRoom.created_at))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_debate_room_details(self, db: AsyncSession, debate_id: int) -> DebateRoom:
        """토론방 상세 조회 (참가자 정보 포함)"""
        query = select(DebateRoom).options(
            selectinload(DebateRoom.participants).joinedload(DebateParticipant.user)
        ).where(DebateRoom.debate_room_id == debate_id)
        
        result = await db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            return None 
            
        return room
    
    async def join_debate_room(self, db: AsyncSession, debate_id: int, user_id: int, role: str) -> DebateParticipant | None:
        """토론방 참가"""
        # 방 정보 확인
        room = await db.get(DebateRoom, debate_id)
        if not room:
            raise ValueError("존재하지 않는 토론방입니다.")

        # 이미 참가한 유저인지 확인
        query = select(DebateParticipant).where(
            DebateParticipant.debate_room_id == debate_id,
            DebateParticipant.user_id == user_id
        )
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise ValueError("이미 참가 중인 방입니다.")

        # 해당 역할의 현재 인원 수 확인
        if role != "observer":
            query_count = select(func.count()).where(
                DebateParticipant.debate_room_id == debate_id,
                DebateParticipant.role == role
            )
            result_count = await db.execute(query_count)
            current_role_count = result_count.scalar()

            # 팀당 최대 인원 (예: 2:2 토론이면 max_users가 4)
            max_team_size = room.max_users // 2

            if current_role_count >= max_team_size:
                raise ValueError(f"{role} 진영이 꽉 찼습니다.")
            
            # 순번 배정
            assign_order = current_role_count + 1
        else:
            assign_order = None

        # 참가자 등록
        new_participant = DebateParticipant(
            debate_room_id=debate_id,
            user_id=user_id,
            role=role,
            turn_order=assign_order
        )

        db.add(new_participant)
        await db.flush()

        # -------------------------------------------------------
        # 수정사항: 인원이 차도 자동으로 상태를 바꾸지 않음.
        # 방장이 소켓(socket_io.py)을 통해 직접 시작할 때까지 WAITING 유지.
        # -------------------------------------------------------
        
        await db.commit()
        await db.refresh(new_participant)

        return new_participant

    async def get_debate_history(self, db: AsyncSession, user_id: int) -> list[dict]:
        """Return finished debates for a user."""
        query = select(DebateParticipant, DebateRoom).join(
            DebateRoom,
            DebateParticipant.debate_room_id == DebateRoom.debate_room_id
        ).where(
            DebateParticipant.user_id == user_id,
            DebateRoom.status == DebateStatus.FINISHED
        ).order_by(
            desc(DebateRoom.finished_at),
            desc(DebateRoom.started_at),
            desc(DebateRoom.created_at)
        )

        result = await db.execute(query)
        rows = result.all()

        items = []
        for participant, room in rows:
            items.append({
                "debate_room_id": room.debate_room_id,
                "title": room.title,
                "topic": room.topic,
                "category": room.category,
                "level": room.level,
                "status": room.status,
                "role": participant.role,
                "result": participant.result,
                "result_reason": participant.result_reason,
                "joined_at": participant.joined_at,
                "started_at": room.started_at,
                "finished_at": room.finished_at
            })

        return items

    async def get_debate_messages(self, db: AsyncSession, debate_id: int, user_id: int) -> list[dict]:
        room = await db.get(DebateRoom, debate_id)
        if not room:
            raise ValueError("Debate room not found.")

        participant_query = select(DebateParticipant).where(
            DebateParticipant.debate_room_id == debate_id,
            DebateParticipant.user_id == user_id
        )
        participant_result = await db.execute(participant_query)
        if participant_result.scalar_one_or_none() is None:
            raise PermissionError("You are not a participant.")

        query = select(DebateMessage).options(
            selectinload(DebateMessage.user)
        ).where(
            DebateMessage.debate_room_id == debate_id
        ).order_by(DebateMessage.created_at.asc(), DebateMessage.message_id.asc())

        result = await db.execute(query)
        messages = result.scalars().all()

        items = []
        for msg in messages:
            items.append({
                "message_id": msg.message_id,
                "debate_room_id": msg.debate_room_id,
                "user_id": msg.user_id,
                "user_name": msg.user.nickname if msg.user else None,
                "role": msg.role,
                "display_type": msg.display_type,
                "content": msg.content,
                "turn": msg.turn,
                "created_at": msg.created_at,
            })

        return items

    async def get_debate_verdict(self, db: AsyncSession, debate_id: int, user_id: int) -> dict:
        room = await db.get(DebateRoom, debate_id)
        if not room:
            raise ValueError("Debate room not found.")

        participant_query = select(DebateParticipant).where(
            DebateParticipant.debate_room_id == debate_id,
            DebateParticipant.user_id == user_id
        )
        participant_result = await db.execute(participant_query)
        if participant_result.scalar_one_or_none() is None:
            raise PermissionError("You are not a participant.")

        query = select(DebateMessage).where(
            DebateMessage.debate_room_id == debate_id,
            DebateMessage.display_type.in_(["report_summary", "report_pro", "report_con", "report_mvp"])
        ).order_by(DebateMessage.created_at.asc(), DebateMessage.message_id.asc())

        result = await db.execute(query)
        messages = result.scalars().all()

        summary = None
        pro_eval = None
        con_eval = None
        best_player = None

        for msg in messages:
            if msg.display_type == "report_summary":
                summary = msg.content
            elif msg.display_type == "report_pro":
                try:
                    pro_eval = json.loads(msg.content)
                except Exception:
                    pro_eval = None
            elif msg.display_type == "report_con":
                try:
                    con_eval = json.loads(msg.content)
                except Exception:
                    con_eval = None
            elif msg.display_type == "report_mvp":
                best_player = msg.content

        return {
            "debate_room_id": debate_id,
            "summary": summary,
            "pro_eval": pro_eval,
            "con_eval": con_eval,
            "best_player": best_player,
            "decided_at": room.finished_at,
        }

    async def set_debate_results(
        self,
        db: AsyncSession,
        debate_id: int,
        payload: DebateResultUpsertRequest
    ) -> dict:
        """Set final results for a debate room."""
        query = select(DebateRoom).options(
            selectinload(DebateRoom.participants)
        ).where(DebateRoom.debate_room_id == debate_id)
        result = await db.execute(query)
        room = result.scalar_one_or_none()

        if not room:
            raise ValueError("Debate room not found.")

        participants = {p.user_id: p for p in room.participants}
        requested_ids = {item.user_id for item in payload.results}
        valid_ids = set(participants.keys())
        missing_ids = {p.user_id for p in room.participants if p.role != DebateRole.OBSERVER} - requested_ids
        extra_ids = requested_ids - valid_ids

        if missing_ids:
            raise ValueError("Missing results for participants.")
        if extra_ids:
            raise ValueError("Invalid participant in results.")

        decided_at = datetime.now()

        for item in payload.results:
            participant = participants.get(item.user_id)
            if not participant:
                continue
            participant.result = item.result
            participant.result_reason = payload.result_reason
            participant.result_decided_at = decided_at
            participant.result_decided_by = payload.decided_by
            db.add(participant)

        room.status = DebateStatus.FINISHED
        if room.finished_at is None:
            room.finished_at = decided_at
        db.add(room)

        await db.commit()

        return {
            "debate_room_id": room.debate_room_id,
            "decided_at": decided_at,
            "decided_by": payload.decided_by
        }

    async def random_match(
        self,
        db: AsyncSession,
        user_id: int,
        level: DebateLevel,
        category: DebateCategory | None,
        max_users: int,
        max_turns: int
    ) -> dict:
        """랜덤 토론방 매칭 또는 생성"""
        room = await self._match_existing_room(db, user_id, level, category)
        if room:
            return room

        return await self._create_random_room(db, user_id, level, category, max_users, max_turns)

    async def _match_existing_room(
        self,
        db: AsyncSession,
        user_id: int,
        level: DebateLevel,
        category: DebateCategory | None
    ) -> dict | None:
        query = select(DebateRoom).options(
            selectinload(DebateRoom.participants)
        ).where(
            DebateRoom.status == DebateStatus.WAITING,
            DebateRoom.is_private.is_(False)
        ).order_by(desc(DebateRoom.created_at))

        if level != DebateLevel.ALL:
            query = query.where(DebateRoom.level == level)
        if category is not None:
            query = query.where(DebateRoom.category == category)

        result = await db.execute(query)
        rooms = result.scalars().all()

        for room in rooms:
            if any(p.user_id == user_id for p in room.participants):
                continue

            role = self._choose_role_for_room(room)
            if not role:
                continue

            try:
                await self.join_debate_room(db, room.debate_room_id, user_id, role.value)
            except ValueError:
                continue

            matched_room = await self.get_debate_room_details(db, room.debate_room_id)
            return {
                "room_id": matched_room.debate_room_id,
                "room": matched_room,
                "joined_role": role,
                "matched_existing": True,
                "queued": False
            }

        return None

    async def _create_random_room(
        self,
        db: AsyncSession,
        user_id: int,
        level: DebateLevel,
        category: DebateCategory | None,
        max_users: int,
        max_turns: int
    ) -> dict:
        role = choice([DebateRole.PRO, DebateRole.CON])
        topic_meta = self._pick_local_topic(level, category)

        topic_text = topic_meta.get("topic_text", "랜덤 토론 주제")
        topic_context = topic_meta.get("one_line_context", "랜덤 매칭으로 생성된 토론입니다.")
        title = topic_text[:100]

        resolved_category = category or self._map_subject_to_category(topic_meta.get("subject"))
        resolved_level = level if level != DebateLevel.ALL else self._map_dataset_level(topic_meta.get("level"))

        debate_create = DebateRoomCreate(
            title=title,
            category=resolved_category,
            topic=topic_text,
            topic_description=topic_context,
            level=resolved_level,
            is_private=False,
            room_password=None,
            allow_observers=True,
            max_users=max_users,
            max_turns=max_turns,
            creator_role=role
        )

        created_room = await self.create_debate_room(db, debate_create, user_id)

        return {
            "room_id": created_room.debate_room_id,
            "room": created_room,
            "joined_role": role,
            "matched_existing": False,
            "queued": True
        }

    def _choose_role_for_room(self, room: DebateRoom) -> DebateRole | None:
        max_team_size = room.max_users // 2
        pro_count = sum(1 for p in room.participants if p.role == DebateRole.PRO)
        con_count = sum(1 for p in room.participants if p.role == DebateRole.CON)

        available_roles = []
        if pro_count < max_team_size:
            available_roles.append(DebateRole.PRO)
        if con_count < max_team_size:
            available_roles.append(DebateRole.CON)

        if not available_roles:
            return None
        if len(available_roles) == 1:
            return available_roles[0]
        if pro_count == con_count:
            return choice(available_roles)
        return DebateRole.PRO if pro_count < con_count else DebateRole.CON

    def _pick_local_topic(self, level: DebateLevel, category: DebateCategory | None) -> dict:
        docs = self._load_local_topics()
        if not docs:
            return {}

        level_ko = self._map_level_to_dataset(level)
        category_ko = self._map_category_to_dataset(category)

        filtered = []
        for doc in docs:
            meta = doc.get("metadata", {})
            if level_ko and meta.get("level") != level_ko:
                continue
            if category_ko and meta.get("subject") != category_ko:
                continue
            filtered.append(meta)

        candidates = filtered or [doc.get("metadata", {}) for doc in docs]
        return choice(candidates) if candidates else {}

    def _load_local_topics(self) -> list:
        csv_path = Path(__file__).resolve().parents[1] / "rag" / "data" / "topics.csv"
        if not csv_path.exists():
            return []
        return load_topics_csv(str(csv_path))

    def _map_level_to_dataset(self, level: DebateLevel) -> str | None:
        mapping = {
            DebateLevel.ELEMENTARY_LOW: "초등_저학년",
            DebateLevel.ELEMENTARY_HIGH: "초등_고학년",
            DebateLevel.MIDDLE: "중학생",
            DebateLevel.HIGH: "고등학생",
        }
        if level == DebateLevel.ALL:
            return None
        return mapping.get(level)

    def _map_category_to_dataset(self, category: DebateCategory | None) -> str | None:
        mapping = {
            DebateCategory.KOREAN: "국어",
            DebateCategory.SOCIAL: "사회",
            DebateCategory.MORAL: "도덕",
            DebateCategory.ETHICS: "도덕",
        }
        if category is None:
            return None
        return mapping.get(category)

    def _map_subject_to_category(self, subject: str | None) -> DebateCategory:
        mapping = {
            "국어": DebateCategory.KOREAN,
            "사회": DebateCategory.SOCIAL,
            "도덕": DebateCategory.MORAL,
            "윤리": DebateCategory.ETHICS,
        }
        return mapping.get(subject, DebateCategory.KOREAN)

    def _map_dataset_level(self, level: str | None) -> DebateLevel:
        mapping = {
            "초등_저학년": DebateLevel.ELEMENTARY_LOW,
            "초등_고학년": DebateLevel.ELEMENTARY_HIGH,
            "중학생": DebateLevel.MIDDLE,
            "고등학생": DebateLevel.HIGH,
        }
        return mapping.get(level, DebateLevel.ALL)
    
    async def _add_badge(self, db: AsyncSession, user: User, badge_type: BadgeType):
        """유저에게 뱃지 추가 (중복 체크)"""
        badge_name = badge_type.value
        current_badges = list(user.badges) if user.badges else []
        
        if any(b.get('name') == badge_name for b in current_badges):
            return

        new_badge = {
            "name": badge_name,
            "acquired_at": datetime.now().isoformat()
        }
        current_badges.append(new_badge)
        user.badges = current_badges
        db.add(user)

debate_service = DebateService()
