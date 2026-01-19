import { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { io } from "socket.io-client";
import { 
    RiSendPlaneFill, 
    RiRobot2Line, 
    RiTimerLine, 
    RiPlayFill, 
    RiUserVoiceLine,
    RiTrophyLine,
    RiMedalLine,
    RiBarChartFill,
    RiFileTextLine,
    RiCheckLine,
    RiInformationLine,
    RiLogoutBoxLine
} from "react-icons/ri";
import "../styles/DebatePage.css";

function DebatePage() {
    const { roomId } = useParams();
    const navigate = useNavigate();
    const { user: currentUser } = useAuth();
    
    const [room, setRoom] = useState(null);
    const [error, setError] = useState("");
    const [messageInput, setMessageInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [debateStarted, setDebateStarted] = useState(false);
    const [debateEnded, setDebateEnded] = useState(false);
    const [turnRemaining, setTurnRemaining] = useState(null);
    const [selectionRemaining, setSelectionRemaining] = useState(null);
    const [hasRaised, setHasRaised] = useState(false);
    
    // 실시간 상태 관리 (라운드, 턴 정보)
    const [roundInfo, setRoundInfo] = useState({
        currentRound: 0,
        turnIndex: 0,
        turnTotal: 0,
        nextSpeaker: null,
        turnDeadline: null,
        selectionActive: false,
        selectionDeadline: null,
        selectionRound: null
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
                    // 방 상태가 진행 중이면 debateStarted를 true로 설정하여 입력창 활성화
                    if (data.status !== "waiting") {
                        setDebateStarted(true);
                    }
                    if (data.status === "finished") {
                        setDebateEnded(true);
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
            
            // ⭐ [해결] 발언권 문제 해결: 업데이트 데이터가 오고 라운드가 1 이상이면 토론 진행 중으로 간주
            if (data.current_round > 0) {
                setDebateStarted(true);
            }

            // 라운드 및 차례 정보 업데이트
            setRoundInfo({
                currentRound: data.current_round,
                turnIndex: data.turn_index,
                turnTotal: data.turn_total,
                nextSpeaker: data.next_speaker,
                turnDeadline: data.turn_deadline || null,
                selectionActive: Boolean(data.selection_active),
                selectionDeadline: data.selection_deadline || null,
                selectionRound: data.selection_round ?? null
            });

            // 메시지 목록 업데이트
            if (data.messages) {
                const formatted = data.messages.map((m, idx) => ({
                    id: m.id || `${Date.now()}-${idx}`,
                    role: m.role,
                    userId: m.user_id ?? null,
                    turn: m.turn ?? null,
                    nickname: m.user_name || (m.role === 'ai' ? 'AI 사회자' : '알 수 없음'),
                    content: m.content,
                    // 서버에서 display_type이 없으면 role 기준으로 기본값 설정
                    displayType: m.display_type || (m.role === 'ai' ? 'moderator' : (m.role === 'system' ? 'system' : 'user'))
                }));

                if (data.replace_messages) {
                    setMessages(formatted.filter((msg) => msg.displayType !== 'loading' && msg.displayType !== 'loading_end'));
                } else {
                    setMessages(prev => {
                        let next = [...prev];
                        formatted.forEach((msg) => {
                            if (msg.displayType === 'loading_end') {
                                next = next.filter((item) => item.displayType !== 'loading');
                                return;
                            }

                            if (msg.displayType === 'loading') {
                                next = next.filter((item) => item.displayType !== 'loading');
                                next.push(msg);
                                return;
                            }

                            next = next.filter((item) => item.displayType !== 'loading');

                            if (msg.displayType !== 'draft' && msg.userId && msg.turn !== null) {
                                next = next.filter((item) => !(
                                    item.displayType === 'draft' &&
                                    item.userId === msg.userId &&
                                    item.turn === msg.turn
                                ));
                            }
                            next.push(msg);
                        });
                        return next;
                    });
                }
            }
        });


        socket.on("participants_update", (data) => {
            if (!data?.participants) return;
            setRoom((prev) => (prev ? { ...prev, participants: data.participants } : prev));
        });

        socket.on("debate_ended", () => {
            setDebateEnded(true);
        });

        socket.on("error", (err) => {
            alert(err.message);
        });

        return () => socket.disconnect();
    }, [roomId, currentUser]);

    // 새 메시지 올 때마다 자동 스크롤
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (debateEnded || !roundInfo.turnDeadline) {
            setTurnRemaining(null);
            return;
        }

        const deadline = new Date(roundInfo.turnDeadline);
        if (Number.isNaN(deadline.getTime())) {
            setTurnRemaining(null);
            return;
        }

        const updateRemaining = () => {
            const diffMs = deadline.getTime() - Date.now();
            const seconds = Math.max(0, Math.ceil(diffMs / 1000));
            setTurnRemaining(seconds);
        };

        updateRemaining();
        const intervalId = setInterval(updateRemaining, 1000);
        return () => clearInterval(intervalId);
    }, [roundInfo.turnDeadline, debateEnded]);

    useEffect(() => {
        if (debateEnded || !roundInfo.selectionActive || !roundInfo.selectionDeadline) {
            setSelectionRemaining(null);
            return;
        }

        const deadline = new Date(roundInfo.selectionDeadline);
        if (Number.isNaN(deadline.getTime())) {
            setSelectionRemaining(null);
            return;
        }

        const updateRemaining = () => {
            const diffMs = deadline.getTime() - Date.now();
            const seconds = Math.max(0, Math.ceil(diffMs / 1000));
            setSelectionRemaining(seconds);
        };

        updateRemaining();
        const intervalId = setInterval(updateRemaining, 1000);
        return () => clearInterval(intervalId);
    }, [roundInfo.selectionActive, roundInfo.selectionDeadline, debateEnded]);

    useEffect(() => {
        setHasRaised(false);
    }, [roundInfo.selectionRound, roundInfo.selectionActive]);

    // 토론 시작 (방장용)
    const handleEndDebate = () => {
        if (!socketRef.current) return;
        if (!window.confirm("토론을 종료하시겠습니까?")) return;
        socketRef.current.emit("end_debate", {
            room_id: roomId,
            user_id: currentUser.user_id
        });
    };

    const handleEndSpeaking = () => {
        if (!socketRef.current) return;
        socketRef.current.emit("end_speaking", {
            room_id: roomId,
            user_id: currentUser.user_id
        });
    };

    const handleRaiseHand = () => {
        if (!socketRef.current) return;
        socketRef.current.emit("raise_hand", {
            room_id: roomId,
            user_id: currentUser.user_id
        });
        setHasRaised(true);
    };

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
            content: messageInput.trim()
        });

        setMessageInput("");
    };

    const formatRemaining = (seconds) => {
        if (seconds === null || seconds === undefined) return "";
        const safeSeconds = Math.max(0, seconds);
        const minutes = Math.floor(safeSeconds / 60);
        const rest = safeSeconds % 60;
        return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
    };

    // 내 차례인지 확인하는 로직 (input 비활성화 해제용)
    const participants = room?.participants ?? [];
    const isMyTurn = roundInfo.nextSpeaker && String(roundInfo.nextSpeaker.user_id) === String(currentUser?.user_id);
    const isCreator = currentUser && parseInt(room?.creator_id) === parseInt(currentUser.user_id);
    const myRole = participants.find((p) => String(p.user_id) === String(currentUser?.user_id))?.role;
    const canRaiseHand = roundInfo.selectionActive && !debateEnded && myRole && myRole !== "observer";

    const handleLeaveDebate = () => {
        if (socketRef.current) {
            socketRef.current.emit("leave_debate", {
                room_id: roomId,
                user_id: currentUser?.user_id,
            });
            socketRef.current.disconnect();
        }
        navigate("/");
    };

    if (error) return <div className="debate-container center-msg">{error}</div>;
    if (!room) return <div className="debate-container center-msg">로딩 중...</div>;

    return (
        <div className="debate-container">
            {/* 왼쪽 사이드바: 참가자 목록 */}
            <aside className="participants-sidebar">
                <TeamSection title="찬성 TEAM" type="pro" members={participants.filter((p) => p.role === "pro")} />
                <TeamSection title="반대 TEAM" type="con" members={participants.filter((p) => p.role === "con")} />
            </aside>

            <main className="center-main-area">
                <header className="debate-room-header">
                    <div className="header-top">
                        <h1 className="room-title">{room.title}</h1>
                        <div className="header-actions">
                            {isCreator && debateStarted && !debateEnded && (
                                <button className="end-debate-btn" onClick={handleEndDebate}>
                                    <RiCheckLine /> 토론 종료하기
                                </button>
                            )}
                            {isCreator && !debateStarted && !debateEnded && (
                                <button className="start-debate-btn" onClick={handleStartDebate}>
                                    <RiPlayFill /> 토론 시작하기
                                </button>
                            )}
                            <button className="leave-debate-btn" onClick={handleLeaveDebate}>
                                <RiLogoutBoxLine /> 토론 나가기
                            </button>
                        </div>
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
                            {debateEnded
                                ? "토론이 종료되었습니다."
                                : roundInfo.selectionActive
                                    ? `발언 신청 라운드 ${roundInfo.selectionRound}`
                                    : !debateStarted
                                        ? "토론을 준비 중입니다..."
                                        : `[라운드 ${roundInfo.currentRound}] ${roundInfo.nextSpeaker?.user_name || '다음 참가자'}님 발언 차례입니다.`}
                        </p>
                    </div>
                    <div className="timer-badge">
                        <RiTimerLine /> {roundInfo.turnIndex + 1}/{roundInfo.turnTotal || 0}
                        {selectionRemaining !== null
                            ? <span className="timer-remaining"> · 신청 {formatRemaining(selectionRemaining)}</span>
                            : turnRemaining !== null
                                ? <span className="timer-remaining"> · {formatRemaining(turnRemaining)}</span>
                                : null}
                    </div>
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
                        {debateEnded ? <span className="not-my-turn">토론이 종료되었습니다.</span>
                            : roundInfo.selectionActive ? <span className="not-my-turn">발언 신청 중입니다.</span>
                                : isMyTurn ? <span className="my-turn"><RiUserVoiceLine /> 내 차례입니다</span>
                                    : debateStarted ? <span className="not-my-turn">다음 차례를 기다리고 있습니다...</span> : null}
                    </div>
                    <div className="input-wrapper">
                        <input
                            type="text"
                            placeholder={debateEnded ? "토론이 종료되었습니다." : !debateStarted ? "토론이 준비중입니다..." : isMyTurn ? "나의 주장을 입력해주세요..." : "발언을 기다리고 있습니다."}
                            value={messageInput}
                            onChange={(e) => setMessageInput(e.target.value)}
                            disabled={!debateStarted || !isMyTurn || debateEnded}
                        />
                        <button type="submit" className="send-btn" disabled={!messageInput.trim() || !isMyTurn || debateEnded}>
                            <RiSendPlaneFill />
                        </button>
                        <button
                            type="button"
                            className="end-turn-btn"
                            onClick={handleEndSpeaking}
                            disabled={!debateStarted || !isMyTurn || debateEnded}
                        >
                            <RiCheckLine /> 발언 종료
                        </button>
                        {roundInfo.selectionActive && canRaiseHand && (
                            <button
                                type="button"
                                className="raise-hand-btn"
                                onClick={handleRaiseHand}
                                disabled={hasRaised}
                            >
                                <RiUserVoiceLine /> 발언 신청
                            </button>
                        )}
                    </div>
                </form>
            </main>
        </div>
    );
}

// 컴포넌트 분리: 메시지 행 (여기서 찢어서 출력 처리)
function MessageRow({ msg, isMe }) {
    if (msg.displayType === 'system') return <div className="system-message"><span>{msg.content}</span></div>;
    
    // ⭐ [신규] 찢어서 출력하기 1: 전체 총평 요약 (display_type: report_summary)
    if (msg.displayType === 'report_summary') return (
        <div className="report-item summary">
            <div className="report-tag"><RiFileTextLine /> 전체 총평</div>
            <div className="report-content">{msg.content}</div>
        </div>
    );

    // ⭐ [신규] 찢어서 출력하기 2: 팀 평가 (display_type: report_pro / report_con)
    // content가 객체(JSON)로 오므로 키 값을 직접 참조함
    if (msg.displayType === 'report_pro' || msg.displayType === 'report_con') {
        const type = msg.displayType === 'report_pro' ? 'pro' : 'con';
        return <TeamResultCard title={type === 'pro' ? '찬성 팀' : '반대 팀'} data={msg.content} type={type} />;
    }

    // ⭐ [신규] 찢어서 출력하기 3: MVP 선정 (display_type: report_mvp)
    if (msg.displayType === 'report_mvp') return (
        <div className="report-item mvp">
            <div className="mvp-announcement">
                <RiMedalLine className="mvp-icon" />
                <span>이번 토론의 MVP는 <strong>{msg.content}</strong>님입니다! 축하드립니다! 🏆</span>
            </div>
        </div>
    );

    // 일반 사회자 메시지
    if (msg.displayType === 'draft') return (
        <div className={`message-row ${msg.role} draft ${isMe ? 'me' : ''}`}>
            {!isMe && (
                <div className="msg-avatar">
                    <img src={`https://api.dicebear.com/9.x/notionists/svg?seed=${msg.nickname}`} alt="p" />
                </div>
            )}
            <div className="msg-content">
                {!isMe && <span className="msg-name">{msg.nickname}</span>}
                <div className={`msg-bubble ${msg.role} draft`}>
                    <span className="draft-label">초안</span>
                    {msg.content}
                </div>
            </div>
        </div>
    );

    if (msg.displayType === 'loading') return (
        <div className="message-row moderator loading">
            <div className="msg-avatar mod"><RiRobot2Line /></div>
            <div className="msg-bubble mod loading">
                {msg.content}
                <span className="loading-dots" aria-hidden="true">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                </span>
            </div>
        </div>
    );

    if (msg.displayType === 'moderator') return (
        <div className="message-row moderator">
            <div className="msg-avatar mod"><RiRobot2Line /></div>
            <div className="msg-bubble mod">{msg.content}</div>
        </div>
    );

    // 일반 사용자 메시지
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

// 팀별 평가 카드 (객체 키-값 접근 핵심)
function TeamResultCard({ title, data, type }) {
    return (
        <div className={`team-result-card ${type}`}>
            <div className="res-header">
                <span className="team-name">{title}</span>
                <span className="total-score">{data.total_score}점</span>
            </div>
            
            {/* 항목별 세부 점수 바 (scores 키 참조) */}
            <div className="score-bars">
                <ScoreBar label="주장 명확성" val={data.scores.clarity} max={25} />
                <ScoreBar label="근거 적합성" val={data.scores.evidence} max={30} />
                <ScoreBar label="상호작용" val={data.scores.interaction} max={25} />
                <ScoreBar label="토론 태도" val={data.scores.attitude} max={20} />
            </div>

            {/* 상세 피드백 (feedback_text 키 참조) */}
            <div className="feedback-body">
                <div className="fb-label"><RiInformationLine /> 상세 평가 이유</div>
                <div className="fb-text">{data.feedback_text}</div>
                {data.fact_check_result && (
                    <div className="fact-check-box">
                        <strong>📌 Fact Check:</strong> {data.fact_check_result}
                    </div>
                )}
            </div>
        </div>
    );
}

// 점수 바 컴포넌트
function ScoreBar({ label, val, max }) {
    const percent = (val / max) * 100;
    return (
        <div className="score-row">
            <span className="label">{label}</span>
            <div className="bar-bg"><div className="bar-fill" style={{width: `${percent}%`}}></div></div>
            <span className="val">{val}</span>
        </div>
    );
}

// 사이드바 팀 섹션
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

export default DebatePage;
