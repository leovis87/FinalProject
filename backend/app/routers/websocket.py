from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from graphs.graph import debate_app
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import json

router = APIRouter()

@router.websocket("/ws/debate/{room_id}")
async def debate_websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    
    # 1. 초기 상태 설정 (DB에서 방 정보를 가져와서 세팅 가능)
    # config의 thread_id를 room_id로 설정하여 대화 기록 유지
    config = {"configurable": {"thread_id": room_id}}
    
    try:
        while True:
            # 2. 클라이언트로부터 메시지 수신 (예: 유저의 발언)
            data = await websocket.receive_text()
            user_input = json.loads(data) # { "user_id": "...", "content": "..." }

            # 3. LangGraph 업데이트 및 실행
            # 유저의 입력을 State에 반영하고 다음 노드 실행
            # 'stream' 모드를 사용하면 노드별 진행 상황을 실시간으로 보낼 수 있음
            async for event in debate_app.astream(
                {"messages": [("user", user_input['content'])]}, 
                config, 
                stream_mode="values"
            ):
                # 4. LangGraph의 실행 결과(State)를 클라이언트에 전송
                # 예: AI 사회자의 멘트, 심판의 판정 등
                await websocket.send_json(event)

    except WebSocketDisconnect:
        print(f"Client disconnected from room {room_id}")