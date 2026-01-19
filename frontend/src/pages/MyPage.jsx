import { useMemo, useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip
} from "recharts";
import "../styles/MyPage.css";
import "../styles/Modal.css";

function MyPage() {
    const { user } = useAuth();
    const [historyRecords, setHistoryRecords] = useState([]);
    const [historyStatus, setHistoryStatus] = useState("idle");
    const [historyError, setHistoryError] = useState("");
    const [replayOpen, setReplayOpen] = useState(false);
    const [replayStatus, setReplayStatus] = useState("idle");
    const [replayError, setReplayError] = useState("");
    const [replayMessages, setReplayMessages] = useState([]);
    const [replayMeta, setReplayMeta] = useState(null);
    const [verdictOpen, setVerdictOpen] = useState(false);
    const [verdictStatus, setVerdictStatus] = useState("idle");
    const [verdictError, setVerdictError] = useState("");
    const [verdictData, setVerdictData] = useState(null);
    const [verdictMeta, setVerdictMeta] = useState(null);

    const mockProfile = useMemo(() => ({
        nickname: user?.nickname || "Guest",
        intro: "꾸준히 성장하는 토론가입니다.",
        level: 1,
        currentXp: 0,
        maxXp: 100,
    }), [user]);

    const stats = [
        { label: "총 토론 수", value: "24회" },
        { label: "승률", value: "58%" },
        { label: "최근 7일 참여", value: "5회" },
    ];

    const activityData = [
        { name: "월", debates: 2 },
        { name: "화", debates: 1 },
        { name: "수", debates: 3 },
        { name: "목", debates: 2 },
        { name: "금", debates: 4 },
        { name: "토", debates: 1 },
        { name: "일", debates: 2 },
    ];

    const recentDebates = [
        { id: 1, title: "플라스틱 규제, 어디까지?", date: "2025.01.12", result: "승리" },
        { id: 2, title: "최저임금 인상, 필요한가?", date: "2025.01.09", result: "패배" },
        { id: 3, title: "온라인 익명성 보장 여부", date: "2025.01.05", result: "승리" },
    ];

    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("access_token");

        if (!token) {
            setHistoryRecords([]);
            setHistoryStatus("idle");
            return () => {
                isMounted = false;
            };
        }

        const formatDate = (value) => {
            if (!value) return "-";
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) return "-";
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const day = String(date.getDate()).padStart(2, "0");
            return `${year}.${month}.${day}`;
        };

        const mapRole = (role) => {
            if (role === "pro") return "찬성";
            if (role === "con") return "반대";
            if (role === "observer") return "관전자";
            return role || "-";
        };

        const mapResult = (result) => {
            if (result === "win") return "승리";
            if (result === "lose") return "패배";
            if (result === "draw") return "무승부";
            return "미정";
        };

        const fetchHistory = async () => {
            setHistoryStatus("loading");
            setHistoryError("");

            try {
                const response = await fetch("http://localhost:8000/api/debates/history", {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Failed to load history");
                }

                const data = await response.json();
                const items = Array.isArray(data) ? data : [];
                const mapped = items.map((item) => ({
                    id: item.debate_room_id ?? item.id,
                    title: item.title || item.topic || "Untitled",
                    date: formatDate(item.finished_at || item.started_at || item.joined_at),
                    role: mapRole(item.role),
                    result: mapResult(item.result),
                }));

                if (isMounted) {
                    setHistoryRecords(mapped);
                    setHistoryStatus("success");
                }
            } catch (error) {
                if (isMounted) {
                    setHistoryRecords([]);
                    setHistoryStatus("error");
                    setHistoryError(error?.message || "Failed to load history");
                }
            }
        };

        fetchHistory();

        return () => {
            isMounted = false;
        };
    }, [user]);

    const badges = [
        { id: 1, name: "첫 토론 완주", earned: true },
        { id: 2, name: "연속 5회 참여", earned: true },
        { id: 3, name: "승률 60% 달성", earned: false },
        { id: 4, name: "피드백 상위 10%", earned: false },
    ];

    const handleOpenReplay = async (record) => {
        const token = localStorage.getItem("access_token");
        if (!token || !record?.id) {
            setReplayError("리플레이를 불러올 수 없습니다.");
            setReplayMessages([]);
            setReplayStatus("error");
            return;
        }

        setReplayOpen(true);
        setReplayMeta(record);
        setReplayStatus("loading");
        setReplayError("");
        setReplayMessages([]);

        try {
            const response = await fetch(`http://localhost:8000/api/debates/${record.id}/messages`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            if (!response.ok) {
                throw new Error("리플레이 불러오기 실패");
            }
            const data = await response.json();
            setReplayMessages(Array.isArray(data) ? data : []);
            setReplayStatus("success");
        } catch (error) {
            setReplayStatus("error");
            setReplayError(error?.message || "리플레이 불러오기 실패");
        }
    };

    const handleCloseReplay = () => {
        setReplayOpen(false);
        setReplayMessages([]);
        setReplayStatus("idle");
        setReplayError("");
        setReplayMeta(null);
    };

    const handleOpenVerdict = async (record) => {
        const token = localStorage.getItem("access_token");
        if (!token || !record?.id) {
            setVerdictError("판결문을 불러올 수 없습니다.");
            setVerdictStatus("error");
            return;
        }

        setVerdictOpen(true);
        setVerdictMeta(record);
        setVerdictStatus("loading");
        setVerdictError("");
        setVerdictData(null);

        try {
            const response = await fetch(`http://localhost:8000/api/debates/${record.id}/verdict`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            if (!response.ok) {
                throw new Error("판결문 불러오기 실패");
            }
            const data = await response.json();
            setVerdictData(data);
            setVerdictStatus("success");
        } catch (error) {
            setVerdictStatus("error");
            setVerdictError(error?.message || "판결문 불러오기 실패");
        }
    };

    const handleCloseVerdict = () => {
        setVerdictOpen(false);
        setVerdictStatus("idle");
        setVerdictError("");
        setVerdictData(null);
        setVerdictMeta(null);
    };

    return (
        <MyPageLayout>
            <StatsOverview stats={stats} />
            <ActivityTabs
                activityData={activityData}
                recentDebates={recentDebates}
                historyRecords={historyRecords}
                historyStatus={historyStatus}
                historyError={historyError}
                onReplay={handleOpenReplay}
                onVerdict={handleOpenVerdict}
                badges={badges}
                nickname={mockProfile.nickname}
            />
            {replayOpen && (
                <ReplayModal
                    record={replayMeta}
                    status={replayStatus}
                    error={replayError}
                    messages={replayMessages}
                    onClose={handleCloseReplay}
                />
            )}
            {verdictOpen && (
                <VerdictModal
                    record={verdictMeta}
                    status={verdictStatus}
                    error={verdictError}
                    verdict={verdictData}
                    onClose={handleCloseVerdict}
                />
            )}
        </MyPageLayout>
    );
}

function MyPageLayout({ children }) {
    return <div className="mypage-container">{children}</div>;
}

function ProfileSummary({ profile }) {
    const xpPercent = Math.round((profile.currentXp / profile.maxXp) * 100);
    const remainingXp = Math.max(0, profile.maxXp - profile.currentXp);

    return (
        <section className="mypage-card profile-summary">
            <div className="profile-main">
                <div className="profile-avatar">
                    <img
                        src={`https://api.dicebear.com/9.x/notionists/svg?seed=${profile.nickname}&backgroundColor=transparent`}
                        alt="Profile"
                    />
                </div>
                <div className="profile-text">
                    <span className="profile-label">프로필</span>
                    <h2>{profile.nickname}</h2>
                    <p>{profile.intro}</p>
                </div>
            </div>
            <div className="profile-progress">
                <div className="profile-level">
                    <span className="mypage-level-chip">LV.{profile.level}</span>
                    <span className="mypage-xp-text">
                        {profile.currentXp} / {profile.maxXp} XP
                    </span>
                </div>
                <div className="mypage-progress-track">
                    <div className="mypage-progress-fill" style={{ width: `${xpPercent}%` }} />
                </div>
                <span className="mypage-xp-remaining">다음 레벨까지 {remainingXp} XP</span>
            </div>
        </section>
    );
}

function StatsOverview({ stats }) {
    return (
        <section className="stats-overview">
            {stats.map((stat) => (
                <div key={stat.label} className="mypage-card stat-card">
                    <span className="stat-label">{stat.label}</span>
                    <strong className="stat-value">{stat.value}</strong>
                </div>
            ))}
        </section>
    );
}

function ActivityTabs({ activityData, recentDebates, historyRecords, historyStatus, historyError, onReplay, onVerdict, badges, nickname }) {
    const [activeTab, setActiveTab] = useState("summary");

    return (
        <section className="mypage-card tabs-card">
            <div className="tabs-header">
                <button
                    type="button"
                    className={`mypage-tab-btn ${activeTab === "summary" ? "active" : ""}`}
                    onClick={() => setActiveTab("summary")}
                >
                    활동 요약
                </button>
                <button
                    type="button"
                    className={`mypage-tab-btn ${activeTab === "history" ? "active" : ""}`}
                    onClick={() => setActiveTab("history")}
                >
                    토론 기록
                </button>
                <button
                    type="button"
                    className={`mypage-tab-btn ${activeTab === "badges" ? "active" : ""}`}
                    onClick={() => setActiveTab("badges")}
                >
                    뱃지 & 업적
                </button>
                <button
                    type="button"
                    className={`mypage-tab-btn ${activeTab === "settings" ? "active" : ""}`}
                    onClick={() => setActiveTab("settings")}
                >
                    설정
                </button>
            </div>

            <div className="tabs-body">
                {activeTab === "summary" && (
                    <ActivitySummaryTab activityData={activityData} recentDebates={recentDebates} />
                )}
                {activeTab === "history" && (
                    <HistoryTab
                        historyRecords={historyRecords}
                        historyStatus={historyStatus}
                        historyError={historyError}
                        onReplay={onReplay}
                        onVerdict={onVerdict}
                    />
                )}
                {activeTab === "badges" && <BadgesTab badges={badges} />}
                {activeTab === "settings" && <SettingsTab nickname={nickname} />}
            </div>
        </section>
    );
}

function ActivitySummaryTab({ activityData, recentDebates }) {
    return (
        <div className="summary-grid">
            <div className="summary-chart">
                <div className="section-title">
                    <h3>최근 활동</h3>
                    <span className="section-desc">최근 7일 참여 추이</span>
                </div>
                {/* TODO: 실제 데이터 바인딩 */}
                <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={activityData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                        <Tooltip />
                        <Line type="monotone" dataKey="debates" stroke="#2563eb" strokeWidth={2} />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            <div className="summary-recent">
                <div className="section-title">
                    <h3>최근 토론</h3>
                    <span className="section-desc">최근 참여한 토론 3개</span>
                </div>
                <div className="recent-list">
                    {recentDebates.map((debate) => (
                        <div key={debate.id} className="recent-card">
                            <div>
                                <strong>{debate.title}</strong>
                                <span>{debate.date}</span>
                            </div>
                            <div className="recent-actions">
                                <span className={`result-pill ${debate.result === "승리" ? "win" : "lose"}`}>
                                    {debate.result}
                                </span>
                                <button type="button" className="mypage-action-btn secondary small">
                                    판결문 보기
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="summary-feedback">
                <div className="section-title">
                    <h3>AI 피드백</h3>
                    <span className="section-desc">최근 토론 요약</span>
                </div>
                <ul>
                    <li>주장의 구조가 명확하고 상대의 논점을 잘 요약했습니다.</li>
                    <li>근거 제시가 조금 더 구체적이면 설득력이 높아집니다.</li>
                    <li>다음 토론에서는 반박 타이밍을 조금 더 빠르게 가져가 보세요.</li>
                </ul>
            </div>
        </div>
    );
}

function HistoryTab({ historyRecords, historyStatus, historyError, onReplay, onVerdict }) {
    return (
        <div className="history-tab">
            <div className="history-filters">
                <select className="filter-select" defaultValue="7d">
                    <option value="7d">최근 7일</option>
                    <option value="30d">최근 30일</option>
                    <option value="all">전체</option>
                </select>
                <select className="filter-select" defaultValue="all">
                    <option value="all">전체 결과</option>
                    <option value="win">승리</option>
                    <option value="lose">패배</option>
                    <option value="draw">무승부</option>
                </select>
            </div>
            <div className="history-list">
                {historyStatus === "loading" && (
                    <div className="history-row history-empty">기록을 불러오는 중...</div>
                )}
                {historyStatus === "error" && (
                    <div className="history-row history-empty">
                        {historyError || "기록을 불러오지 못했습니다."}
                    </div>
                )}
                {historyStatus !== "loading" && historyStatus !== "error" && historyRecords.length === 0 && (
                    <div className="history-row history-empty">아직 기록이 없습니다.</div>
                )}
                {historyRecords.map((record) => (
                    <div key={record.id} className="history-row">
                        <div>
                            <strong>{record.title}</strong>
                            <span>{record.date}</span>
                        </div>
                        <span className="history-meta">{record.role}</span>
                        <span className="history-meta">{record.result}</span>
                        <div className="history-actions">
                            <button
                                type="button"
                                className="mypage-action-btn secondary small"
                                onClick={() => onVerdict?.(record)}
                            >
                                판결문
                            </button>
                            <button
                                type="button"
                                className="mypage-action-btn ghost small"
                                onClick={() => onReplay?.(record)}
                            >
                                리플레이
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function ReplayModal({ record, status, error, messages, onClose }) {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content replay-modal" onClick={(event) => event.stopPropagation()}>
                <button type="button" className="modal-close-btn" onClick={onClose} aria-label="닫기">
                    ×
                </button>
                <div className="replay-header">
                    <h2 className="replay-title">토론 리플레이</h2>
                    <div className="replay-meta">
                        <span>{record?.title || "토론 제목 없음"}</span>
                        <span>{record?.date || "-"}</span>
                        <span>{record?.role || "-"}</span>
                        <span>{record?.result || "-"}</span>
                    </div>
                </div>
                <div className="replay-body">
                    {status === "loading" && <div className="replay-status">리플레이를 불러오는 중...</div>}
                    {status === "error" && <div className="replay-status error">{error || "불러오지 못했습니다."}</div>}
                    {status === "success" && messages.length === 0 && (
                        <div className="replay-status">표시할 메시지가 없습니다.</div>
                    )}
                    {status === "success" && messages.length > 0 && (
                        <div className="replay-list">
                            {messages.map((msg) => (
                                <div key={msg.message_id} className={`replay-message ${msg.role}`}>
                                    <div className="replay-message-head">
                                        <span className="replay-role">{msg.user_name || msg.role}</span>
                                        <span className="replay-time">
                                            {msg.turn ? `Turn ${msg.turn}` : "-"}
                                        </span>
                                    </div>
                                    <div className="replay-content">{msg.content}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function VerdictModal({ record, status, error, verdict, onClose }) {
    const proEval = verdict?.pro_eval || null;
    const conEval = verdict?.con_eval || null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content verdict-modal" onClick={(event) => event.stopPropagation()}>
                <button type="button" className="modal-close-btn" onClick={onClose} aria-label="닫기">
                    ×
                </button>
                <div className="verdict-header">
                    <h2 className="verdict-title">판결문</h2>
                    <div className="verdict-meta">
                        <span>{record?.title || "토론 제목 없음"}</span>
                        <span>{record?.date || "-"}</span>
                        <span>{record?.result || "-"}</span>
                    </div>
                </div>
                <div className="verdict-body">
                    {status === "loading" && <div className="verdict-status">판결문을 불러오는 중...</div>}
                    {status === "error" && <div className="verdict-status error">{error || "불러오지 못했습니다."}</div>}
                    {status === "success" && !verdict && (
                        <div className="verdict-status">판결문 데이터가 없습니다.</div>
                    )}
                    {status === "success" && verdict && (
                        <div className="verdict-content">
                            {verdict.summary && (
                                <div className="verdict-section">
                                    <h3>전체 총평</h3>
                                    <p>{verdict.summary}</p>
                                </div>
                            )}
                            <div className="verdict-scores">
                                <div className="verdict-card pro">
                                    <h4>찬성 팀</h4>
                                    <strong>{proEval?.total_score ?? "-"}점</strong>
                                    {proEval?.feedback_text && <p>{proEval.feedback_text}</p>}
                                </div>
                                <div className="verdict-card con">
                                    <h4>반대 팀</h4>
                                    <strong>{conEval?.total_score ?? "-"}점</strong>
                                    {conEval?.feedback_text && <p>{conEval.feedback_text}</p>}
                                </div>
                            </div>
                            {verdict.best_player && (
                                <div className="verdict-section highlight">
                                    MVP: <strong>{verdict.best_player}</strong>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function BadgesTab({ badges }) {
    return (
        <div className="badges-grid">
            {badges.map((badge) => (
                <div key={badge.id} className={`badge-card ${badge.earned ? "earned" : "locked"}`}>
                    <span className={`badge-icon ${badge.earned ? "earned" : "locked"}`}>
                        {badge.earned ? "OK" : "LOCK"}
                    </span>
                    <strong>{badge.name}</strong>
                    <span>{badge.earned ? "획득 완료" : "미획득"}</span>
                </div>
            ))}
        </div>
    );
}

function SettingsTab({ nickname }) {
    const [nameValue, setNameValue] = useState(nickname);
    const [introValue, setIntroValue] = useState("꾸준히 성장하는 토론가입니다.");

    return (
        <div className="settings-tab">
            <div className="settings-section">
                <h3>프로필 설정</h3>
                <label>
                    닉네임
                    <input
                        type="text"
                        value={nameValue}
                        onChange={(event) => setNameValue(event.target.value)}
                    />
                </label>
                <label>
                    한 줄 소개
                    <input
                        type="text"
                        value={introValue}
                        onChange={(event) => setIntroValue(event.target.value)}
                    />
                </label>
                {/* TODO: 아바타 변경 기능 연결 */}
                <button type="button" className="mypage-action-btn secondary">
                    아바타 변경
                </button>
            </div>

            <div className="settings-section">
                <h3>알림 설정</h3>
                <label className="toggle-row">
                    토론 알림 받기
                    <input type="checkbox" defaultChecked />
                </label>
                <label className="toggle-row">
                    판결문 업데이트 알림
                    <input type="checkbox" />
                </label>
            </div>

            <div className="settings-section">
                <h3>계정/보안</h3>
                {/* TODO: 계정/보안 기능 연결 */}
                <button type="button" className="mypage-action-btn secondary">
                    비밀번호 변경
                </button>
                <button type="button" className="mypage-action-btn ghost">
                    로그아웃
                </button>
            </div>
        </div>
    );
}

export default MyPage;
