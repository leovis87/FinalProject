import { useState, useEffect, useMemo } from "react";
import { useAuth } from "../contexts/AuthContext";
import { 
    RiFileList3Line, 
    RiChatCheckLine, 
    RiSearchLine,
    RiFilter3Line
} from "react-icons/ri";
import "../styles/MyPage.css"; // 스타일은 MyPage와 공유하거나 별도 CSS 사용
import "../styles/Modal.css";

// ----------------------------------------------------------------------
// 1. 메인 페이지 컴포넌트
// ----------------------------------------------------------------------
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

    // --- 1. 토론 기록 불러오기 ---
    useEffect(() => {
        let isMounted = true;
        const token = localStorage.getItem("access_token");

        if (!token) return;

        const fetchHistory = async () => {
            setHistoryStatus("loading");
            try {
                // 실제 API 엔드포인트에 맞춰 수정
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

                // 최신순 정렬
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

    // --- 2. 개인 피드백 데이터 취합하기 ---
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
                // 각 토론 기록에 대해 메시지를 조회하여 'report_user' 타입만 필터링
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

    // --- 핸들러: 리플레이 열기 ---
    const handleOpenReplay = async (record) => {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        setReplayOpen(true);
        setReplayMeta(record);
        setReplayStatus("loading");
        
        try {
            // 포트나 주소는 환경에 맞게 조정 필요
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

    // --- 핸들러: 판결문 열기 ---
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
            <div className="page-header">
                <h1>기록 보관소</h1>
                <p>지난 토론의 기록과 AI 코칭 내역을 확인하세요.</p>
            </div>

            <div className="mypage-bottom-section">
                {/* 탭 네비게이션 */}
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
// 2. 하위 섹션 컴포넌트 (리스트 렌더링)
// ----------------------------------------------------------------------

// A. 토론 기록 리스트 섹션
function HistoryListSection({ records, status, error, onReplay, onVerdict }) {
    const [filter, setFilter] = useState("all"); // 'all', 'win', 'lose'

    const filteredRecords = useMemo(() => {
        if (filter === 'all') return records;
        if (filter === 'win') return records.filter(r => r.result === '승리');
        if (filter === 'lose') return records.filter(r => r.result === '패배');
        return records;
    }, [records, filter]);

    if (status === 'loading') return <div className="loading-msg">기록을 불러오는 중...</div>;
    if (status === 'error') return <div className="error-msg">{error}</div>;

    return (
        <div className="history-section animate-fade-in">
            <div className="filter-bar">
                <div className="filter-group">
                    <RiFilter3Line className="filter-icon"/>
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
                <div className="record-count">총 {filteredRecords.length}건</div>
            </div>

            <div className="history-list-container">
                {filteredRecords.length === 0 ? (
                    <div className="empty-state">기록이 없습니다.</div>
                ) : (
                    filteredRecords.map((item) => (
                        <div key={item.id} className="history-card-item">
                            <div className="history-card-main">
                                <div className="history-card-header">
                                    <span className={`role-badge ${item.role === '찬성' ? 'pro' : item.role === '반대' ? 'con' : 'obs'}`}>
                                        {item.role}
                                    </span>
                                    <span className="history-date">{item.date}</span>
                                </div>
                                <h3 className="history-title">{item.title}</h3>
                            </div>
                            
                            <div className="history-card-actions">
                                <div className={`result-tag ${item.result === '승리' ? 'win' : item.result === '패배' ? 'lose' : ''}`}>
                                    {item.result}
                                </div>
                                <div className="btn-group">
                                    <button className="action-btn outline" onClick={() => onReplay(item)}>
                                        리플레이
                                    </button>
                                    <button className="action-btn primary" onClick={() => onVerdict(item)}>
                                        판결문
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// B. 피드백 리스트 섹션
function FeedbackListSection({ feedbacks, status, error, onOpen }) {
    const [query, setQuery] = useState("");

    const filtered = useMemo(() => {
        if (!query) return feedbacks;
        return feedbacks.filter(item => 
            item.title.includes(query) || 
            (item.report?.rawText && item.report.rawText.includes(query))
        );
    }, [feedbacks, query]);

    const getSummary = (report) => {
        if (!report) return "내용 없음";
        if (report.strength?.length > 0) return `강점: ${report.strength[0]}`;
        if (report.weakness?.length > 0) return `개선: ${report.weakness[0]}`;
        return report.rawText || "상세 내용을 확인하세요.";
    };

    if (status === 'loading') return <div className="loading-msg">피드백을 분석 중...</div>;
    if (status === 'error') return <div className="error-msg">{error}</div>;

    return (
        <div className="feedback-section animate-fade-in">
            <div className="search-bar-container">
                <RiSearchLine className="search-icon"/>
                <input 
                    type="text" 
                    placeholder="주제 또는 내용 검색..." 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="search-input"
                />
            </div>

            <div className="feedback-grid">
                {filtered.length === 0 ? (
                    <div className="empty-state">피드백 내역이 없습니다.</div>
                ) : (
                    filtered.map((item) => (
                        <div key={item.id} className="feedback-card" onClick={() => onOpen(item)}>
                            <div className="feedback-header">
                                <span className="feedback-date">{item.date}</span>
                                <span className={`feedback-role ${item.role === '찬성' ? 'pro' : 'con'}`}>
                                    {item.role}
                                </span>
                            </div>
                            <h4 className="feedback-title">{item.title}</h4>
                            <p className="feedback-preview">
                                {getSummary(item.report)}
                            </p>
                            <div className="feedback-footer">
                                <span>상세 보기 &rarr;</span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// ----------------------------------------------------------------------
// 3. 모달 컴포넌트 (제공된 코드 기반 단순화/통합)
// ----------------------------------------------------------------------

function ReplayModal({ record, status, error, messages, onClose }) {
    // 메시지 파싱 및 정규화 로직 (제공된 코드의 normalizeMessages 등 활용 필요)
    // 간략하게 렌더링하도록 처리
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content replay-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose}>×</button>
                <div className="replay-header">
                    <h2>{record?.title} <span className="sub">리플레이</span></h2>
                </div>
                <div className="replay-body">
                    {status === 'loading' && <div>대화 내용을 불러오는 중...</div>}
                    {status === 'error' && <div className="error">{error}</div>}
                    {status === 'success' && messages.map((msg, idx) => (
                        <div key={msg.id || idx} className={`replay-msg ${msg.role}`}>
                            <div className="msg-sender">{msg.user_name || msg.role}</div>
                            <div className="msg-bubble">{
                                typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
                            }</div>
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
            <div className="modal-content verdict-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close-btn" onClick={onClose}>×</button>
                <div className="verdict-header">
                    <h2>판결문</h2>
                    <div className="verdict-winner">
                         {record?.result === '승리' ? '👑 승리' : record?.result === '패배' ? '💀 패배' : '무승부'}
                    </div>
                </div>
                <div className="verdict-body">
                    {status === 'loading' && <div>판결문을 작성 중...</div>}
                    {status === 'error' && <div className="error">{error}</div>}
                    {status === 'success' && verdict && (
                        <>
                            <div className="verdict-summary">
                                <h3>총평</h3>
                                <p>{verdict.summary}</p>
                            </div>
                            {/* MVP 등 추가 정보 */}
                            {verdict.best_player && (
                                <div className="verdict-mvp">
                                    🏆 MVP: {verdict.best_player}
                                </div>
                            )}
                        </>
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
                <div className="modal-header">
                    <h2>개인 코칭 리포트</h2>
                    <p>{item?.title}</p>
                </div>
                <div className="modal-scroll-body">
                    {/* 강점 */}
                    {report.strength && (
                        <div className="feedback-block good">
                            <h3>🌟 잘한 점</h3>
                            <ul>{report.strength.map((t, i) => <li key={i}>{t}</li>)}</ul>
                        </div>
                    )}
                    {/* 개선점 */}
                    {report.weakness && (
                        <div className="feedback-block bad">
                            <h3>🔥 보완할 점</h3>
                            <ul>{report.weakness.map((t, i) => <li key={i}>{t}</li>)}</ul>
                        </div>
                    )}
                    {/* 추천 자료 */}
                    {report.recommended_reading && (
                        <div className="feedback-block info">
                            <h3>📚 추천 학습</h3>
                            <p>{report.recommended_reading}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default HistoryPage;