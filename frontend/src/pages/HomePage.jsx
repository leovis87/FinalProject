import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { 
    RiMegaphoneLine,      
    RiLightbulbLine,      
    RiArrowRightSLine,
    RiSwordLine,         // 추가: 배틀 아이콘
    RiSearchLine,        // 추가: 검색 아이콘
    RiAddCircleLine      // 추가: 생성 아이콘
} from "react-icons/ri";
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
                const response = await fetch("/api/debates/");
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
                const response = await fetch("/api/debates/verdicts/popular?limit=3", {
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

    const handleCreateRoom = () => {
        navigate('/create');
    };

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
                const response = await fetch("/api/debates/random-match", {
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
        <div className="page-container">
            <section className="quick-access-section">
                
                {/* 상단: 랜덤 토론 배틀 (이미지 디자인 적용) */}
                <div className="banner-card battle-banner">
                    <div className="banner-content">
                        <div className="banner-header">
                            <div className="banner-icon-box">
                                <RiSwordLine />
                            </div>
                            <div className="banner-text">
                                <h2>토론 배틀 시작!</h2>
                                <p className="sub-title">실력을 증명할 시간입니다</p>
                            </div>
                        </div>
                        <p className="banner-desc">
                            배틀에서 승리하고 경험치를 얻으세요.<br />
                            레벨업하고 새로운 배지를 획득하며 토론 마스터가 되어보세요! 🎮
                        </p>
                        
                        {/* 액션 버튼 그룹 */}
                        <div className="banner-actions">
                            <button 
                                className="banner-action-btn primary"
                                onClick={handleRandomMatch}
                                disabled={isMatching}
                            >
                                {isMatching ? "매칭 중..." : "⚔️ 랜덤 토론"}
                            </button>

                            <button 
                                className="banner-action-btn secondary"
                                onClick={() => navigate('/find')}
                            >
                                <RiSearchLine size={18} /> 토론 찾기
                            </button>

                            <button 
                                className="banner-action-btn secondary"
                                onClick={() => navigate('/create')}
                            >
                                <RiAddCircleLine size={18} /> 방 만들기
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            <section className="info-grid-section">
                {/* 왼쪽: 공지사항 카드 */}
                <div className="info-card notice-card">
                    <div className="info-card-header">
                        <div className="header-title">
                            <RiMegaphoneLine className="header-icon notice-icon" />
                            <h3>공지사항</h3>
                        </div>
                        <button className="more-btn">더보기 <RiArrowRightSLine /></button>
                    </div>
                    <ul className="notice-list">
                        <li className="notice-item">
                            <span className="notice-tag new">NEW</span>
                            <span className="notice-text">🔥 이번 주 '베스트 토론왕' 선정 결과 안내</span>
                            <span className="notice-date">10.24</span>
                        </li>
                        <li className="notice-item">
                            <span className="notice-tag">공지</span>
                            <span className="notice-text">서비스 점검 안내 (10/25 02:00 ~ 04:00)</span>
                            <span className="notice-date">10.22</span>
                        </li>
                        <li className="notice-item">
                            <span className="notice-tag">이벤트</span>
                            <span className="notice-text">친구 초대하고 경험치 2배 부스트 받자!</span>
                            <span className="notice-date">10.20</span>
                        </li>
                    </ul>
                </div>

                {/* 오른쪽: 오늘의 토론 팁 */}
                <div className="info-card tip-card">
                    <div className="info-card-header">
                        <div className="header-title">
                            <RiLightbulbLine className="header-icon tip-icon" />
                            <h3>오늘의 토론 팁</h3>
                        </div>
                    </div>
                    <div className="tip-content">
                        <strong className="tip-title">"상대방의 논리를 일부 인정해보세요"</strong>
                        <p className="tip-desc">
                            무조건적인 반박보다는 상대의 타당한 점을 인정한 뒤, 
                            그럼에도 불구하고 내 주장이 왜 더 설득력 있는지 설명하는 것이 
                            청중에게 훨씬 깊은 인상을 남깁니다. (Yes, but 화법)
                        </p>
                        <div className="tip-tag">#설득의기술 #화법 #논리</div>
                    </div>
                </div>

            </section>
        </div>
    );
}

export default HomePage;
