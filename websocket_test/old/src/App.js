import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  // ========================================
  // 상태 관리 (State)
  // ========================================
  
  // 사용자 ID (처음 입장할 때 입력)
  const [clientId, setClientId] = useState('');
  
  // 현재 입력 중인 메시지
  const [message, setMessage] = useState('');
  
  // 받은 메시지들을 저장하는 배열
  const [messages, setMessages] = useState([]);
  
  // WebSocket 연결 상태 (true: 연결됨, false: 끊어짐)
  const [isConnected, setIsConnected] = useState(false);
  
  // WebSocket 객체를 저장 (useRef로 관리)
  // 비유: 전화기 자체를 저장해둠
  const ws = useRef(null);

  // ========================================
  // WebSocket 연결 함수
  // ========================================
  const connectWebSocket = () => {
    if (!clientId.trim()) {
      alert('사용자 ID를 입력하세요!');
      return;
    }

    // WebSocket 연결 생성
    // ws://localhost:8000/ws/user123 형태로 연결
    ws.current = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

    // 연결 성공 시 실행되는 함수
    ws.current.onopen = () => {
      console.log('✅ WebSocket 연결 성공!');
      setIsConnected(true);
      
      // 시스템 메시지 추가
      setMessages(prev => [...prev, {
        type: 'system',
        content: '서버에 연결되었습니다!',
        timestamp: new Date().toLocaleTimeString()
      }]);
    };

    // 메시지를 받았을 때 실행되는 함수
    ws.current.onmessage = (event) => {
      console.log('📩 메시지 받음:', event.data);
      
      try {
        // JSON 파싱
        const data = JSON.parse(event.data);
        
        // messages 배열에 추가
        setMessages(prev => [...prev, {
          type: data.type,
          content: data.message || data.echo || data.original,
          clientId: data.client_id,
          timestamp: data.timestamp || new Date().toLocaleTimeString(),
          original: data.original
        }]);
      } catch (error) {
        console.error('메시지 파싱 오류:', error);
      }
    };

    // 연결이 끊어졌을 때 실행되는 함수
    ws.current.onclose = () => {
      console.log('❌ WebSocket 연결 종료');
      setIsConnected(false);
      
      setMessages(prev => [...prev, {
        type: 'system',
        content: '서버 연결이 끊어졌습니다.',
        timestamp: new Date().toLocaleTimeString()
      }]);
    };

    // 오류 발생 시 실행되는 함수
    ws.current.onerror = (error) => {
      console.error('⚠️ WebSocket 오류:', error);
      
      setMessages(prev => [...prev, {
        type: 'error',
        content: '연결 오류가 발생했습니다.',
        timestamp: new Date().toLocaleTimeString()
      }]);
    };
  };

  // ========================================
  // 메시지 전송 함수
  // ========================================
  const sendMessage = () => {
    if (!message.trim()) {
      alert('메시지를 입력하세요!');
      return;
    }

    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      alert('서버에 연결되지 않았습니다!');
      return;
    }

    // WebSocket으로 메시지 전송
    ws.current.send(message);
    console.log('📤 메시지 전송:', message);

    // 입력창 비우기
    setMessage('');
  };

  // ========================================
  // 연결 종료 함수
  // ========================================
  const disconnect = () => {
    if (ws.current) {
      // "종료" 메시지 보내기 (서버에서 break 실행됨)
      ws.current.send('종료');
      
      // WebSocket 연결 닫기
      ws.current.close();
      ws.current = null;
    }
    setIsConnected(false);
  };

  // ========================================
  // 컴포넌트가 언마운트될 때 연결 종료
  // ========================================
  useEffect(() => {
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  // ========================================
  // 엔터 키로 메시지 전송
  // ========================================
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      if (!isConnected) {
        connectWebSocket();
      } else {
        sendMessage();
      }
    }
  };

  // ========================================
  // UI 렌더링
  // ========================================
  return (
    <div className="App">
      <header className="App-header">
        <h1>🌐 WebSocket 실시간 에코 챗봇</h1>
        
        {/* 연결 상태 표시 */}
        <div className="status">
          {isConnected ? (
            <span className="connected">✅ 연결됨</span>
          ) : (
            <span className="disconnected">❌ 연결 안 됨</span>
          )}
        </div>

        {/* 연결 전: 사용자 ID 입력 */}
        {!isConnected && (
          <div className="connect-section">
            <input
              type="text"
              placeholder="사용자 ID 입력 (예: user123)"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              onKeyPress={handleKeyPress}
              className="input"
            />
            <button onClick={connectWebSocket} className="button connect">
              연결하기
            </button>
          </div>
        )}

        {/* 연결 후: 메시지 입력 */}
        {isConnected && (
          <div className="chat-section">
            <div className="messages-container">
              {messages.map((msg, index) => (
                <div 
                  key={index} 
                  className={`message ${msg.type}`}
                >
                  <span className="timestamp">[{msg.timestamp}]</span>
                  {msg.clientId && <span className="client-id">{msg.clientId}: </span>}
                  <span className="content">{msg.content}</span>
                  {msg.original && msg.type === 'echo' && (
                    <span className="original"> (원본: {msg.original})</span>
                  )}
                </div>
              ))}
            </div>

            <div className="input-section">
              <input
                type="text"
                placeholder="메시지 입력..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                className="input"
              />
              <button onClick={sendMessage} className="button send">
                전송
              </button>
              <button onClick={disconnect} className="button disconnect">
                연결 종료
              </button>
            </div>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;