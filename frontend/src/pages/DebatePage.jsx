import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { io } from "socket.io-client";
import { RiSendPlaneFill, RiRobot2Line, RiTimerLine, RiPlayFill, RiUserVoiceLine } from "react-icons/ri";
import "../styles/DebatePage.css";

function DebatePage() {
    const { roomId } = useParams();
    const { user: currentUser } = useAuth();
    
    const [room, setRoom] = useState(null);
    const [error, setError] = useState("");
    const [messageInput, setMessageInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [debateStarted, setDebateStarted] = useState(false);
    
    // 실시간 상태 관리
    const [roundInfo, setRoundInfo] = useState({
        currentRound: 0,
        turnIndex: 0,
        turnTotal: 0,
        nextSpeaker: null
    });

    const socketRef = useRef(null);
    const chatEndRef = useRef(null);

    // 1. 초기 방 정보 가져오기
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

    // 2. Socket.io 실시간 통신 설정
    useEffect(() => {
        if (!roomId || !currentUser) return;

        const socket = io("http://localhost:8000", {
            path: "/socket.io",
            transports: ["websocket"],
        });
        socketRef.current = socket;

        socket.on("connect", () => {
            console.log("✅ 토론 서버 연결:", socket.id);
            socket.emit("join_debate", { 
                room_id: roomId,
                user_id: currentUser.user_id 
            });
        });

        socket.on("debate_started", () => {
            setDebateStarted(true);
        });

        // 서버의 debate_update 이벤트 처리
        socket.on("debate_update", (data) => {
            console.log("📩 실시간 업데이트:", data);
            
            // 라운드 및 차례 정보 업데이트
            setRoundInfo({
                currentRound: data.current_round,
                turnIndex: data.turn_index,
                turnTotal: data.turn_total,
                nextSpeaker: data.next_speaker
            });

            // 메시지 목록 업데이트 (replace_messages가 true면 전체 교체)
            if (data.messages) {
                const formatted = data.messages.map((m, idx) => ({
                    id: m.id || `${Date.now()}-${idx}`,
                    role: m.role,
                    nickname: m.user_name || (m.role === 'ai' ? 'AI 사회자' : '시스템'),
                    content: m.content,
                    displayType: m.role === 'ai' ? 'moderator' : (m.role === 'system' ? 'system' : 'user')
                }));

                if (data.replace_messages) {
                    setMessages(formatted);
                } else {
                    setMessages(prev => [...prev, ...formatted]);
                }
            }
        });

        socket.on("error", (err) => {
            alert(err.message);
        });

        return () => socket.disconnect();
    }, [roomId, currentUser]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // 토론 시작 (방장용)
    const handleStartDebate = () => {
        socketRef.current?.emit("start_debate", {
            room_id: roomId,
            user_id: currentUser.user_id
        });
    };

    // 메시지 전송
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

    // 내 차례인지 확인하는 로직
    const isMyTurn = roundInfo.nextSpeaker && String(roundInfo.nextSpeaker.user_id) === String(currentUser?.user_id);
    const isCreator = currentUser && parseInt(room?.creator_id) === parseInt(currentUser.user_id);

    if (error) return <div className="debate-container center-msg">{error}</div>;
    if (!room) return <div className="debate-container center-msg">로딩 중...</div>;

    return (
        <div className="debate-container">
            {/* 왼쪽 사이드바: 참가자 목록 */}
            <aside className="participants-sidebar">
                <TeamSection title="찬성 TEAM" type="pro" members={room.participants.filter(p => p.role === "pro")} />
                <TeamSection title="반대 TEAM" type="con" members={room.participants.filter(p => p.role === "con")} />
            </aside>

            <main className="center-main-area">
                <header className="debate-room-header">
                    <div className="header-top">
                        <h1 className="room-title">{room.title}</h1>
                        {isCreator && !debateStarted && (
                            <button className="start-debate-btn" onClick={handleStartDebate}>
                                <RiPlayFill /> 토론 시작하기
                            </button>
                        )}
                    </div>
                    <div className="topic-box">
                        <span className={`category-badge ${room.category}`}>{room.category}</span>
                        <span className="topic-text">{room.topic}</span>
                    </div>
                </header>

                {/* AI 사회자 상태바 - 현재 진행 상황 표시 */}
                <div className="moderator-status-bar">
                    <div className="mod-icon"><RiRobot2Line /></div>
                    <div className="mod-content">
                        <span className="mod-label">AI 사회자</span>
                        <p className="mod-text">
                            {!debateStarted ? "토론 시작을 기다리고 있습니다." : 
                             `[라운드 ${roundInfo.currentRound}] ${roundInfo.nextSpeaker?.user_name || '진행'}님의 차례입니다.`}
                        </p>
                    </div>
                    <div className="timer-badge"><RiTimerLine /> {roundInfo.turnIndex + 1}/{roundInfo.turnTotal || 0}</div>
                </div>

                {/* 채팅창 */}
                <div className="chat-window">
                    {messages.map((msg) => (
                        <MessageRow key={msg.id} msg={msg} isMe={msg.nickname === currentUser?.nickname} />
                    ))}
                    <div ref={chatEndRef} />
                </div>

                {/* 입력창 - 내 차례가 아니면 비활성화 */}
                <form className="input-area" onSubmit={handleSendMessage}>
                    <div className="turn-indicator">
                        {isMyTurn ? <span className="my-turn"><RiUserVoiceLine /> 내 차례입니다!</span> : 
                         debateStarted ? <span className="not-my-turn">상대방의 발언을 듣고 있습니다...</span> : null}
                    </div>
                    <div className="input-wrapper">
                        <input
                            type="text"
                            placeholder={!debateStarted ? "토론 시작 대기 중..." : isMyTurn ? "메시지를 입력하세요..." : "지금은 발언권이 없습니다."}
                            value={messageInput}
                            onChange={(e) => setMessageInput(e.target.value)}
                            disabled={!debateStarted || !isMyTurn}
                        />
                        <button type="submit" className="send-btn" disabled={!messageInput.trim() || !isMyTurn}>
                            <RiSendPlaneFill />
                        </button>
                    </div>
                </form>
            </main>
        </div>
    );
}

// 컴포넌트 분리: 팀 목록
function TeamSection({ title, type, members }) {
    return (
        <div className={`team-section ${type}`}>
            <div className={`team-header-card ${type}`}>
                <h2>{title}</h2>
                <span className="count-badge">{members.length}명</span>
            </div>
            <div className="user-list">
                {members.map((p) => (
                    <div key={p.user_id} className={`participant-card ${type}`}>
                        <div className="avatar-wrapper">
                            <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${p.nickname}`} alt={p.nickname} />
                        </div>
                        <div className="participant-info">
                            <span className="nickname">{p.nickname}</span>
                            <span className="role-badge">{type === 'pro' ? '찬성' : '반대'} 토론자</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// 컴포넌트 분리: 메시지 행
function MessageRow({ msg, isMe }) {
    if (msg.displayType === 'system') return <div className="system-message"><span>{msg.content}</span></div>;
    
    if (msg.displayType === 'moderator') return (
        <div className="message-row moderator">
            <div className="msg-avatar mod"><RiRobot2Line /></div>
            <div className="msg-bubble mod">{msg.content}</div>
        </div>
    );

    return (
        <div className={`message-row ${msg.role} ${isMe ? 'me' : ''}`}>
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
}

export default DebatePage;