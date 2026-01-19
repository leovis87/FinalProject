from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from routers.user import get_current_user
from models.enums import DebateRole
from models.user import User
from schemas.debate import (
    DebateRoomCreate,
    DebateRoomResponse,
    RandomMatchRequest,
    RandomMatchResponse,
    DebateHistoryItem,
    DebateMessageResponse,
    DebateResultUpsertRequest,
    DebateResultUpsertResponse
)
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

@router.post("/random-match", response_model=RandomMatchResponse)
async def random_match(
    payload: RandomMatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    랜덤 토론 매칭 (대기 중 방 우선, 없으면 새 방 생성)
    """
    return await debate_service.random_match(
        db=db,
        user_id=current_user.user_id,
        level=payload.level,
        category=payload.category,
        max_users=payload.max_users,
        max_turns=payload.max_turns
    )

@router.get("/history", response_model=List[DebateHistoryItem])
async def get_debate_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await debate_service.get_debate_history(db, current_user.user_id)

@router.get("/{debate_id}/messages", response_model=List[DebateMessageResponse])
async def get_debate_messages(
    debate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await debate_service.get_debate_messages(db, debate_id, current_user.user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{debate_id}", response_model=DebateRoomResponse)
async def get_debate_room(
    debate_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Tip: 참가자 정보까지 한번에 로딩하려면 select options(joinedload)를 써야 할 수도 있습니다.
    # 간단하게는 service에서 구현
    return await debate_service.get_debate_room_details(db, debate_id)

@router.post("/{debate_id}/result", response_model=DebateResultUpsertResponse)
async def set_debate_results(
    debate_id: int,
    payload: DebateResultUpsertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await debate_service.set_debate_results(db, debate_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{debate_id}/join")
async def join_debate(
    debate_id: int,
    role: DebateRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        await debate_service.join_debate_room(db, debate_id, current_user.user_id, role.value)
        return {"message": "참가 성공"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
