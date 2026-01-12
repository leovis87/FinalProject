from fastapi import WebSocket
from typing import List, Dict
import json

# 연결된 클라이언트들을 저장하는 리스트
# 비유: 토론방에 들어온 사람들의 명단
class ConnectionManager:
    """
    연결 관리 로직을 한 곳에 모아두는 class.
        - 추가 / 삭세 / 개별 메시지 / 브로드캐스트(전체)
    """
    def __init__(self):
        # active_connections = 현재 접속 중인 WebSocket들의 리스트
        # Dict:
        #   Key: room_id
        #   Value: WebSocket List
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self,
                      room_id: str,
                      websocket: WebSocket):
        """
        특정 토론방 연결

        비유: 토론방에 새 사람이 들어옴
            - websocket.accept(): 서버가 연결을 받아들이는 정식 허가 (통로 개통)
                -> 정식 허가 이후, websocket.send_text() / websocket.receive_text()
                사용 가능해 짐.
            - 왜 .append(websocket)?:
                -> 각 사용자에게 websocket 객체를 부여(개통)하기 때문.
        """
        await websocket.accept()  # 연결 수락 (악수하는 것)

        # 해당 room_id의 리스트에 추가
        if room_id not in self.active_connections:
            # 초기화
            self.active_connections[room_id]= []

        self.active_connections[room_id].append(websocket) # room_id의 리스트에 추가
        print(f"✅ {room_id}방에 연결! 현재 {len(self.active_connections)}명 접속 중")
    
    def disconnect(self,
                   room_id: str,
                   websocket: WebSocket):
        """
        특정 토론방 연결 해제
        비유: 토론방에서 사람이 나감
        """
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
        print(f"❌ {room_id} 연결 종료! 현재 {len(self.active_connections)}명 접속 중")
    
    async def send_personal_message(self,
                                    room_id: str,
                                    message: str,
                                    websocket: WebSocket):
        """
        특정 사용자에게 메시지 전송
        비유: 특정 사람에게만 귓속말
            - 예: 특정 사용자가 '욕설' | '부적절한 언행' 시,
            해당 사용자에게만 '경고: 채팅 규칙을 지켜주세요'와 같은 메시지 송출 가능
        """
        if room_id not in self.active_connections:
            return
        
        message_json = json.dumps(message, ensure_ascii = False)
        await websocket.send_text(message_json)
    
    async def broadcast(self,
                        room_id: str,
                        message: str):
        """
        특정 토론방의 모든 사용자에게 메시지 전송
        비유: 토론방 전체에 공지
        """
        if room_id not in self.active_connections:
            return
        
        # broadcast 함수 내부에서 json string 직렬화
        # 호출부에서는 직렬화 불필요.
        #   -> manager.broadcast(room_id,
        #                        {"type": "...", "client_id": "...", "message": f"{client_id}님 환영합니다!"})
        message_json = json.dumps(message, ensure_ascii = False)

        for connection in self.active_connections[room_id]:
            await connection.send_text(message_json)