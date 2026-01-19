import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import SearchPanel from "../components/panels/SearchPanel";
import VerdictsPanel from "../components/panels/VerdictsPanel";
import "../styles/HomePage.css";

function HomePage() {
    const { user } = useAuth();
    const [activePanel, setActivePanel] = useState(null);
    const [isMatching, setIsMatching] = useState(false);
    const navigate = useNavigate();
    const [infoTab, setInfoTab] = useState("notice");

    const togglePanel = (panelName) => {
        if (activePanel === panelName) {
            setActivePanel(null);
        } else {
            setActivePanel(panelName);
        }
    };

    const availableDebates = [
        {
            id: "debate-1",
            title: "최저임금 인상, 필요한가?",
            tags: ["경제", "정책"],
            participants: 3,
            capacity: 4,
            start: "3분 후 시작",
            level: "LV.1~3 추천",
        },
        {
            id: "debate-2",
            title: "온라인 익명성은 보장되어야 하는가?",
            tags: ["사회", "윤리"],
            participants: 2,
            capacity: 4,
            start: "바로 시작",
            level: "LV.2~4 추천",
        },
        {
            id: "debate-3",
            title: "플라스틱 규제, 어디까지?",
            tags: ["환경", "정책"],
            participants: 1,
            capacity: 4,
            start: "5분 후 시작",
            level: "LV.1~2 추천",
        },
    ];
    const featuredDebate = availableDebates[0];
    const compactDebates = availableDebates.slice(1);

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
                        {/* TODO: 친구와 방 만들기 기능 연결 */}
                        <button type="button" className="action-btn link" disabled>
                            친구와 방 만들기
                        </button>
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

                    {featuredDebate && (
                        <article className="card debate-card compact featured">
                            <div className="debate-compact-main">
                                <div className="debate-title-row">
                                    <span className="featured-label">Featured</span>
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
                                    {featuredDebate.start === "바로 시작" ? "바로 시작" : "대기 중"}
                                </span>
                                <button type="button" className="action-btn secondary small">
                                    참여하기
                                </button>
                            </div>
                        </article>
                    )}

                    <div className="debate-compact-list">
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
                                        {debate.start === "바로 시작" ? "바로 시작" : "대기 중"}
                                    </span>
                                    <button type="button" className="action-btn secondary small">
                                        참여하기
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>

                <aside className="lobby-right">
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
                                    <div className="verdict-item">
                                        <span>청소년 스마트폰 제한, 필요한가?</span>
                                        <span className="tag-pill">TOP</span>
                                    </div>
                                    <div className="verdict-item">
                                        <span>원격근무 의무화의 장단점</span>
                                    </div>
                                </>
                            )}
                        </div>
                    </section>
                </aside>
            </div>

            <SearchPanel isOpen={activePanel === "search"} onClose={() => setActivePanel(null)} />
            <VerdictsPanel isOpen={activePanel === "verdicts"} onClose={() => setActivePanel(null)} />
        </div>
    );
}

export default HomePage;
