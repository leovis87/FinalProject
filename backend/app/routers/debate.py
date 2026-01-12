from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from routers.user import get_current_user
from models.user import User
from schemas.debate import DebateRoomCreate, DebateRoomResponse
from services.debate import debate_service

router = APIRouter(prefix="/api/debates", tags=["토론방"])

@router.post("/", response_model=DebateRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_debate_room(
    debate_create: DebateRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    토론방 생성
    """
    return await debate_service.create_debate_room(db, debate_create, current_user.user_id)

@router.get("/", response_model=List[DebateRoomResponse])
async def read_debate_rooms(db: AsyncSession = Depends(get_db)):
    """토론방 목록 조회"""
    return await debate_service.get_all_debate_rooms(db)