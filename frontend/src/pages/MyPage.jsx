import { useState, useEffect, useMemo } from "react";
import { useAuth } from "../contexts/AuthContext";
import { debateApi } from "../api/debateApi";
import { 
    RiFlashlightLine, 
    RiTrophyLine, 
    RiBarChartHorizontalLine, 
    RiMedalLine 
} from "react-icons/ri";
import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip
} from "recharts";
import '../styles/MyPage.css';

// 요청하신 배지 설정
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
    const [activeTab, setActiveTab] = useState("summary"); // 'summary' | 'badge'
    const [historyRecords, setHistoryRecords] = useState([]);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);

    // --- 기본 통계 계산 ---
    const winRate = user?.total_debates > 0 
        ? Math.round((user.win_count / user.total_debates) * 100) 
        : 0;
    const currentExp = user?.exp || 0;
    const maxExp = user?.next_level_exp || 100;
    const expPercentage = Math.min((currentExp / maxExp) * 100, 100);

    const TIER_GOALS = {
        "옹알이": 100, "입문자": 300, "아마추어": 600, "프로": 1000, "마스터": 2000
    };
    const currentPoints = user?.points || 0;
    const currentTier = user?.tier || "옹알이";
    const nextTierPoints = TIER_GOALS[currentTier];
    let tierPercentage = 100;
    if (nextTierPoints) {
        tierPercentage = Math.min((currentPoints / nextTierPoints) * 100, 100);
    }

    // --- 토론 기록 가져오기 ---
    useEffect(() => {
        const fetchHistory = async () => {
            setIsLoadingHistory(true);
            try {
                // API 함수가 없으면 빈 배열 처리 (debateApi.getHistory 구현 필요)
                const data = debateApi.getHistory ? await debateApi.getHistory() : [];
                
                const mapped = (Array.isArray(data) ? data : []).map(item => ({
                    id: item.debate_room_id ?? item.id,
                    title: item.title || item.topic || "제목 없음",
                    rawDate: item.finished_at || item.started_at || item.joined_at, 
                    date: new Date(item.finished_at || item.started_at || item.joined_at).toLocaleDateString(),
                    role: item.role === 'pro' ? '찬성' : item.role === 'con' ? '반대' : '관전',
                    result: item.result === 'win' ? '승리' : item.result === 'lose' ? '패배' : item.result === 'draw' ? '무승부' : '미정'
                }));
                
                mapped.sort((a, b) => new Date(b.rawDate) - new Date(a.rawDate));
                setHistoryRecords(mapped);
            } catch (error) {
                console.error("토론 기록 로드 실패:", error);
            } finally {
                setIsLoadingHistory(false);
            }
        };

        if (user) {
            fetchHistory();
        }
    }, [user]);

    // --- 차트 데이터 (최근 7일) ---
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
            if (isNaN(date.getTime()) || date < start || date > now) return;
            counts[date.getDay()].debates += 1;
        });
        return counts;
    }, [historyRecords]);

    const recentDebates = historyRecords.slice(0, 3);

    // --- 배지 현황 매핑 ---
    const myBadges = useMemo(() => {
        const userBadges = user?.badges || []; // userBadges는 [{name: "...", acquired_at: "..."}] 형태 가정
        
        return BADGE_CONFIG.map((config) => {
            // 이름이 일치하는 배지를 찾음
            const earnedBadge = userBadges.find((b) => b.name === config.name);
            
            return {
                ...config,
                earned: !!earnedBadge, // 획득 여부
                acquired_at: earnedBadge ? earnedBadge.acquired_at : null
            };
        });
    }, [user]);

    // 날짜 포맷팅 헬퍼
    const formatDate = (isoString) => {
        if (!isoString) return "";
        const date = new Date(isoString);
        return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    };

    if (!user) return <div className="loading">로딩 중...</div>;

    return (
        <div className="page-container">
            {/* 1. 상단 통계 카드 */}
            <div className="user-stats-grid">
                <div className="user-stat-card">
                    <div className="user-stat-label">총 토론 수</div>
                    <div className="user-stat-value">{user.total_debates}회</div>
                </div>
                <div className="user-stat-card">
                    <div className="user-stat-label">승률</div>
                    <div className="user-stat-value">{winRate}%</div>
                    <div className="user-stat-sub">
                        ({user.win_count}승 / {Math.max(0, user.total_debates - user.win_count)}패)
                    </div>
                </div>
                <div className="user-stat-card">
                    <div className="user-stat-label">최근 7일 토론</div>
                    <div className="user-stat-value">{user.recent_debate_count || 0}회</div>
                </div>
            </div>

            {/* 2. 레벨/티어 진행도 */}
            <div className="progress-section">
                <div className="level-progress-card">
                    <div className="level-header">
                        <div className="level-title">
                            <div className="icon-box"><RiFlashlightLine /></div>
                            <span>다음 레벨까지</span>
                        </div>
                        <div className="xp-text">
                            <span className="current">{currentExp}</span>
                            <span className="divider">/</span>
                            <span className="max">{maxExp} XP</span>
                        </div>
                    </div>
                    <div className="xp-track">
                        <div className="xp-fill" style={{ width: `${expPercentage}%` }}></div>
                    </div>
                    <p className="level-msg">
                        레벨업까지 <strong>{maxExp - currentExp} XP</strong> 남았습니다.
                    </p>
                </div>

                <div className="tier-progress-card">
                    <div className="tier-header">
                        <div className="tier-title">
                            <div className="icon-box"><RiTrophyLine /></div>
                            <span>{currentTier}</span>
                        </div>
                        <div className="xp-text">
                            <span className="current">{currentPoints}</span>
                            {nextTierPoints && (
                                <><span className="divider">/</span><span className="max">{nextTierPoints} 점</span></>
                            )}
                        </div>
                    </div>
                    <div className="xp-track">
                        <div className="xp-fill tier-fill" style={{ width: `${tierPercentage}%` }}></div>
                    </div>
                    <p className="tier-msg">
                        {nextTierPoints 
                            ? <>다음 티어까지 <strong>{nextTierPoints - currentPoints} 점</strong> 남았습니다.</>
                            : <strong>최고 티어에 도달했습니다!</strong>
                        }
                    </p>
                </div>
            </div>

            {/* 3. 하단 탭 섹션 */}
            <div className="mypage-bottom-section">
                <div className="mypage-tabs">
                    <button 
                        className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
                        onClick={() => setActiveTab('summary')}
                    >
                        <RiBarChartHorizontalLine /> 활동 요약
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'badge' ? 'active' : ''}`}
                        onClick={() => setActiveTab('badge')}
                    >
                        <RiMedalLine /> 배지
                    </button>
                </div>

                <div className="tab-content">
                    {activeTab === 'summary' ? (
                        <div className="summary-grid-section animate-fade-in">
                            {/* 활동 그래프 */}
                            <div className="chart-card">
                                <div className="section-header">
                                    <h3>최근 활동 추이</h3>
                                    <span className="section-desc">지난 7일간의 참여 기록</span>
                                </div>
                                <div className="chart-wrapper">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={activityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                                            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} allowDecimals={false} />
                                            <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                                            <Line 
                                                type="monotone" 
                                                dataKey="debates" 
                                                stroke="var(--point-main-color)" 
                                                strokeWidth={3} 
                                                dot={{ r: 4, fill: 'var(--point-main-color)', strokeWidth: 2, stroke: '#fff' }}
                                                activeDot={{ r: 6 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* 최근 토론 */}
                            <div className="recent-history-card">
                                <div className="section-header">
                                    <h3>최근 참여한 토론</h3>
                                    <span className="section-desc">최신순 3건</span>
                                </div>
                                <div className="recent-list-wrapper">
                                    {isLoadingHistory ? (
                                        <div className="empty-message">불러오는 중...</div>
                                    ) : recentDebates.length === 0 ? (
                                        <div className="empty-message">참여한 토론 기록이 없습니다.</div>
                                    ) : (
                                        recentDebates.map((item) => (
                                            <div key={item.id} className="recent-item">
                                                <div className="recent-item-info">
                                                    <div className="recent-item-title">{item.title}</div>
                                                    <div className="recent-item-meta">
                                                        <span>{item.date}</span>
                                                        <span className="dot">·</span>
                                                        <span>{item.role}</span>
                                                    </div>
                                                </div>
                                                <div className={`result-badge ${item.result === '승리' ? 'win' : item.result === '패배' ? 'lose' : 'draw'}`}>
                                                    {item.result}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="badge-grid-section animate-fade-in">
                            {/* 배지 리스트 */}
                            <div className="badge-card-container">
                                {myBadges.map((badge) => (
                                    <div key={badge.name} className={`badge-item ${badge.earned ? 'acquired' : 'locked'}`}>
                                        <div className="badge-icon">
                                            {badge.earned ? badge.icon : "🔒"}
                                        </div>
                                        <div className="badge-info">
                                            <div className="badge-name">{badge.name}</div>
                                            <div className="badge-desc">{badge.description}</div>
                                            {badge.earned && badge.acquired_at && (
                                                <div className="badge-date">{formatDate(badge.acquired_at)} 획득</div>
                                            )}
                                        </div>
                                        {badge.earned && <div className="badge-check">✔</div>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
export default MyPage;