import socketio
import json
import traceback
from graphs.graph import debate_app
from core.database import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # ✅ 이 부분을 추가하여 연관 데이터를 미리 로드합니다.
from models.debate_room import DebateRoom
from models.debate_participant import DebateParticipant
from core.config import settings

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print(f"✅ Client connected: {sid}")

@sio.on("join_debate")
async def handle_join(sid, data):
    room_id = str(data.get("room_id"))
    await sio.enter_room(sid, f"debate_{room_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            room_stmt = select(DebateRoom).where(DebateRoom.debate_room_id == int(room_id))
            room_result = await db.execute(room_stmt)
            room = room_result.scalar_one_or_none()
            
            if room:
                # 🔹 [핵심 수정] selectinload(DebateParticipant.user)를 추가하여
                # p.nickname 호출 시 필요한 유저 정보를 미리 가져옵니다.
                part_stmt = (
                    select(DebateParticipant)
                    .options(selectinload(DebateParticipant.user)) 
                    .where(DebateParticipant.debate_room_id == int(room_id))
                )
                part_result = await db.execute(part_stmt)
                participants = part_result.scalars().all()

                config = {"configurable": {"thread_id": f"debate_{room_id}"}}
                
                initial_state = {
                    "topic": room.topic,
                    "pro_users": [
                        {
                            "user_id": str(p.user_id), 
                            # 이제 p.user 정보가 로드되어 있으므로 p.nickname 참조 시 에러가 나지 않습니다.
                            "user_name": p.nickname if hasattr(p, 'nickname') else f"User_{p.user_id}", 
                            "is_premium": False
                        } 
                        for p in participants if p.role == "pro"
                    ],
                    "con_users": [
                        {
                            "user_id": str(p.user_id), 
                            "user_name": p.nickname if hasattr(p, 'nickname') else f"User_{p.user_id}", 
                            "is_premium": False
                        } 
                        for p in participants if p.role == "con"
                    ],
                    "max_turns": room.max_turns or 10,
                    "current_turn": 1,
                    "messages": []
                }
                
                debate_app.update_state(config, initial_state)
                print(f"✅ Room {room_id} 초기화 완료")
            else:
                print(f"⚠️ Room {room_id}를 DB에서 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ 초기화 중 에러 발생: {e}")
            traceback.print_exc()

@sio.on("send_message")
async def handle_message(sid, data):
    room_id = str(data.get("room_id"))
    content = data.get("content")
    config = {"configurable": {"thread_id": f"debate_{room_id}"}}

    try:
        async for event in debate_app.astream(
            {"user_input": content}, 
            config, 
            stream_mode="values"
        ):
            await sio.emit("debate_update", event, room=f"debate_{room_id}")
    except Exception as e:
        print(f"❌ 메시지 처리 중 에러 발생:")
        traceback.print_exc()

@sio.event
async def disconnect(sid):
    print(f"❌ Client disconnected: {sid}")