from fastapi import (FastAPI, WebSocket, WebSocketDisconnect,
                     Depends, HTTPException)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import (List, Dict, Tuple,
                    Union, Optional, Generator)
from datetime import datetime, timezone, timedelta
from src.models import User
from utils.websocket import ConnectionManager
from utils.database import (SessionLocal, engine, get_db)
from utils.set_llm import (summary_and_judgment)
from utils.set_time import time_zone
from utils.crud import (create_room, join_room, save_message,
                        get_room_messages, get_rooms, get_room_info,
                        get_participants, get_user_side, create_user,
                        get_user_by_id)
from utils.schemas import (SenderType, ChatRequest,
                            SystemPromptRequest, JoinRoomRequest,
                            RoomResponse, CreateRoomRequest,
                            UserRegister, UserLogin, UserResponse,
                            Token, TokenData)
from utils.auth import (create_access_token, authenticate_user,
                        get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES)
import logging
import json
import time

# FastAPI 앱 생성
app = FastAPI()


# KST 시간대 설정
KST = time_zone(location = "Asia/Seoul")

# return: String
# .strftime(%Y-%m-%d %H:%M) -> (연-월-일 시:분)
# .isoformat()              -> (yyyy-mm-ddT)
DISPLAY_TIME = KST.strftime("%H:%M:%S")
DB_LOG_TIME = KST.isoformat()


# logging 설정
logging.basicConfig(
    format = '%(asctime)s %(levelname)s:%(message)s',
    level = logging.DEBUG,
    datefmt = '%m/%d/%Y %I:%M:%S %p',
    filename = 'WebSocket_test.log'
)


# CORS 설정 (React에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],  # React 개발 서버 주소
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)
# ConnectionManager 인스턴스 생성 (전역 변수)
manager = ConnectionManager()


# ===== LLM model selector =====
Use_Claude = True


# ===== endpoint 설정 =====
@app.get("/")
async def root():
    """
    서버 상태 확인용 엔드포인트
    브라우저에서 http://localhost:8099 접속하면 보임
    """
    return {
        "message": "WebSocket 토론방 서버 실행 중!",
        "active_connections": len(manager.active_connections)
    }


# ===== Create =====
# 토론방 생성
# ==================
@app.post("/api/rooms", response_model = RoomResponse)
async def creat_debate_room(
    request: CreateRoomRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    새로운 토론방 생성 (로그인 필수)
        - 1. create_room() 호출
        - 2. 생성된 방 정보 반환
        - 3. 에러 처리 (예: DB 오류)
    """
    # 1. 만들어 놓은 함수 호출
    new_room = create_room(
        db = db,
        created_by = current_user.user_id,
        title = request.title,
        topic = request.topic,
        room_type = request.room_type,
        max_participants = request.max_participants
    )

    # 2. 반환
    return new_room


# ===== Create =====
# 토론방 입장
# ==================
@app.post("/api/rooms/{room_id}/join")
async def join_debate_room(
    room_id: int,
    request: JoinRoomRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    토론방 입장 (찬성 / 반대 선택) + 로그인 필수
        - 1. join_room() 호출
        - 2. 성공 시: {"message": "입장 완료", "participants": ...}
        - 3. 실패 시: HTTPException 발생
            -> 방이 꽉 참
            -> 이미 참가 상태
            -> 방이 없음
    """
    try:
        participant = join_room(
            db = db,
            room_id = room_id,
            user_id = current_user.user_id,
            nickname = current_user.nickname,
            side = request.side
        )
        return {
            "message": "✅ 입장 완료",
            "participant": participant
        }

    except Exception as e:
        raise HTTPException(status_code = 400,
                            detail = str(e))


# ===== Create =====
# 회원 가입
# ==================
@app.post("/api/auth/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    회원가입
    
    Request:
        - user_id: 로그인 ID
        - email: 이메일
        - nickname: 닉네임
        - password: 비밀번호
    
    Response:
        - 생성된 사용자 정보 (비밀번호 제외)
    """
    try:
        new_user = create_user(
            db=db,
            user_id=user_data.user_id,
            email=user_data.email,
            nickname=user_data.nickname,
            password=user_data.password
        )
        return new_user
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ===== Create =====
# 로그인
# ==================
@app.post("/api/auth/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    로그인
    
    Request:
        - user_id: 로그인 ID
        - password: 비밀번호
    
    Response:
        - access_token: JWT 토큰
        - token_type: "bearer"
    """
    # 1. 사용자 인증
    user = authenticate_user(db, user_data.user_id, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. JWT 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ===== Get =====
# 로그인한 사용자
# 정보 조회
# ===============
@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    현재 로그인한 사용자 정보 조회
    
    Headers:
        Authorization: Bearer {token}
    
    Response:
        - 사용자 정보
    """
    return current_user


# ===== Get =====
# 방 목록 조회
# ===============
@app.get("/api/rooms", response_model = List[RoomResponse])
async def get_rooms_list(
    db: Session = Depends(get_db)
):
    """
    모든 토론방 목록 가져오기
        - 1. get_rooms() 호출
        - 2. 방 리스트 반환
    """
    rooms = get_rooms(db = db)
    return rooms


# ===== Get =====
# 방 상세 조회
# ===============
@app.get("/api/rooms/{room_id}", response_model = RoomResponse)
async def get_room_detail(
    room_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 토론방의 상세 정보 가져오기
        - 1. get_room_info(room_id) 호출
        - 2. 방이 없으면 오류 처리 HTTPException (404)
        - 3. 방 정보 반환
    """
    room = get_room_info(db = db,
                         room_id = room_id)
    
    if not room:
        raise HTTPException(status_code = 404,
                            detail = "⚠️ 방을 찾을 수 없습니다.")
    
    return room


# ===== Get =====
# 참가자 목록 조회
# ===============
@app.get("/api/rooms/{room_id}/participants")
async def get_room_participants(
    room_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 토론방에 참여한 참가자 목록 가져오기
        - 1. get_participants(room_id) 호출
        - 2. 참가자 리스트 반환
    """
    participants = get_participants(
        db = db,
        room_id = room_id
    )

    return participants


@app.websocket("/ws/room/{room_id}/{user_id}")
async def debate_room_websocket(websocket: WebSocket,
                                room_id: str,
                                user_id: str,
                                db: Session = Depends(get_db)):
    """
    토론방 WebSocket 엔드포인트
    
    파라미터:
        - websocket: WebSocket 객체 (연결 자체)
        - room_id: 토론방
        - user_id: 클라이언트 식별자 (예: "user123")
    
    URL 예시: ws://localhost:8099/ws/room/room123/user444
    """

    # ⭐ 연결 전, 먼저 사용자의 참가 side 확인 (예: 찬성 / 반대)
    user_side = get_user_side(db, room_id, user_id)
    
    # 1. 연결 수락
    await manager.connect(websocket, room_id)
    
    # 2. 토론방 입장 알림을 모든 사람에게 전송
    await manager.broadcast(room_id, {
        "type": "system",
        "message": f"{user_id}님이 입장했습니다.",
        "timestamp": DISPLAY_TIME
    })

    # 3. AI 사회자 환영 멘트 (서버에서 자동 생성) 전송
    await manager.broadcast(room_id, {
        "type": "ai_moderator",
        "user_id": "AI_사회자",
        "message": f"{user_id}님 환영합니다!",
        "timestamp": DISPLAY_TIME
    })
    
    try:
        # 4. while True로 계속 사용자 메시지 대기
        # 비유: 상담원이 계속 고객의 말을 듣고 있는 상태
        while True:
            # 메시지 받기 (여기서 대기 중)
            user_message = await websocket.receive_text()
            print(f"    📩 {user_id}로부터 받은 메시지: {user_message}")

            # 5. DB 저장
            save_message(
                db = db,
                room_id = room_id,
                sender_type = "user",
                sender_id = user_id,
                side = user_side,
                content = user_message
            )

            # ========================================
            # 🔴 여기서 종료 조건을 추가할 수 있음!
            # ========================================
            if user_message == "종료":
                print(f"🛑 {user_id}가 종료 요청")
                break  # while 루프 탈출 → 연결 종료
            
            # 6. 모든 참가자(사용자)에게 브로드캐스트 출력
            await manager.broadcast(room_id,{
                "type": "user_message",
                "user_id": user_id,
                "message": user_message,
                "timestamp": DISPLAY_TIME
            })
            
            # 6-1. 보낸 사람에게 확인 메시지
            await manager.send_personal_message(room_id, {
                "type": "user_message",
                "user_id": user_id,
                "message": user_message,
                "timestamp": DISPLAY_TIME
            })

            # ========================================
            # 7. LLM API default = Claude['haiku']
            # AI 사회자 응답 조건 체크
            # ========================================
            # 조건 1: 상대 팀으로 턴 넘길 때
            # if await is_turn_complete(room_id):
            #     ai_response = await get_ai_turn_change_message(room_id)

            #     await manager.broadcast(room_id,{
            #         "type": "ai_moderator",
            #         "user_id": "AI_사회자",
            #         "message": ai_response
            #     })

            # # 조건 2: 토론이 끝났을 때
            # if await is_debate_finished(room_id):
            #     # LLM API가 모든 message를 읽고 요약
            #     pull_all_messages = await db.get_room_messages()


    except WebSocketDisconnect:
        # 연결이 끊어졌을 때 (클라이언트가 창을 닫거나 네트워크 끊김)
        print(f"🔌 {user_id} 연결 끊김")
        manager.disconnect(websocket)
        
        # 퇴장 알림
        await manager.broadcast(json.dumps({
            "type": "system",
            "message": f"{user_id}님이 퇴장했습니다.",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
    
    except Exception as e:
        # 기타 예외 처리
        print(f"⚠️ 오류 발생: {e}")
        manager.disconnect(websocket)


# 서버 실행 시 출력
if __name__ == "__main__":
    import uvicorn
    print("🚀 토론 플랫폼 서버 시작!")
    print("📍 http://localhost:8099")
    print("📍 WebSocket: ws://localhost:8099/ws/{user_id}")
    uvicorn.run(app, host = "0.0.0.0", port = 8099)