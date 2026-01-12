import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { io } from "socket.io-client"; // ✅ socket.io-client 임포트
import { RiSendPlaneFill, RiRobot2Line, RiTimerLine } from "react-icons/ri";
import "../styles/DebatePage.css";

function DebatePage() {
    const { roomId } = useParams();
    const { user: currentUser } = useAuth();
    const [room, setRoom] = useState(null);
    const [error, setError] = useState("");

    // 채팅 관련 상태
    const [messageInput, setMessageInput] = useState("");
    const [messages, setMessages] = useState([]);
    const socketRef = useRef(null); // ✅ Socket 객체를 유지하기 위한 Ref
    const chatEndRef = useRef(null);

    // 1. 방 정보 가져오기 (REST API)
    useEffect(() => {
        const fetchRoom = async () => {
            try {
                const token = localStorage.getItem("access_token");
                const response = await fetch(`http://localhost:8000/api/debates/${roomId}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    setRoom(data);
                } else {
                    setError("방 정보를 불러오지 못했습니다.");
                }
            } catch (err) {
                console.error(err);
                setError("서버 통신 오류");
            }
        };
        fetchRoom();
    }, [roomId]);

    // 2. 🔹 Socket.io 연결 및 이벤트 리스너 설정
    useEffect(() => {
        if (!roomId) return;

        // Socket.io 연결 시도 (백엔드 포트 8000)
        const socket = io("http://localhost:8000", {
            path: "/socket.io",
            transports: ["websocket"], // 성능을 위해 웹소켓 전송 강제
        });
        socketRef.current = socket;

        socket.on("connect", () => {
            console.log("✅ Socket.io 연결 성공:", socket.id);
            // 방 입장 이벤트 전송 (백엔드에서 sio.enter_room 처리를 위함)
            socket.emit("join_debate", { room_id: roomId });
            setMessages([{ id: 'sys-start', type: 'system', content: "토론 서버에 연결되었습니다." }]);
        });

        // 서버로부터 실시간 상태 업데이트 수신 (LangGraph의 State 데이터)
        socket.on("debate_update", (data) => {
            console.log("📩 서버 메시지 수신:", data);
            if (data.messages) {
                // LangGraph의 메시지 배열을 UI 형식에 맞춰 변환
                const formatted = data.messages.map((m, idx) => ({
                    id: `msg-${idx}`,
                    role: m.role || 'moderator',
                    nickname: m.user_name || (m.role === 'ai' ? 'AI 사회자' : '시스템'),
                    content: m.content,
                    type: m.role === 'ai' ? 'moderator' : (m.role === 'system' ? 'system' : 'user')
                }));
                setMessages(formatted);
            }
        });

        socket.on("connect_error", (err) => {
            console.error("❌ 연결 에러:", err);
            setError("실시간 통신 연결에 실패했습니다.");
        });

        socket.on("disconnect", (reason) => {
            console.log("❌ 연결 종료:", reason);
        });

        // 클린업: 컴포넌트 언마운트 시 연결 해제
        return () => {
            if (socket) socket.disconnect();
        };
    }, [roomId]);

    // 스크롤 자동 이동
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // 3. 🔹 메시지 전송 로직
    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!messageInput.trim() || !socketRef.current) return;

        // 서버에 'send_message' 이벤트로 데이터 전송
        socketRef.current.emit("send_message", {
            room_id: roomId,
            user_id: currentUser?.user_id,
            user_name: currentUser?.nickname || "익명",
            content: messageInput
        });

        setMessageInput("");
    };

    const getCategoryName = (catCode) => {
        const categories = { korean: '국어', social: '사회', moral: '도덕', ethics: '윤리' };
        return categories[catCode] || '기타';
    };

    if (error) return <div className="debate-container center-msg">{error}</div>;
    if (!room) return <div className="debate-container center-msg">로딩 중...</div>;

    const proTeam = room.participants.filter(p => p.role === "pro");
    const conTeam = room.participants.filter(p => p.role === "con");

    return (
        <div className="debate-container">
            {/* 왼쪽 사이드바 (참가자 목록) */}
            <aside className="participants-sidebar">
                <div className="team-section pro">
                    <div className="team-header-card pro">
                        <h2>찬성 TEAM</h2>
                        <span className="count-badge">{proTeam.length}명</span>
                    </div>
                    <div className="user-list">
                        {proTeam.map((p) => (
                            <div key={p.user_id} className="participant-card pro">
                                <div className="avatar-wrapper">
                                    <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${p.nickname}`} alt={p.nickname} />
                                </div>
                                <div className="participant-info">
                                    <span className="nickname">{p.nickname}</span>
                                    <span className="role-badge">찬성 토론자</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="team-section con">
                    <div className="team-header-card con">
                        <h2>반대 TEAM</h2>
                        <span className="count-badge">{conTeam.length}명</span>
                    </div>
                    <div className="user-list">
                        {conTeam.map((p) => (
                            <div key={p.user_id} className="participant-card con">
                                <div className="avatar-wrapper">
                                    <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${p.nickname}`} alt={p.nickname} />
                                </div>
                                <div className="participant-info">
                                    <span className="nickname">{p.nickname}</span>
                                    <span className="role-badge">반대 토론자</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </aside>

            {/* 중앙 메인 영역 */}
            <main className="center-main-area">
                <header className="debate-room-header">
                    <h1 className="room-title">{room.title}</h1>
                    <div className="topic-box">
                        <span className={`category-badge ${room.category}`}>{getCategoryName(room.category)}</span>
                        <span className="topic-text">{room.topic}</span>
                    </div>
                </header>

                {/* AI 사회자 상태 바 */}
                <div className="moderator-status-bar">
                    <div className="mod-icon"><RiRobot2Line /></div>
                    <div className="mod-content">
                        <span className="mod-label">AI 사회자</span>
                        <p className="mod-text">실시간으로 토론을 분석하고 있습니다.</p>
                    </div>
                    <div className="timer-badge"><RiTimerLine /> 실시간</div>
                </div>

                {/* 채팅 내역 영역 */}
                <div className="chat-window">
                    {messages.map((msg) => {
                        const isMe = msg.nickname === currentUser?.nickname;
                        if (msg.type === 'system') return <div key={msg.id} className="system-message"><span>{msg.content}</span></div>;
                        if (msg.type === 'moderator') return (
                            <div key={msg.id} className="message-row moderator">
                                <div className="msg-avatar mod"><RiRobot2Line /></div>
                                <div className="msg-bubble mod">{msg.content}</div>
                            </div>
                        );

                        return (
                            <div key={msg.id} className={`message-row ${msg.role} ${isMe ? 'me' : ''}`}>
                                {!isMe && (
                                    <div className="msg-avatar">
                                        <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${msg.nickname}`} alt="p" />
                                    </div>
                                )}
                                <div className="msg-content">
                                    {!isMe && <span className="msg-name">{msg.nickname}</span>}
                                    <div className={`msg-bubble ${msg.role}`}>{msg.content}</div>
                                </div>
                            </div>
                        );
                    })}
                    <div ref={chatEndRef} />
                </div>

                {/* 입력창 */}
                <form className="input-area" onSubmit={handleSendMessage}>
                    <input
                        type="text"
                        placeholder="메시지를 입력하세요..."
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                    />
                    <button type="submit" className="send-btn" disabled={!messageInput.trim()}>
                        <RiSendPlaneFill />
                    </button>
                </form>
            </main>
        </div>
    );
}

export default DebatePage;