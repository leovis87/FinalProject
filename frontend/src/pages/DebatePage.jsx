import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { RiSendPlaneFill, RiRobot2Line, RiTimerLine } from "react-icons/ri";
import "../styles/DebatePage.css";

function DebatePage() {
    const { roomId } = useParams();
    const { user: currentUser } = useAuth();
    const [room, setRoom] = useState(null);
    const [error, setError] = useState("");

    // 채팅 관련 상태 (더미 데이터)
    const [messageInput, setMessageInput] = useState("");
    const [messages, setMessages] = useState([
        { id: 1, type: "system", content: "토론방에 입장하셨습니다." },
        { id: 2, type: "moderator", content: "지금부터 토론을 시작하겠습니다." },
        { id: 3, role: "pro", nickname: "토론왕", content: "안녕하세요, 찬성 측 입론 시작하겠습니다." },
        { id: 4, role: "con", nickname: "반대파", content: "반대 측입니다. 잘 부탁드립니다." },
    ]);

    const chatEndRef = useRef(null);

    // 방 정보 가져오기
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

    // 스크롤 자동 이동
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!messageInput.trim()) return;

        const newMessage = {
            id: Date.now(),
            role: "pro", // 테스트용
            nickname: currentUser?.nickname || "나",
            content: messageInput
        };

        setMessages(prev => [...prev, newMessage]);
        setMessageInput("");
    };

    const getCategoryName = (catCode) => {
        switch (catCode) {
            case 'korean': return '국어';
            case 'social': return '사회';
            case 'moral': return '도덕';
            case 'ethics': return '윤리';
            default: return '기타';
        }
    };

    if (error) return <div className="debate-container center-msg">{error}</div>;
    if (!room) return <div className="debate-container center-msg">로딩 중...</div>;

    const proTeam = room.participants.filter(p => p.role === "pro");
    const conTeam = room.participants.filter(p => p.role === "con");

    return (
        <div className="debate-container">
            {/* --- 왼쪽 사이드바 (팀 목록) --- */}
            <aside className="participants-sidebar">
                {/* 상단: 찬성 팀 */}
                <div className="team-section pro">
                    <div className="team-header-card pro">
                        <h2>찬성 TEAM</h2>
                        <span className="count-badge">{proTeam.length}명</span>
                    </div>
                    <div className="user-list">
                        {proTeam.map((p) => (
                            <div key={p.user_id} className="participant-card pro">
                                <div className="avatar-wrapper">
                                    <img
                                        src={`https://api.dicebear.com/9.x/notionists/svg?seed=${p.nickname}`}
                                        alt={p.nickname}
                                    />
                                </div>
                                <div className="participant-info">
                                    <span className="nickname">{p.nickname}</span>
                                    <span className="role-badge">찬성 토론자</span>
                                </div>
                            </div>
                        ))}
                        {proTeam.length === 0 && <div className="empty-slot">대기 중...</div>}
                    </div>
                </div>

                {/* 하단: 반대 팀 */}
                <div className="team-section con">
                    <div className="team-header-card con">
                        <h2>반대 TEAM</h2>
                        <span className="count-badge">{conTeam.length}명</span>
                    </div>
                    <div className="user-list">
                        {conTeam.map((p) => (
                            <div key={p.user_id} className="participant-card con">
                                <div className="avatar-wrapper">
                                    <img
                                        src={`https://api.dicebear.com/9.x/notionists/svg?seed=${p.nickname}`}
                                        alt={p.nickname}
                                    />
                                </div>
                                <div className="participant-info">
                                    <span className="nickname">{p.nickname}</span>
                                    <span className="role-badge">반대 토론자</span>
                                </div>
                            </div>
                        ))}
                        {conTeam.length === 0 && <div className="empty-slot">대기 중...</div>}
                    </div>
                </div>
            </aside>

            {/* --- 중앙 메인 영역 --- */}
            <main className="center-main-area">
                {/* 1. 상단 정보 (제목/카테고리+논제/설명) */}
                <header className="debate-room-header">
                    <div className="header-top">
                        <h1 className="room-title">{room.title}</h1>
                    </div>
                    <div className="topic-box">
                        <span className={`category-badge ${room.category}`}>
                            {getCategoryName(room.category)}
                        </span>
                        <span className="topic-text">{room.topic}</span>
                    </div>
                    {room.topic_description && (
                        <div className="topic-desc-box">
                            <p>{room.topic_description}</p>
                        </div>
                    )}
                </header>

                {/* 2. 사회자 멘트 영역 */}
                <div className="moderator-status-bar">
                    <div className="mod-icon">
                        <RiRobot2Line />
                    </div>
                    <div className="mod-content">
                        <span className="mod-label">AI 사회자</span>
                        <p className="mod-text">현재 <span className="highlight">찬성 측 입론</span> 단계입니다. 발언 시간은 3분입니다.</p>
                    </div>
                    <div className="timer-badge">
                        <RiTimerLine /> 02:59
                    </div>
                </div>

                {/* 3. 채팅 내역 */}
                <div className="chat-window">
                    {messages.map((msg) => {
                        const isMe = msg.nickname === (currentUser?.nickname || "나");
                        const isModerator = msg.type === 'moderator';
                        const isSystem = msg.type === 'system';

                        if (isSystem) {
                            return <div key={msg.id} className="system-message"><span>{msg.content}</span></div>;
                        }

                        if (isModerator) {
                            return (
                                <div key={msg.id} className="message-row moderator">
                                    <div className="msg-avatar mod">
                                        <RiRobot2Line />
                                    </div>
                                    <div className="msg-bubble mod">
                                        {msg.content}
                                    </div>
                                </div>
                            );
                        }

                        return (
                            <div key={msg.id} className={`message-row ${msg.role} ${isMe ? 'me' : ''}`}>
                                {!isMe && (
                                    <div className="msg-avatar">
                                        <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${msg.nickname}`} alt="profile" />
                                    </div>
                                )}
                                <div className="msg-content">
                                    {!isMe && <span className="msg-name">{msg.nickname}</span>}
                                    <div className={`msg-bubble ${msg.role}`}>
                                        {msg.content}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                    <div ref={chatEndRef} />
                </div>

                {/* 4. 하단 입력창 */}
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