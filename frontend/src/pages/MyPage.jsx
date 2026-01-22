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
import "../styles/Modal.css";
import "../styles/MyPage.css";

// 티어별 다음 단계까지 필요한 목표 점수 설정
const nextTierMap = {
    "옹알이": 100,
    "입문자": 300,
    "아마추어": 600,
    "프로": 1000,
    "마스터": 2000 // 마스터는 만점 혹은 고정값
};

const BADGE_CONFIG = [
    {
        type: "SEED",
        name: "씨앗 토론가",
        description: "신규 가입 시 부여",
        icon: "🌱"
    },
    {
        type: "SPROUT",
        name: "새싹 토론가",
        description: "첫 토론 참여 완료",
        icon: "🌿"
    },
    {
        type: "BLOOMING",
        name: "피어나는 토론가",
        description: "토론 참여 20회 달성",
        icon: "🌸"
    },
    {
        type: "PASSIONATE",
        name: "열혈 토론가",
        description: "토론 참여 100회 달성",
        icon: "🔥"
    },
    {
        type: "POPULAR",
        name: "인기 토론가",
        description: "좋아요 30개 이상 획득",
        icon: "💖"
    },
    {
        type: "KING",
        name: "토론왕",
        description: "최근 20판 승률 70% 이상",
        icon: "👑"
    }
];

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
    const [personalStatus, setPersonalStatus] = useState("idle");
    const [personalError, setPersonalError] = useState("");
    const [personalFeedbacks, setPersonalFeedbacks] = useState([]);
    const [personalQuery, setPersonalQuery] = useState("");
    const [personalOpen, setPersonalOpen] = useState(false);
    const [personalTarget, setPersonalTarget] = useState(null);

    const myBadges = useMemo(() => {
        const userBadges = user?.badges || [];
        
        return BADGE_CONFIG.map((config) => {
            const earnedBadge = userBadges.find((b) => b.name === config.name);
            
            return {
                ...config,
                earned: !!earnedBadge,
                acquired_at: earnedBadge ? earnedBadge.acquired_at : null
            };
        });
    }, [user]);

    const activityData = useMemo(() => {
        const weekLabels = ["일", "월", "화", "수", "목", "금", "토"];
        const counts = Array.from({ length: 7 }, (_, idx) => ({ name: weekLabels[idx], debates: 0 }));
        const now = new Date();
        const start = new Date(now);
        start.setDate(start.getDate() - 6);
        start.setHours(0, 0, 0, 0);

        historyRecords.forEach((record) => {
            if (!record.rawDate) return;
            const date = new Date(record.rawDate);
            if (Number.isNaN(date.getTime())) return;
            if (date < start || date > now) return;
            const dayIndex = date.getDay();
            counts[dayIndex].debates += 1;
        });

        return counts;
    }, [historyRecords]);

    const stats = useMemo(() => {
        const total = historyRecords.length;
        const wins = historyRecords.filter((record) => record.result === "승리").length;
        const winRate = total ? Math.round((wins / total) * 100) : 0;
        const recentCount = activityData.reduce((sum, item) => sum + item.debates, 0);
        return [
            { label: "총 토론 수", value: `${total}회` },
            { label: "승률", value: `${winRate}%` },
            { label: "최근 7일 참여", value: `${recentCount}회` },
        ];
    }, [activityData, historyRecords]);

    const recentDebates = useMemo(() => {
        if (!historyRecords.length) return [];
        return historyRecords.slice(0, 3).map((record) => ({
            id: record.id,
            title: record.title,
            date: record.date,
            result: record.result,
        }));
    }, [historyRecords]);

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
                const response = await fetch("http://61.40.108.149:8000/api/debates/history", {
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
                    rawDate: item.finished_at || item.started_at || item.joined_at,
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

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (!token || historyRecords.length === 0) {
            setPersonalStatus("idle");
            setPersonalFeedbacks([]);
            return;
        }

        let isMounted = true;

        const parseReportPayload = (content) => {
            if (!content) return null;
            if (typeof content === "object") return content;
            if (typeof content !== "string") return null;
            try {
                return JSON.parse(content);
            } catch (error) {
                return { rawText: content };
            }
        };

        const fetchPersonalFeedbacks = async () => {
            setPersonalStatus("loading");
            setPersonalError("");
            try {
                const results = await Promise.all(historyRecords.map(async (record) => {
                    const response = await fetch(`http://61.40.108.149:8000/api/debates/${record.id}/messages`, {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    });
                    if (!response.ok) {
                        return [];
                    }
                    const data = await response.json();
                    const messages = Array.isArray(data) ? data : [];
                    return messages
                        .filter((msg) => msg.display_type === "report_user")
                        .map((msg) => ({
                            id: msg.message_id ?? `${record.id}-${msg.turn || "report"}`,
                            debateId: record.id,
                            title: record.title,
                            date: record.date,
                            rawDate: record.rawDate,
                            role: record.role,
                            result: record.result,
                            createdAt: msg.created_at,
                            report: parseReportPayload(msg.content),
                        }));
                }));

                if (isMounted) {
                    const flattened = results.flat();
                    const sorted = flattened.sort((a, b) => {
                        const timeA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
                        const timeB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
                        return timeB - timeA;
                    });
                    setPersonalFeedbacks(sorted);
                    setPersonalStatus("success");
                }
            } catch (error) {
                if (isMounted) {
                    setPersonalFeedbacks([]);
                    setPersonalStatus("error");
                    setPersonalError(error?.message || "개인 피드백을 불러오지 못했습니다.");
                }
            }
        };

        fetchPersonalFeedbacks();

        return () => {
            isMounted = false;
        };
    }, [historyRecords]);

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
            const response = await fetch(`http://61.40.108.149:8000/api/debates/${record.id}/messages`, {
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
            const response = await fetch(`http://61.40.108.149:8000/api/debates/${record.id}/verdict`, {
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

    // MyPage 컴포넌트 하단
return (
        <MyPageLayout>
            {/* 1. 중복된 ProfileSummary 삭제 */}
            
            {/* 2. 바로 통계 요약부터 시작 */}
            <StatsOverview stats={stats} />
            
            <ActivityTabs
                activityData={activityData}
                recentDebates={recentDebates}
                historyRecords={historyRecords}
                historyStatus={historyStatus}
                historyError={historyError}
                onReplay={handleOpenReplay}
                onVerdict={handleOpenVerdict}
                personalFeedbacks={personalFeedbacks}
                personalStatus={personalStatus}
                personalError={personalError}
                personalQuery={personalQuery}
                onPersonalQueryChange={setPersonalQuery}
                onOpenPersonal={(item) => {
                    setPersonalTarget(item);
                    setPersonalOpen(true);
                }}
                badges={myBadges}
                nickname={user?.nickname || user?.name}
            />

        {/* 모달 로직들 */}
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
        {personalOpen && (
            <PersonalFeedbackModal
                item={personalTarget}
                onClose={() => {
                    setPersonalOpen(false);
                    setPersonalTarget(null);
                }}
            />
        )}
    </MyPageLayout>
);
}
function MyPageLayout({ children }) {
    return <div className="mypage-container">{children}</div>;
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

function ActivityTabs({
    activityData,
    recentDebates,
    historyRecords,
    historyStatus,
    historyError,
    onReplay,
    onVerdict,
    personalFeedbacks,
    personalStatus,
    personalError,
    personalQuery,
    onPersonalQueryChange,
    onOpenPersonal,
    badges,
    nickname
}) {
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
                    <ActivitySummaryTab
                        activityData={activityData}
                        recentDebates={recentDebates}
                        onVerdict={onVerdict}
                        personalFeedbacks={personalFeedbacks}
                        personalStatus={personalStatus}
                        personalError={personalError}
                        personalQuery={personalQuery}
                        onPersonalQueryChange={onPersonalQueryChange}
                        onOpenPersonal={onOpenPersonal}
                    />
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

function ActivitySummaryTab({
    activityData,
    recentDebates,
    onVerdict,
    personalFeedbacks,
    personalStatus,
    personalError,
    personalQuery,
    onPersonalQueryChange,
    onOpenPersonal
}) {
    const buildSummaryText = (report) => {
        if (!report) return "피드백 요약이 없습니다.";
        if (Array.isArray(report.strength) && report.strength.length > 0) {
            return `강점: ${report.strength[0]}`;
        }
        if (Array.isArray(report.weakness) && report.weakness.length > 0) {
            return `개선: ${report.weakness[0]}`;
        }
        if (report.recommended_reading) {
            return `추천: ${report.recommended_reading}`;
        }
        if (report.rawText) {
            return report.rawText;
        }
        return "피드백 요약이 없습니다.";
    };

    const buildSearchText = (item) => {
        const report = item?.report || {};
        const parts = [
            item?.title,
            item?.date,
            item?.role,
            item?.result,
            ...(Array.isArray(report.strength) ? report.strength : []),
            ...(Array.isArray(report.weakness) ? report.weakness : []),
            report.recommended_reading,
            report.rawText,
        ];

        if (Array.isArray(report.detailed_points)) {
            report.detailed_points.forEach((point) => {
                parts.push(point?.original_text);
                parts.push(point?.critique);
                parts.push(point?.suggestion);
            });
        }

        return parts.filter(Boolean).join(" ").toLowerCase();
    };

    const filteredPersonalFeedbacks = useMemo(() => {
        if (!personalQuery) return personalFeedbacks;
        const query = personalQuery.toLowerCase();
        return personalFeedbacks.filter((item) => buildSearchText(item).includes(query));
    }, [personalFeedbacks, personalQuery]);

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
                                <span
                                    className={`result-pill ${
                                        debate.result === "승리"
                                            ? "win"
                                            : debate.result === "패배"
                                                ? "lose"
                                                : debate.result === "무승부"
                                                    ? "draw"
                                                    : "pending"
                                    }`}
                                >
                                    {debate.result}
                                </span>
                                <button
                                    type="button"
                                    className="mypage-action-btn secondary small"
                                    onClick={() => onVerdict?.(debate)}
                                >
                                    판결문 보기
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="summary-feedback personal-feedback">
                <div className="section-title personal-feedback-header">
                    <div>
                        <h3>개인 피드백</h3>
                        <span className="section-desc">토론별 개인 코칭 리포트</span>
                    </div>
                    <div className="personal-feedback-search">
                        <input
                            type="text"
                            placeholder="피드백 검색"
                            value={personalQuery}
                            onChange={(event) => onPersonalQueryChange?.(event.target.value)}
                        />
                    </div>
                </div>
                {personalStatus === "loading" && (
                    <div className="summary-feedback-state">개인 피드백을 불러오는 중...</div>
                )}
                {personalStatus === "error" && (
                    <div className="summary-feedback-state error">{personalError}</div>
                )}
                {personalStatus !== "loading" && personalStatus !== "error" && filteredPersonalFeedbacks.length === 0 && (
                    <div className="summary-feedback-state">표시할 개인 피드백이 없습니다.</div>
                )}
                {personalStatus === "success" && filteredPersonalFeedbacks.length > 0 && (
                    <div className="personal-feedback-list">
                        {filteredPersonalFeedbacks.map((item) => (
                            <button
                                key={item.id}
                                type="button"
                                className="personal-feedback-item"
                                onClick={() => onOpenPersonal?.(item)}
                            >
                                <div className="personal-feedback-main">
                                    <strong>{item.title}</strong>
                                    <span className="personal-feedback-snippet">
                                        {buildSummaryText(item.report)}
                                    </span>
                                </div>
                                <div className="personal-feedback-meta">
                                    <span>{item.date || "-"}</span>
                                    <div className="personal-feedback-badges">
                                        <span className={`feedback-badge role ${item.role === "찬성" ? "pro" : item.role === "반대" ? "con" : "observer"}`}>
                                            {item.role || "-"}
                                        </span>
                                        <span className={`feedback-badge result ${
                                            item.result === "승리"
                                                ? "win"
                                                : item.result === "패배"
                                                    ? "lose"
                                                    : item.result === "무승부"
                                                        ? "draw"
                                                        : "pending"
                                        }`}>
                                            {item.result || "-"}
                                        </span>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function HistoryTab({ historyRecords, historyStatus, historyError, onReplay, onVerdict }) {
    const [rangeFilter, setRangeFilter] = useState("7d");
    const [resultFilter, setResultFilter] = useState("all");

    const filteredRecords = useMemo(() => {
        const now = new Date();
        const start = new Date(now);
        if (rangeFilter === "7d") {
            start.setDate(start.getDate() - 6);
        } else if (rangeFilter === "30d") {
            start.setDate(start.getDate() - 29);
        }
        start.setHours(0, 0, 0, 0);

        return historyRecords.filter((record) => {
            if (rangeFilter !== "all") {
                if (!record.rawDate) return false;
                const date = new Date(record.rawDate);
                if (Number.isNaN(date.getTime())) return false;
                if (date < start || date > now) return false;
            }

            if (resultFilter !== "all") {
                if (resultFilter === "win" && record.result !== "승리") return false;
                if (resultFilter === "lose" && record.result !== "패배") return false;
                if (resultFilter === "draw" && record.result !== "무승부") return false;
            }

            return true;
        });
    }, [historyRecords, rangeFilter, resultFilter]);

    return (
        <div className="history-tab">
            <div className="history-filters">
                <select
                    className="filter-select"
                    value={rangeFilter}
                    onChange={(event) => setRangeFilter(event.target.value)}
                >
                    <option value="7d">최근 7일</option>
                    <option value="30d">최근 30일</option>
                    <option value="all">전체</option>
                </select>
                <select
                    className="filter-select"
                    value={resultFilter}
                    onChange={(event) => setResultFilter(event.target.value)}
                >
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
                {historyStatus !== "loading" && historyStatus !== "error" && filteredRecords.length === 0 && (
                    <div className="history-row history-empty">아직 기록이 없습니다.</div>
                )}
                {filteredRecords.map((record) => (
                    <div key={record.id} className="history-row">
                        <div>
                            <strong>{record.title}</strong>
                            <span>{record.date}</span>
                        </div>
                        <div className="history-meta">
                            <span className={`feedback-badge role ${record.role === "찬성" ? "pro" : record.role === "반대" ? "con" : "observer"}`}>
                                {record.role}
                            </span>
                        </div>
                        <div className="history-meta">
                            <span className={`feedback-badge result ${
                                record.result === "승리"
                                    ? "win"
                                    : record.result === "패배"
                                        ? "lose"
                                        : record.result === "무승부"
                                            ? "draw"
                                            : "pending"
                            }`}>
                                {record.result}
                            </span>
                        </div>
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
    const parseFeedback = (text) => {
        if (!text) return [];
        return text
            .split("###")
            .map((part) => part.trim())
            .filter(Boolean)
            .map((part) => {
                const match = part.match(/\[(.+?)\]\s*\((\d+)점\)\s*-\s*(.*)/s);
                if (match) {
                    return {
                        title: match[1],
                        score: match[2],
                        body: match[3].trim(),
                    };
                }
                return {
                    title: "추가 정보",
                    score: null,
                    body: part,
                };
            });
    };
    const scoreItems = (scores) => {
        if (!scores) return [];
        return [
            { label: "주장 명확성", value: scores.clarity },
            { label: "근거 적합성", value: scores.evidence },
            { label: "상호작용", value: scores.interaction },
            { label: "태도", value: scores.attitude },
        ].filter((item) => item.value !== undefined && item.value !== null);
    };
    const parseAiEvaluation = (content) => {
        if (typeof content !== "string") return null;
        try {
            const data = JSON.parse(content);
            if (!data || typeof data !== "object") return null;
            if (!("total_score" in data) || !("feedback_text" in data)) return null;
            return data;
        } catch (error) {
            return null;
        }
    };
    const parseSummaryPayload = (content) => {
        if (typeof content !== "string") return null;
        try {
            const data = JSON.parse(content);
            if (!data || typeof data !== "object") return null;
            if (data.title && (data.summary || data.pro_items || data.con_items)) {
                return data;
            }
            if (data.round && data.pro_items && data.con_items) {
                return data;
            }
        } catch (error) {
            return null;
        }
        return null;
    };
    const parseItemsPayload = (content) => {
        if (typeof content !== "string") return null;
        try {
            const data = JSON.parse(content);
            if (!data || typeof data !== "object") return null;
            if (data.title && Array.isArray(data.items)) {
                return data;
            }
        } catch (error) {
            return null;
        }
        return null;
    };

    const hasPersonalKeys = (data) => {
        if (!data || typeof data !== "object") return false;
        return (
            "strength" in data ||
            "weakness" in data ||
            "detailed_points" in data ||
            "recommended_reading" in data ||
            "message" in data
        );
    };

    const parsePersonalPayload = (msg) => {
        if (!msg) return null;
        const raw = msg.content;
        const isPersonalType = msg.display_type === "report_user";
        if (raw && typeof raw === "object") {
            if (isPersonalType || hasPersonalKeys(raw)) return raw;
            return null;
        }
        if (typeof raw === "string") {
            try {
                const data = JSON.parse(raw);
                if (!data || typeof data !== "object") return null;
                if (isPersonalType || hasPersonalKeys(data)) return data;
            } catch (_) {
                if (isPersonalType) return { rawText: raw };
                return null;
            }
        }
        return null;
    };

    const renderSummaryCard = (data) => {
        if (!data) return null;
        const proItems = Array.isArray(data.pro_items) ? data.pro_items : [];
        const conItems = Array.isArray(data.con_items) ? data.con_items : [];

        return (
            <div className="replay-message replay-summary">
                <div className="replay-message-head">
                    <span className="replay-role">AI 요약</span>
                    <span className="replay-time">{data.round ? `Turn ${data.round}` : "-"}</span>
                </div>
                <div className="replay-summary-card">
                    <div className="replay-summary-title">{data.title || "요약"}</div>
                    {data.summary && <div className="replay-summary-text">{data.summary}</div>}
                    <div className="replay-summary-grid">
                        <div className="replay-summary-col pro">
                            <div className="replay-summary-col-title">찬성측 입장 요약</div>
                            {proItems.length === 0 ? (
                                <div className="replay-summary-empty">내용 없음</div>
                            ) : (
                                <ul>
                                    {proItems.map((item, index) => (
                                        <li key={`replay-pro-${index}`}>{item}</li>
                                    ))}
                                </ul>
                            )}
                        </div>
                        <div className="replay-summary-col con">
                            <div className="replay-summary-col-title">반대측 입장 요약</div>
                            {conItems.length === 0 ? (
                                <div className="replay-summary-empty">내용 없음</div>
                            ) : (
                                <ul>
                                    {conItems.map((item, index) => (
                                        <li key={`replay-con-${index}`}>{item}</li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const renderPersonalFeedbackCard = (data, msg) => {
        if (!data) return null;
        const strengths = Array.isArray(data.strength) ? data.strength : [];
        const weaknesses = Array.isArray(data.weakness) ? data.weakness : [];
        const details = Array.isArray(data.detailed_points) ? data.detailed_points : [];

        return (
            <div className="replay-message replay-personal">
                <div className="replay-message-head">
                    <span className="replay-role">개인 피드백</span>
                    <span className="replay-time">{msg?.turn ? `Turn ${msg.turn}` : "-"}</span>
                </div>
                <div className="replay-personal-card">
                    {data.message && <p className="replay-personal-text">{data.message}</p>}
                    {!data.message && (
                        <>
                            <div className="personal-feedback-section">
                                <h3>강점</h3>
                                {strengths.length > 0 ? (
                                    <ul>
                                        {strengths.map((item, index) => (
                                            <li key={`replay-strength-${index}`}>{item}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p>강점 정보가 없습니다.</p>
                                )}
                            </div>
                            <div className="personal-feedback-section">
                                <h3>개선 포인트</h3>
                                {weaknesses.length > 0 ? (
                                    <ul>
                                        {weaknesses.map((item, index) => (
                                            <li key={`replay-weakness-${index}`}>{item}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p>개선 포인트가 없습니다.</p>
                                )}
                            </div>
                            <div className="personal-feedback-section">
                                <h3>세부 코칭</h3>
                                {details.length > 0 ? (
                                    <div className="personal-feedback-detail-list">
                                        {details.map((detail, index) => (
                                            <div key={`replay-detail-${index}`} className="personal-feedback-detail">
                                                <div className="personal-feedback-detail-head">
                                                    <strong>Turn {detail.turn ?? "-"}</strong>
                                                    <span>{detail.original_text || "발언 기록 없음"}</span>
                                                </div>
                                                {detail.critique && (
                                                    <p className="personal-feedback-detail-text">
                                                        피드백: {detail.critique}
                                                    </p>
                                                )}
                                                {detail.suggestion && (
                                                    <p className="personal-feedback-detail-text">
                                                        제안: {detail.suggestion}
                                                    </p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p>세부 코칭이 없습니다.</p>
                                )}
                            </div>
                            {data.recommended_reading && (
                                <div className="personal-feedback-section highlight">
                                    추천 학습: <strong>{data.recommended_reading}</strong>
                                </div>
                            )}
                            {data.rawText && (
                                <div className="personal-feedback-section">
                                    <h3>원문</h3>
                                    <p>{data.rawText}</p>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        );
    };

    const normalizeMessages = (list) => {
        const output = [];
        let topicIndex = -1;
        for (const msg of list) {
            const summaryPayload = parseSummaryPayload(msg.content);
            if (summaryPayload) {
                topicIndex = output.length;
                output.push({ ...msg });
                continue;
            }
            const payload = parseItemsPayload(msg.content);
            if (!payload) {
                output.push({ ...msg });
                continue;
            }

            const title = payload.title || "";
            const isPro = title.includes("찬성");
            const isCon = title.includes("반대");
            if (!isPro && !isCon) {
                output.push(msg);
                continue;
            }

            if (topicIndex >= 0) {
                const existing = output[topicIndex];
                const existingPayload = parseSummaryPayload(existing.content) || {};
                const merged = {
                    title: existingPayload.title || "토론 주제 요약",
                    summary: existingPayload.summary || "",
                    pro_items: Array.isArray(existingPayload.pro_items) ? existingPayload.pro_items : [],
                    con_items: Array.isArray(existingPayload.con_items) ? existingPayload.con_items : [],
                };
                if (isPro) merged.pro_items = payload.items;
                if (isCon) merged.con_items = payload.items;
                existing.content = JSON.stringify(merged);
                continue;
            }

            const existing = output.find((entry) => entry.__summaryBucket);
            if (existing) {
                if (isPro) existing.__summaryBucket.pro_items = payload.items;
                if (isCon) existing.__summaryBucket.con_items = payload.items;
                existing.content = JSON.stringify({
                    title: "토론 주제 요약",
                    pro_items: existing.__summaryBucket.pro_items,
                    con_items: existing.__summaryBucket.con_items,
                });
                continue;
            }

            output.push({
                ...msg,
                content: JSON.stringify({
                    title: "토론 주제 요약",
                    pro_items: isPro ? payload.items : [],
                    con_items: isCon ? payload.items : [],
                }),
                __summaryBucket: {
                    pro_items: isPro ? payload.items : [],
                    con_items: isCon ? payload.items : [],
                },
            });
        }
        return output;
    };

    const normalizedMessages = useMemo(() => normalizeMessages(messages), [messages]);

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
                    {status === "success" && normalizedMessages.length === 0 && (
                        <div className="replay-status">표시할 메시지가 없습니다.</div>
                    )}
                    {status === "success" && normalizedMessages.length > 0 && (
                        <div className="replay-list">
                            {normalizedMessages.map((msg) => {
                                const aiEval = parseAiEvaluation(msg.content);
                                if (aiEval) {
                                    const feedbackItems = parseFeedback(aiEval.feedback_text || "");
                                    return (
                                        <div key={msg.message_id} className="replay-message replay-eval">
                                            <div className="replay-message-head">
                                                <span className="replay-role">AI 평가</span>
                                                <span className="replay-time">
                                                    {msg.turn ? `Turn ${msg.turn}` : "-"}
                                                </span>
                                            </div>
                                            <div className="replay-eval-summary">
                                                <strong>{aiEval.total_score}점</strong>
                                                {scoreItems(aiEval.scores).length > 0 && (
                                                    <div className="replay-eval-scores">
                                                        {scoreItems(aiEval.scores).map((item) => (
                                                            <div key={item.label} className="replay-eval-score">
                                                                <span>{item.label}</span>
                                                                <span>{item.value}점</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            {feedbackItems.length > 0 && (
                                                <div className="replay-eval-feedback">
                                                    {feedbackItems.map((item, index) => (
                                                        <div key={`${item.title}-${index}`} className="replay-eval-item">
                                                            <div className="replay-eval-head">
                                                                <span>{item.title}</span>
                                                                {item.score && <span className="replay-eval-badge">{item.score}점</span>}
                                                            </div>
                                                            <p>{item.body}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            {aiEval.fact_check_result && (
                                                <div className="replay-eval-fact">
                                                    <span>Fact-check</span>
                                                    <p>{aiEval.fact_check_result}</p>
                                                </div>
                                            )}
                                        </div>
                                    );
                                }
                                const personalPayload = parsePersonalPayload(msg);
                                if (personalPayload) {
                                    return (
                                        <div key={msg.message_id}>
                                            {renderPersonalFeedbackCard(personalPayload, msg)}
                                        </div>
                                    );
                                }
                                const summaryPayload = parseSummaryPayload(msg.content);
                                if (summaryPayload) {
                                    return (
                                        <div key={msg.message_id}>
                                            {renderSummaryCard(summaryPayload)}
                                        </div>
                                    );
                                }
                                const itemsPayload = parseItemsPayload(msg.content);
                                if (itemsPayload) {
                                    return (
                                        <div key={msg.message_id} className="replay-message ai">
                                            <div className="replay-message-head">
                                                <span className="replay-role">AI</span>
                                                <span className="replay-time">
                                                    {msg.turn ? `Turn ${msg.turn}` : "-"}
                                                </span>
                                            </div>
                                            <div className="replay-content">
                                                <strong>{itemsPayload.title}</strong>
                                                <ul className="replay-items-list">
                                                    {itemsPayload.items.map((item, index) => (
                                                        <li key={`item-${index}`}>{item}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    );
                                }
                                return (
                                    <div key={msg.message_id} className={`replay-message ${msg.role}`}>
                                        <div className="replay-message-head">
                                            <span className="replay-role">{msg.user_name || msg.role}</span>
                                            <span className="replay-time">
                                                {msg.turn ? `Turn ${msg.turn}` : "-"}
                                            </span>
                                        </div>
                                        <div className="replay-content">{msg.content}</div>
                                    </div>
                                );
                            })}
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
    const parseFeedback = (text) => {
        if (!text) return [];
        const normalized = text.replace(/\r\n/g, "\n");
        const parts = normalized.split(/\n(?=\*\*\[|###\s*\[)/);
        const items = [];

        parts.forEach((part) => {
            const chunk = part.trim();
            if (!chunk) return;

            const titleMatch = chunk.match(/\*\*\[([^\]]+)\]\*\*|###\s*\[([^\]]+)\]/);
            const title = titleMatch ? (titleMatch[1] || titleMatch[2]) : null;
            const scoreMatch = chunk.match(/점수\s*:\s*(\d+)\s*점/);
            const score = scoreMatch ? scoreMatch[1] : null;

            let body = chunk;
            if (titleMatch) {
                body = body.replace(titleMatch[0], "");
            }
            body = body.replace(/-?\s*점수\s*:\s*\d+\s*점\s*/g, "");
            body = body.replace(/-?\s*근거\s*:\s*/g, "");
            body = body.replace(/^\s*[-•]\s*/gm, "");
            body = body.trim();

            if (!title && !body) return;

            items.push({
                title: title || "추가 정보",
                score,
                body,
            });
        });

        return items;
    };
    const proFeedback = parseFeedback(proEval?.feedback_text || "");
    const conFeedback = parseFeedback(conEval?.feedback_text || "");
    const scoreItems = (scores) => {
        if (!scores) return [];
        return [
            { label: "주장 명확성", value: scores.clarity },
            { label: "근거 적합성", value: scores.evidence },
            { label: "상호작용", value: scores.interaction },
            { label: "태도", value: scores.attitude },
        ].filter((item) => item.value !== undefined && item.value !== null);
    };

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
                                <VerdictTeamStack
                                    title="찬성팀"
                                    tone="pro"
                                    totalScore={proEval?.total_score}
                                    scores={scoreItems(proEval?.scores)}
                                    feedback={proFeedback}
                                    factCheck={proEval?.fact_check_result}
                                />
                                <VerdictTeamStack
                                    title="반대팀"
                                    tone="con"
                                    totalScore={conEval?.total_score}
                                    scores={scoreItems(conEval?.scores)}
                                    feedback={conFeedback}
                                    factCheck={conEval?.fact_check_result}
                                />
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

function VerdictTeamStack({ title, tone, totalScore, scores, feedback, factCheck }) {
    return (
        <div className={`verdict-card stacked ${tone}`}>
            <div className="verdict-team-header">
                <span>{title}</span>
                <strong>{totalScore ?? "-"}점</strong>
            </div>
            <div className="verdict-team-section">
                <div className="verdict-team-section-title">상세 평가</div>
                {scores.length > 0 ? (
                    <div className="verdict-score-stack">
                        {scores.map((item) => {
                            const detail = feedback?.find((entry) => entry.title === item.label);
                            return (
                                <div key={item.label} className="verdict-score-row">
                                    <div className="verdict-score-label">
                                        <span>{item.label}</span>
                                        <span className="verdict-score-badge">{item.value}점</span>
                                    </div>
                                    {detail?.body && <p>{detail.body}</p>}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p>상세 평가가 없습니다.</p>
                )}
            </div>
            {factCheck && (
                <div className="verdict-factcheck">
                    <span>Fact-check</span>
                    <p>{factCheck}</p>
                </div>
            )}
        </div>
    );
}

function PersonalFeedbackModal({ item, onClose }) {
    const report = item?.report || null;
    const strengths = Array.isArray(report?.strength) ? report.strength : [];
    const weaknesses = Array.isArray(report?.weakness) ? report.weakness : [];
    const details = Array.isArray(report?.detailed_points) ? report.detailed_points : [];

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content personal-feedback-modal" onClick={(event) => event.stopPropagation()}>
                <button type="button" className="modal-close-btn" onClick={onClose} aria-label="닫기">
                    ×
                </button>
                <div className="personal-feedback-modal-header">
                    <h2>개인 피드백</h2>
                    <div className="personal-feedback-modal-meta">
                        <span>{item?.title || "토론 제목 없음"}</span>
                        <span>{item?.date || "-"}</span>
                        <span>{item?.role || "-"}</span>
                        <span>{item?.result || "-"}</span>
                    </div>
                </div>

                {!report && (
                    <div className="personal-feedback-empty">피드백 내용을 불러오지 못했습니다.</div>
                )}

                {report && (
                    <div className="personal-feedback-modal-body">
                        <div className="personal-feedback-section">
                            <h3>강점</h3>
                            {strengths.length > 0 ? (
                                <ul>
                                    {strengths.map((strength, index) => (
                                        <li key={`strength-${index}`}>{strength}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p>강점 정보가 없습니다.</p>
                            )}
                        </div>

                        <div className="personal-feedback-section">
                            <h3>개선 포인트</h3>
                            {weaknesses.length > 0 ? (
                                <ul>
                                    {weaknesses.map((weakness, index) => (
                                        <li key={`weakness-${index}`}>{weakness}</li>
                                    ))}
                                </ul>
                            ) : (
                                <p>개선 포인트가 없습니다.</p>
                            )}
                        </div>

                        <div className="personal-feedback-section">
                            <h3>세부 코칭</h3>
                            {details.length > 0 ? (
                                <div className="personal-feedback-detail-list">
                                    {details.map((detail, index) => (
                                        <div key={`detail-${index}`} className="personal-feedback-detail">
                                            <div className="personal-feedback-detail-head">
                                                <strong>Turn {detail.turn ?? "-"}</strong>
                                                <span>{detail.original_text || "발언 기록 없음"}</span>
                                            </div>
                                            {detail.critique && (
                                                <p className="personal-feedback-detail-text">
                                                    피드백: {detail.critique}
                                                </p>
                                            )}
                                            {detail.suggestion && (
                                                <p className="personal-feedback-detail-text">
                                                    제안: {detail.suggestion}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p>세부 코칭이 없습니다.</p>
                            )}
                        </div>

                        {report.recommended_reading && (
                            <div className="personal-feedback-section highlight">
                                추천 학습: <strong>{report.recommended_reading}</strong>
                            </div>
                        )}

                        {report.rawText && (
                            <div className="personal-feedback-section">
                                <h3>원문</h3>
                                <p>{report.rawText}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function BadgesTab({ badges }) {
    const formatDate = (isoString) => {
        if (!isoString) return "";
        const date = new Date(isoString);
        return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    };

    return (
        <div className="badges-grid">
            {badges.map((badge) => (
                <div 
                    key={badge.name} 
                    className={`badge-card ${badge.earned ? "earned" : "locked"}`}
                    title={badge.description} // 마우스 오버 시 조건 표시
                >
                    <span className={`badge-icon ${badge.earned ? "earned" : "locked"}`}>
                        {/* 아이콘이 있으면 아이콘 표시, 없으면 텍스트 */}
                        {badge.earned ? (badge.icon || "OK") : "🔒"}
                    </span>
                    <strong>{badge.name}</strong>
                    
                    {/* 획득 상태에 따른 텍스트 표시 */}
                    <span className="badge-status">
                        {badge.earned ? formatDate(badge.acquired_at) : "미획득"}
                    </span>
                    
                    {/* (선택사항) 설명 텍스트를 항상 보여주고 싶다면 아래 주석 해제 */}
                    {/* <p className="badge-desc">{badge.description}</p> */}
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
