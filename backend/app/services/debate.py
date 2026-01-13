from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime

from models.debate_room import DebateRoom
from models.debate_participant import DebateParticipant
from models.user import User
from models.enums import DebateStatus, BadgeType
from schemas.debate import DebateRoomCreate

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

        # 인원수가 꽉 찼는지 확인하여 방 상태 변경
        # 관전자를 제외한 실제 토론자 수 계산
        query_total = select(func.count()).where(
            DebateParticipant.debate_room_id == debate_id,
            DebateParticipant.role.in_(["pro", "con"])
        )
        total_debaters = (await db.execute(query_total)).scalar()

        if total_debaters >= room.max_users:
            room.status = DebateStatus.PROCEEDING
            room.started_at = datetime.now()
        
        await db.commit()
        await db.refresh(new_participant)

        return new_participant
    
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