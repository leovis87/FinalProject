import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { io } from "socket.io-client";
import { RiSendPlaneFill, RiRobot2Line, RiTimerLine, RiPlayFill } from "react-icons/ri";
import "../styles/DebatePage.css";

function DebatePage() {
    const { roomId } = useParams();
    const { user: currentUser } = useAuth();
    const [room, setRoom] = useState(null);
    const [error, setError] = useState("");

    const [messageInput, setMessageInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [debateStarted, setDebateStarted] = useState(false); // 토론 시작 여부 상태
    const socketRef = useRef(null);
    const chatEndRef = useRef(null);

    // 1. 방 정보 가져오기
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
                    // 방 상태가 이미 진행 중이라면 시작 버튼을 숨김
                    if (data.status !== "waiting") {
                        setDebateStarted(true);
                    }
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

    // 2. Socket.io 연결
    useEffect(() => {
        if (!roomId || !currentUser) return;

        const socket = io("http://localhost:8000", {
            path: "/socket.io",
            transports: ["websocket"],
        });
        socketRef.current = socket;

        socket.on("connect", () => {
            console.log("✅ Socket.io 연결 성공:", socket.id);
            // 소켓 접속 시 join_debate 전송
            socket.emit("join_debate", { 
                room_id: roomId,
                user_id: currentUser.user_id 
            });
            setMessages([{ id: 'sys-start', type: 'system', content: "토론 서버에 연결되었습니다." }]);
        });

        // 서버에서 토론이 시작됨을 알림 (방장의 start_debate 성공 시)
        socket.on("debate_started", (data) => {
            console.log("🚀 토론이 시작되었습니다!");
            setDebateStarted(true);
        });

        socket.on("debate_update", (data) => {
            console.log("📩 서버 업데이트:", data);
            if (data.messages && Array.isArray(data.messages)) {
                const formatted = data.messages.map((m, idx) => ({
                    id: m.id || `msg-${idx}`,
                    role: m.role,
                    nickname: m.user_name || (m.role === 'ai' ? 'AI 사회자' : '시스템'),
                    content: m.content,
                    displayType: m.role === 'ai' ? 'moderator' : (m.role === 'system' ? 'system' : 'user')
                }));
                setMessages(formatted);
            }
        });

        socket.on("error", (err) => {
            alert(err.message); // "Only the creator can start." 등의 에러 메시지 표시
        });

        return () => {
            if (socket) socket.disconnect();
        };
    }, [roomId, currentUser]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // [추가] 토론 시작 버튼 클릭 핸들러
    const handleStartDebate = () => {
        if (!socketRef.current || !currentUser) return;

        // 서버의 handle_start(sid, data)는 room_id와 user_id를 기대함
        socketRef.current.emit("start_debate", {
            room_id: roomId,
            user_id: currentUser.user_id
        });
    };

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!messageInput.trim() || !socketRef.current) return;

        socketRef.current.emit("send_message", {
            room_id: roomId,
            user_id: currentUser.user_id,
            user_name: currentUser.nickname,
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
    
    // 현재 접속자가 방장인지 확인
    const isCreator = currentUser && parseInt(room.creator_id) === parseInt(currentUser.user_id);

    return (
        <div className="debate-container">
            <aside className="participants-sidebar">
                {/* ... (팀 목록 UI는 이전과 동일) ... */}
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

            <main className="center-main-area">
                <header className="debate-room-header">
                    <div className="header-top">
                        <h1 className="room-title">{room.title}</h1>
                        {/* 🚀 방장이고 토론이 시작되지 않았을 때만 '토론 시작' 버튼 노출 */}
                        {isCreator && !debateStarted && (
                            <button className="start-debate-btn" onClick={handleStartDebate}>
                                <RiPlayFill /> 토론 시작하기
                            </button>
                        )}
                    </div>
                    <div className="topic-box">
                        <span className={`category-badge ${room.category}`}>{getCategoryName(room.category)}</span>
                        <span className="topic-text">{room.topic}</span>
                    </div>
                </header>

                <div className="moderator-status-bar">
                    <div className="mod-icon"><RiRobot2Line /></div>
                    <div className="mod-content">
                        <span className="mod-label">AI 사회자</span>
                        <p className="mod-text">
                            {debateStarted ? "토론이 진행 중입니다." : "토론 시작을 기다리고 있습니다."}
                        </p>
                    </div>
                    <div className="timer-badge"><RiTimerLine /> 실시간</div>
                </div>

                <div className="chat-window">
                    {messages.map((msg) => {
                        const isMe = msg.nickname === currentUser?.nickname;
                        if (msg.displayType === 'system') return <div key={msg.id} className="system-message"><span>{msg.content}</span></div>;
                        if (msg.displayType === 'moderator') return (
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

                <form className="input-area" onSubmit={handleSendMessage}>
                    <input
                        type="text"
                        placeholder={debateStarted ? "메시지를 입력하세요..." : "토론이 시작된 후 입력 가능합니다."}
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        disabled={!debateStarted} // 시작 전에는 입력 불가
                    />
                    <button type="submit" className="send-btn" disabled={!messageInput.trim() || !debateStarted}>
                        <RiSendPlaneFill />
                    </button>
                </form>
            </main>
        </div>
    );
}

export default DebatePage;