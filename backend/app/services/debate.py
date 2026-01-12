from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.debate_room import DebateRoom
from models.enums import DebateStatus
from schemas.debate import DebateRoomCreate

class DebateService:
    async def create_debate_room(self, db: AsyncSession, debate_create: DebateRoomCreate, creator_id: int) -> DebateRoom:
        """토론방 생성"""
        debate_data = debate_create.model_dump()
        
        new_debate = DebateRoom(
            creator_id=creator_id,
            **debate_data
        )

        db.add(new_debate)
        await db.commit()
        await db.refresh(new_debate)
        
        return new_debate
    
    async def get_all_debate_rooms(self, db: AsyncSession):
        """모든 토론방 조회 (최신순)"""
        query = select(DebateRoom).where(
            DebateRoom.status != DebateStatus.FINISHED
        ).order_by(desc(DebateRoom.created_at))
        result = await db.execute(query)
        return result.scalars().all()

debate_service = DebateService()