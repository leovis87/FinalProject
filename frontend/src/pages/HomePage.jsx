import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import SearchPanel from "../components/panels/SearchPanel";
import VerdictsPanel from "../components/panels/VerdictsPanel";
import JoinRoomModal from "../components/modals/JoinRoomModal";
import CreateRoomModal from "../components/modals/CreateRoomModal";
import "../styles/HomePage.css";

function HomePage() {
    const { user } = useAuth();
    const [activePanel, setActivePanel] = useState(null);
    const [isMatching, setIsMatching] = useState(false);
    const navigate = useNavigate();
    const [infoTab, setInfoTab] = useState("notice");
    const [debateRooms, setDebateRooms] = useState([]);
    const [isLoadingDebates, setIsLoadingDebates] = useState(false);
    const [debateError, setDebateError] = useState("");
    const [selectedJoinRoom, setSelectedJoinRoom] = useState(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [popularVerdicts, setPopularVerdicts] = useState([]);
    const [isLoadingVerdicts, setIsLoadingVerdicts] = useState(false);
    const [verdictError, setVerdictError] = useState("");

    const togglePanel = (panelName) => {
        if (activePanel === panelName) {
            setActivePanel(null);
        } else {
            setActivePanel(panelName);
        }
    };

    useEffect(() => {
        const fetchDebates = async () => {
            setIsLoadingDebates(true);
            setDebateError("");
            try {
                const response = await fetch("http://localhost:8000/api/debates/");
                if (!response.ok) {
                    throw new Error("토론 목록을 불러오지 못했습니다.");
                }
                const data = await response.json();
                setDebateRooms(Array.isArray(data) ? data : []);
            } catch (error) {
                setDebateError(error instanceof Error ? error.message : "토론 목록 로드 실패");
            } finally {
                setIsLoadingDebates(false);
            }
        };

        fetchDebates();
    }, []);

    useEffect(() => {
        const fetchVerdicts = async () => {
            setIsLoadingVerdicts(true);
            setVerdictError("");
            try {
                const token = localStorage.getItem("access_token");
                const response = await fetch("http://localhost:8000/api/debates/verdicts/popular?limit=3", {
                    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
                });
                if (!response.ok) {
                    throw new Error("인기 판결문을 불러오지 못했습니다.");
                }
                const data = await response.json();
                setPopularVerdicts(Array.isArray(data) ? data : []);
            } catch (error) {
                setVerdictError(error instanceof Error ? error.message : "인기 판결문 로드 실패");
            } finally {
                setIsLoadingVerdicts(false);
            }
        };

        fetchVerdicts();
    }, []);

    const levelLabelMap = {
        all: "제한 없음",
        elementary_low: "초등 (저)",
        elementary_high: "초등 (고)",
        middle: "중등",
        high: "고등",
    };

    const categoryLabelMap = {
        korean: "국어",
        social: "사회",
        moral: "도덕",
        ethics: "윤리",
    };

    const getStartLabel = (status) => {
        if (status === "waiting") return "대기 중";
        if (status && status.startsWith("in_progress")) return "진행 중";
        return "대기 중";
    };

    const eligibleDebates = debateRooms
        .filter((room) => room.status !== "finished")
        .sort((a, b) => {
            const aTime = new Date(a.started_at || a.created_at || 0).getTime();
            const bTime = new Date(b.started_at || b.created_at || 0).getTime();
            return bTime - aTime;
        });

    const availableDebates = eligibleDebates.map((room) => ({
        id: room.debate_room_id,
        title: room.title,
        tags: [
            categoryLabelMap[room.category] || room.category || "기타",
            levelLabelMap[room.level] || room.level || "수준 정보 없음",
        ],
        participants: room.current_users ?? room.participants?.length ?? 0,
        capacity: room.max_users,
        start: getStartLabel(room.status),
        raw: room,
    }));

    const featuredDebate = availableDebates[0];
    const compactDebates = availableDebates.slice(1, 6);

    // TODO: 대기열 상태 연결 시 queuedRoom에 데이터 주입
    const queuedRoom = null;
    const hasQueuedRoom = Boolean(queuedRoom);

    const handleRandomMatch = () => {
        if (isMatching) return;
        const token = localStorage.getItem("access_token");
        if (!token) {
            alert("로그인이 필요합니다.");
            return;
        }

        const runMatch = async () => {
            setIsMatching(true);
            try {
                const response = await fetch("http://localhost:8000/api/debates/random-match", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`,
                    },
                    body: JSON.stringify({}),
                });

                if (!response.ok) {
                    let detail = "랜덤 매칭에 실패했습니다.";
                    try {
                        const payload = await response.json();
                        if (payload?.detail) {
                            detail = payload.detail;
                        }
                    } catch (_) {
                        // ignore json parse errors
                    }
                    throw new Error(detail);
                }

                const data = await response.json();
                if (!data?.room_id) {
                    throw new Error("매칭 결과를 확인할 수 없습니다.");
                }

                navigate(`/debate/room/${data.room_id}`);
            } catch (err) {
                alert(err instanceof Error ? err.message : "랜덤 매칭에 실패했습니다.");
            } finally {
                setIsMatching(false);
            }
        };

        runMatch();
    };

    const handleJoinClick = (room) => {
        const isParticipant = room.participants?.some((participant) => participant.user_id === user?.user_id);
        if (isParticipant) {
            navigate(`/debate/room/${room.debate_room_id}`);
            return;
        }
        setSelectedJoinRoom(room);
    };

    return (
        <div className="home-container">
            <div className="lobby-grid">
                <aside className="lobby-left">
                    <section className="card quick-start-card">
                        <div className="card-title-row">
                            <h3>빠른 시작</h3>
                            <p>지금 바로 토론을 시작해보세요.</p>
                        </div>
                        <button type="button" className="action-btn primary" onClick={handleRandomMatch} disabled={isMatching}>
                            {isMatching ? "매칭 중..." : "랜덤 토론 시작"}
                        </button>
                        <button type="button" className="action-btn secondary" onClick={() => togglePanel("search")}>
                            토론 찾기
                        </button>
                        <button
                            type="button"
                            className="action-btn secondary"
                            onClick={() => setIsCreateModalOpen(true)}
                        >
                            토론방 만들기
                        </button>
                    </section>

                    <section className="card info-card">
                        <div className="tab-header">
                            <button
                                type="button"
                                className={`tab-btn ${infoTab === "notice" ? "active" : ""}`}
                                onClick={() => setInfoTab("notice")}
                            >
                                공지사항
                            </button>
                            <button
                                type="button"
                                className={`tab-btn ${infoTab === "tips" ? "active" : ""}`}
                                onClick={() => setInfoTab("tips")}
                            >
                                오늘의 토론 팁
                            </button>
                            <button
                                type="button"
                                className={`tab-btn ${infoTab === "verdicts" ? "active" : ""}`}
                                onClick={() => setInfoTab("verdicts")}
                            >
                                인기 판결문
                            </button>
                        </div>

                        <div className="tab-content">
                            {infoTab === "notice" && (
                                <>
                                    <div className="card-title-row split">
                                        <h3>공지사항</h3>
                                        <button type="button" className="text-link">
                                            자세히 보기
                                        </button>
                                    </div>
                                    <div className="notice-item">
                                        <strong className="notice-title">랜덤 매칭 오픈 안내</strong>
                                        <p className="notice-desc">간단한 매칭으로 빠르게 토론에 참여해보세요.</p>
                                    </div>
                                    <div className="notice-item">
                                        <strong className="notice-title">신규 토론 룰북 업데이트</strong>
                                        <p className="notice-desc">발언 시간과 판정 기준을 확인해 주세요.</p>
                                    </div>
                                </>
                            )}

                            {infoTab === "tips" && (
                                <>
                                    <div className="card-title-row">
                                        <h3>오늘의 토론 팁</h3>
                                    </div>
                                    <ul className="tip-list">
                                        <li>주장은 한 문장으로 요약하고 근거를 붙이세요.</li>
                                        <li>상대 주장의 핵심을 먼저 요약하면 설득력이 높아집니다.</li>
                                        <li>사례나 통계로 주장 신뢰도를 높이세요.</li>
                                    </ul>
                                </>
                            )}

                            {infoTab === "verdicts" && (
                                <>
                                    <div className="card-title-row split">
                                        <h3>인기 판결문</h3>
                                        <button
                                            type="button"
                                            className="text-link"
                                            onClick={() => togglePanel("verdicts")}
                                        >
                                            더보기
                                        </button>
                                    </div>
                                    {isLoadingVerdicts && (
                                        <div className="verdict-item">
                                            <span>불러오는 중...</span>
                                        </div>
                                    )}
                                    {!isLoadingVerdicts && verdictError && (
                                        <div className="verdict-item">
                                            <span>{verdictError}</span>
                                        </div>
                                    )}
                                    {!isLoadingVerdicts && !verdictError && popularVerdicts.length === 0 && (
                                        <div className="verdict-item">
                                            <span>표시할 판결문이 없습니다.</span>
                                        </div>
                                    )}
                                    {!isLoadingVerdicts && !verdictError && popularVerdicts.map((item, index) => (
                                        <div
                                            key={item.debate_room_id}
                                            className="verdict-item clickable"
                                            role="button"
                                            tabIndex={0}
                                            onClick={() => togglePanel("verdicts")}
                                            onKeyDown={(event) => {
                                                if (event.key === "Enter" || event.key === " ") {
                                                    event.preventDefault();
                                                    togglePanel("verdicts");
                                                }
                                            }}
                                        >
                                            <span>{item.title}</span>
                                            <span className="tag-pill">{index === 0 ? "TOP" : "HOT"}</span>
                                        </div>
                                    ))}
                                </>
                            )}
                        </div>
                    </section>
                </aside>

                <section className="lobby-center">
                    <div className="section-header">
                        <div>
                            <h2>지금 참여 가능한 토론</h2>
                            <p className="section-desc">대기 중인 방에 참여하거나 직접 만들어보세요.</p>
                        </div>
                    </div>

                    {hasQueuedRoom && (
                        <div className="card queue-card">
                            <div>
                                <span className="queue-label">대기 중인 방</span>
                                <h3 className="queue-title">{queuedRoom.title}</h3>
                                <p className="queue-meta">
                                    시작까지 {queuedRoom.startIn} · {queuedRoom.participants}/{queuedRoom.capacity}명
                                </p>
                            </div>
                            <div className="queue-actions">
                                <button type="button" className="action-btn secondary small">
                                    입장하기
                                </button>
                                <button type="button" className="action-btn ghost small">
                                    대기 취소
                                </button>
                            </div>
                        </div>
                    )}

                    {isLoadingDebates && (
                        <div className="card debate-card compact">
                            <div className="debate-compact-main">
                                <h4 className="debate-title">불러오는 중...</h4>
                                <p className="section-desc">참여 가능한 토론을 준비하고 있어요.</p>
                            </div>
                        </div>
                    )}

                    {!isLoadingDebates && debateError && (
                        <div className="card debate-card compact">
                            <div className="debate-compact-main">
                                <h4 className="debate-title">목록을 불러오지 못했습니다.</h4>
                                <p className="section-desc">{debateError}</p>
                            </div>
                        </div>
                    )}

                    {!isLoadingDebates && !debateError && featuredDebate && (
                        <article className="card debate-card compact featured">
                            <div className="debate-compact-main">
                                <div className="debate-title-row">
                                    <span className="featured-label">추천</span>
                                    <h3 className="debate-title">{featuredDebate.title}</h3>
                                </div>
                                <div className="tag-row">
                                    {featuredDebate.tags.slice(0, 2).map((tag) => (
                                        <span key={`${featuredDebate.id}-${tag}`} className="tag-pill">
                                            #{tag}
                                        </span>
                                    ))}
                                </div>
                                <div className="debate-meta compact">
                                    <span className="meta-item">
                                        참여 {featuredDebate.participants}/{featuredDebate.capacity}명
                                    </span>
                                    <span className="meta-item">{featuredDebate.start}</span>
                                </div>
                            </div>
                            <div className="debate-compact-actions">
                                <span className="status-pill subtle">
                                    {featuredDebate.start === "진행 중" ? "진행 중" : "대기 중"}
                                </span>
                                <button
                                    type="button"
                                    className="action-btn secondary small"
                                    onClick={() => handleJoinClick(featuredDebate.raw)}
                                >
                                    참여하기
                                </button>
                            </div>
                        </article>
                    )}

                    <div className="debate-compact-list">
                        {!isLoadingDebates && !debateError && availableDebates.length === 0 && (
                            <div className="card debate-card compact">
                                <div className="debate-compact-main">
                                    <h4 className="debate-title">참여 가능한 토론이 없습니다.</h4>
                                    <p className="section-desc">새로운 토론방을 만들어보세요.</p>
                                </div>
                            </div>
                        )}

                        {compactDebates.map((debate) => (
                            <article key={debate.id} className="card debate-card compact">
                                <div className="debate-compact-main">
                                    <div>
                                        <h4 className="debate-title">{debate.title}</h4>
                                        <div className="tag-row">
                                            {debate.tags.slice(0, 2).map((tag) => (
                                                <span key={`${debate.id}-${tag}`} className="tag-pill">
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="debate-meta compact">
                                        <span className="meta-item">
                                            참여 {debate.participants}/{debate.capacity}명
                                        </span>
                                        <span className="meta-item">{debate.start}</span>
                                    </div>
                                </div>
                                <div className="debate-compact-actions">
                                    <span className="status-pill subtle">
                                        {debate.start === "진행 중" ? "진행 중" : "대기 중"}
                                    </span>
                                    <button
                                        type="button"
                                        className="action-btn secondary small"
                                        onClick={() => handleJoinClick(debate.raw)}
                                    >
                                        참여하기
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>

            </div>

            <SearchPanel isOpen={activePanel === "search"} onClose={() => setActivePanel(null)} />
            <VerdictsPanel isOpen={activePanel === "verdicts"} onClose={() => setActivePanel(null)} />
            {selectedJoinRoom && (
                <JoinRoomModal room={selectedJoinRoom} onClose={() => setSelectedJoinRoom(null)} />
            )}
            {isCreateModalOpen && (
                <CreateRoomModal onClose={() => setIsCreateModalOpen(false)} />
            )}
        </div>
    );
}

export default HomePage;
