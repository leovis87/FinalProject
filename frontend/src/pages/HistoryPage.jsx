import { useState, useEffect, useMemo } from "react";
import { useAuth } from "../contexts/AuthContext";
import { 
    RiFileList3Line, 
    RiChatCheckLine, 
    RiSearchLine,
    RiFilter3Line,
    RiArchiveDrawerLine,
    RiRestartLine,
    RiFilePaper2Line,
    RiEmotionHappyLine,
    RiEmotionUnhappyLine
} from "react-icons/ri";
import "../styles/HistoryPage.css";

// --- 1. 메인 페이지 컴포넌트 ---
function HistoryPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState("history"); // 'history' | 'feedback'
    
    // 데이터 상태
    const [historyRecords, setHistoryRecords] = useState([]);
    const [historyStatus, setHistoryStatus] = useState("idle");
    const [historyError, setHistoryError] = useState("");

    const [personalFeedbacks, setPersonalFeedbacks] = useState([]);
    const [personalStatus, setPersonalStatus] = useState("idle");
    const [personalError, setPersonalError] = useState("");

    // 모달 상태
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

    const [personalOpen, setPersonalOpen] = useState(false);
    const [personalTarget, setPersonalTarget] = useState(null);

    // --- 데이터 로딩 로직 ---
    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("access_token");
        if (!token) return;

        const fetchHistory = async () => {
            setHistoryStatus("loading");
            try {
                const response = await fetch("/api/debates/history", {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (!response.ok) throw new Error("기록을 불러오는데 실패했습니다.");

                const data = await response.json();
                const items = Array.isArray(data) ? data : [];
                
                const mapped = items.map((item) => ({
                    id: item.debate_room_id ?? item.id,
                    title: item.title || item.topic || "제목 없음",
                    date: new Date(item.finished_at || item.started_at || item.joined_at).toLocaleDateString(),
                    rawDate: item.finished_at || item.started_at || item.joined_at,
                    role: item.role === 'pro' ? '찬성' : item.role === 'con' ? '반대' : '관전',
                    result: item.result === 'win' ? '승리' : item.result === 'lose' ? '패배' : item.result === 'draw' ? '무승부' : '미정'
                }));

                mapped.sort((a, b) => new Date(b.rawDate) - new Date(a.rawDate));

                if (isMounted) {
                    setHistoryRecords(mapped);
                    setHistoryStatus("success");
                }
            } catch (error) {
                if (isMounted) {
                    setHistoryError(error.message);
                    setHistoryStatus("error");
                }
            }
        };
        fetchHistory();
        return () => { isMounted = false; };
    }, [user]);

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (!token || historyRecords.length === 0) return;
        let isMounted = true;

        const parseReportPayload = (content) => {
            if (!content) return null;
            if (typeof content === "object") return content;
            try { return JSON.parse(content); } 
            catch { return { rawText: content }; }
        };

        const fetchFeedbacks = async () => {
            setPersonalStatus("loading");
            try {
                const results = await Promise.all(historyRecords.map(async (record) => {
                    try {
                        const res = await fetch(`/api/debates/${record.id}/messages`, {
                            headers: { Authorization: `Bearer ${token}` }
                        });
                        if (!res.ok) return [];
                        const msgs = await res.json();
                        
                        return msgs
                            .filter(m => m.display_type === "report_user")
                            .map(m => ({
                                id: m.message_id || `${record.id}-feedback`,
                                debateId: record.id,
                                title: record.title,
                                date: record.date,
                                role: record.role,
                                result: record.result,
                                report: parseReportPayload(m.content)
                            }));
                    } catch {
                        return [];
                    }
                }));

                if (isMounted) {
                    const flattened = results.flat();
                    setPersonalFeedbacks(flattened);
                    setPersonalStatus("success");
                }
            } catch (error) {
                if (isMounted) {
                    setPersonalError("피드백 데이터를 가져오지 못했습니다.");
                    setPersonalStatus("error");
                }
            }
        };
        fetchFeedbacks();
        return () => { isMounted = false; };
    }, [historyRecords]);

    // --- 핸들러들 ---
    const handleOpenReplay = async (record) => {
        const token = localStorage.getItem("access_token");
        if (!token) return;
        setReplayOpen(true);
        setReplayMeta(record);
        setReplayStatus("loading");
        try {
            const response = await fetch(`/api/debates/${record.id}/messages`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if(!response.ok) throw new Error("리플레이 로드 실패");
            const data = await response.json();
            setReplayMessages(Array.isArray(data) ? data : []);
            setReplayStatus("success");
        } catch (e) {
            setReplayError(e.message);
            setReplayStatus("error");
        }
    };

    const handleOpenVerdict = async (record) => {
        const token = localStorage.getItem("access_token");
        if (!token) return;
        setVerdictOpen(true);
        setVerdictMeta(record);
        setVerdictStatus("loading");
        try {
            const response = await fetch(`/api/debates/${record.id}/verdict`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if(!response.ok) throw new Error("판결문 로드 실패");
            const data = await response.json();
            setVerdictData(data);
            setVerdictStatus("success");
        } catch (e) {
            setVerdictError(e.message);
            setVerdictStatus("error");
        }
    };

    return (
        <div className="page-container">
            {/* 상단 배너 섹션 (VerdictsPage와 동일한 구조/스타일) */}
            <section className="history-banner-card">
                <div className="history-banner-header">
                    <div className="history-icon-box">
                        <RiArchiveDrawerLine />
                    </div>
                    <h1 className="history-main-title">기록 보관소</h1>
                </div>
                <p className="history-sub-desc">
                    나의 지난 토론 기록을 되돌아보고, AI 코칭을 통해 성장하세요.
                </p>
            </section>

            {/* 탭 네비게이션 */}
            <div className="history-content-wrapper">
                <div className="mypage-tabs">
                    <button 
                        className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                        onClick={() => setActiveTab('history')}
                    >
                        <RiFileList3Line /> 토론 기록
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
                        onClick={() => setActiveTab('feedback')}
                    >
                        <RiChatCheckLine /> 개인 피드백
                    </button>
                </div>

                <div className="tab-content">
                    {activeTab === 'history' ? (
                        <HistoryListSection 
                            records={historyRecords}
                            status={historyStatus}
                            error={historyError}
                            onReplay={handleOpenReplay}
                            onVerdict={handleOpenVerdict}
                        />
                    ) : (
                        <FeedbackListSection 
                            feedbacks={personalFeedbacks}
                            status={personalStatus}
                            error={personalError}
                            onOpen={(item) => {
                                setPersonalTarget(item);
                                setPersonalOpen(true);
                            }}
                        />
                    )}
                </div>
            </div>

            {/* --- 모달 컴포넌트들 --- */}
            {replayOpen && (
                <ReplayModal
                    record={replayMeta}
                    status={replayStatus}
                    error={replayError}
                    messages={replayMessages}
                    onClose={() => { setReplayOpen(false); setReplayMessages([]); }}
                />
            )}
            {verdictOpen && (
                <VerdictModal 
                    record={verdictMeta}
                    status={verdictStatus}
                    error={verdictError}
                    verdict={verdictData}
                    onClose={() => { setVerdictOpen(false); setVerdictData(null); }}
                />
            )}
            {personalOpen && (
                <PersonalFeedbackModal 
                    item={personalTarget}
                    onClose={() => { setPersonalOpen(false); setPersonalTarget(null); }}
                />
            )}
        </div>
    );
}

// ----------------------------------------------------------------------
// 2. 하위 섹션 컴포넌트
// ----------------------------------------------------------------------

function HistoryListSection({ records, status, error, onReplay, onVerdict }) {
    const [filter, setFilter] = useState("all");
    const [search, setSearch] = useState("");

    const filteredRecords = useMemo(() => {
        let result = records;
        if (filter === 'win') result = result.filter(r => r.result === '승리');
        if (filter === 'lose') result = result.filter(r => r.result === '패배');
        
        if (search) {
            result = result.filter(r => r.title.includes(search));
        }
        return result;
    }, [records, filter, search]);

    if (status === 'loading') return <div className="loading-state">기록을 불러오는 중...</div>;
    if (status === 'error') return <div className="error-text">{error}</div>;

    return (
        <div className="history-section animate-fade-in">
            {/* 필터 바 */}
            <div className="history-filter-bar">
                <div className="search-input-box small">
                    <RiSearchLine className="search-icon" />
                    <input 
                        type="text" 
                        placeholder="토론 제목 검색" 
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <div className="filter-group-row">
                    <div className="select-wrapper">
                        <RiFilter3Line className="filter-icon-small"/>
                        <select 
                            className="filter-select"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        >
                            <option value="all">전체 결과</option>
                            <option value="win">승리만</option>
                            <option value="lose">패배만</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="history-list-grid">
                {filteredRecords.length === 0 ? (
                    <div className="empty-state">
                        <p>토론 기록이 없습니다.</p>
                    </div>
                ) : (
                    filteredRecords.map((item) => (
                        <div key={item.id} className="history-card-item">
                            {/* 상단: 날짜 및 뱃지 */}
                            <div className="history-card-top">
                                <span className="history-date">{item.date}</span>
                                <span className={`result-badge-small ${item.result === '승리' ? 'win' : item.result === '패배' ? 'lose' : 'draw'}`}>
                                    {item.result}
                                </span>
                            </div>

                            {/* 중단: 제목 및 역할 */}
                            <div className="history-card-main">
                                <h3 className="history-item-title">{item.title}</h3>
                                <div className="history-role-info">
                                    <span className={`role-pill ${item.role === '찬성' ? 'pro' : item.role === '반대' ? 'con' : 'obs'}`}>
                                        {item.role}
                                    </span>
                                    <span className="role-text">측 참여</span>
                                </div>
                            </div>
                            
                            {/* 하단: 액션 버튼 */}
                            <div className="history-card-footer">
                                <button className="history-action-btn outline" onClick={() => onReplay(item)}>
                                    <RiRestartLine /> 리플레이
                                </button>
                                <button className="history-action-btn primary" onClick={() => onVerdict(item)}>
                                    <RiFilePaper2Line /> 판결문
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

function FeedbackListSection({ feedbacks, status, error, onOpen }) {
    const [query, setQuery] = useState("");

    const filtered = useMemo(() => {
        if (!query) return feedbacks;
        return feedbacks.filter(item => 
            item.title.includes(query)
        );
    }, [feedbacks, query]);

    const getPreview = (report) => {
        if (!report) return "내용 없음";
        if (report.strength?.length > 0) return `🌟 ${report.strength[0]}`;
        if (report.weakness?.length > 0) return `🔥 ${report.weakness[0]}`;
        return report.rawText || "상세 내용을 확인하세요.";
    };

    if (status === 'loading') return <div className="loading-state">피드백을 분석 중...</div>;
    if (status === 'error') return <div className="error-text">{error}</div>;

    return (
        <div className="feedback-section animate-fade-in">
            <div className="history-filter-bar">
                <div className="search-input-box small full-width">
                    <RiSearchLine className="search-icon" />
                    <input 
                        type="text" 
                        placeholder="주제 키워드로 검색..." 
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                </div>
            </div>

            <div className="feedback-grid">
                {filtered.length === 0 ? (
                    <div className="empty-state">피드백 내역이 없습니다.</div>
                ) : (
                    filtered.map((item) => (
                        <div key={item.id} className="feedback-card" onClick={() => onOpen(item)}>
                            <div className="feedback-header">
                                <div className={`feedback-result-icon ${item.result === '승리' ? 'win' : 'lose'}`}>
                                    {item.result === '승리' ? <RiEmotionHappyLine /> : <RiEmotionUnhappyLine />}
                                </div>
                                <div className="feedback-meta">
                                    <span className="feedback-date">{item.date}</span>
                                    <span className={`feedback-role ${item.role === '찬성' ? 'pro' : 'con'}`}>
                                        {item.role}
                                    </span>
                                </div>
                            </div>
                            <h4 className="feedback-title">{item.title}</h4>
                            <div className="feedback-preview-box">
                                {getPreview(item.report)}
                            </div>
                            <div className="feedback-footer-link">
                                상세 리포트 확인하기 &rarr;
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// ----------------------------------------------------------------------
// 3. 모달 컴포넌트
// ----------------------------------------------------------------------

function ReplayModal({ record, status, error, messages, onClose }) {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content replay-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose}>×</button>
                <div className="modal-header-simple">
                    <h2>리플레이</h2>
                    <p>{record?.title}</p>
                </div>
                <div className="replay-body-scroll">
                    {status === 'loading' && <div className="loading-state">대화 내용을 불러오는 중...</div>}
                    {status === 'error' && <div className="error-text">{error}</div>}
                    {status === 'success' && messages.map((msg, idx) => (
                        <div key={msg.id || idx} className={`chat-bubble-row ${msg.role}`}>
                            <div className="chat-sender">{msg.user_name || (msg.role === 'ai' ? 'AI 사회자' : '참가자')}</div>
                            <div className={`chat-bubble ${msg.role}`}>
                                {typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function VerdictModal({ record, status, error, verdict, onClose }) {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content verdict-modal-content" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose}>×</button>
                <div className="verdict-modal-header">
                    <div className={`verdict-badge ${record?.result === '승리' ? 'win' : 'lose'}`}>
                         {record?.result === '승리' ? 'WIN' : 'LOSE'}
                    </div>
                    <h2>판결문</h2>
                    <p className="verdict-sub-info">AI 배심원이 분석한 토론 결과입니다.</p>
                </div>
                <div className="verdict-scroll-body">
                    {status === 'loading' && <div className="loading-state">판결문을 불러오는 중...</div>}
                    {status === 'error' && <div className="error-text">{error}</div>}
                    {status === 'success' && verdict && (
                        <div className="verdict-content-wrapper">
                            <div className="verdict-summary-section">
                                <h3>💡 총평</h3>
                                <p>{verdict.summary}</p>
                            </div>
                            {verdict.best_player && (
                                <div className="verdict-mvp-section">
                                    <span className="mvp-label">🏆 MVP Player</span>
                                    <span className="mvp-name">{verdict.best_player}</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function PersonalFeedbackModal({ item, onClose }) {
    const report = item?.report || {};
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content personal-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose}>×</button>
                <div className="modal-header-simple">
                    <h2>AI 코칭 리포트</h2>
                    <p>{item?.title}</p>
                </div>
                <div className="modal-scroll-body">
                    {report.strength && (
                        <div className="feedback-block good">
                            <h3>🌟 강점 분석</h3>
                            <ul>{report.strength.map((t, i) => <li key={i}>{t}</li>)}</ul>
                        </div>
                    )}
                    {report.weakness && (
                        <div className="feedback-block bad">
                            <h3>🔥 개선 포인트</h3>
                            <ul>{report.weakness.map((t, i) => <li key={i}>{t}</li>)}</ul>
                        </div>
                    )}
                    {report.recommended_reading && (
                        <div className="feedback-block info">
                            <h3>📚 추천 학습 자료</h3>
                            <p>{report.recommended_reading}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default HistoryPage;