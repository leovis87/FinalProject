import { useEffect, useState } from "react";
import { debateApi } from "../api/debateApi";
import { 
    RiMedalLine, 
    RiSearchLine,
    RiFilterLine,
    RiBookOpenLine,
    RiQuillPenLine,
    RiGlobalLine,
    RiFlaskLine,
    RiScales3Line,
    RiChatQuoteLine,
    RiTrophyLine,
    RiVipCrownLine // [추가] 우승자 아이콘
} from "react-icons/ri";
import VerdictDetailModal from "../components/modals/VerdictDetailModal";
import "../styles/VerdictsPage.css"

function VerdictsPage() {
    const [verdicts, setVerdicts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    
    // 모달 및 필터 상태
    const [selectedRoomId, setSelectedRoomId] = useState(null);
    const [searchKeyword, setSearchKeyword] = useState("");
    const [selectedSubject, setSelectedSubject] = useState("all");
    const [selectedGrade, setSelectedGrade] = useState("all");

    useEffect(() => {
        const fetchVerdicts = async () => {
            setIsLoading(true);
            setError("");
            try {
                const response = await debateApi.getPopularVerdicts(20);
                const data = response.data || response;
                setVerdicts(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error(err);
                setError("판결문 목록을 불러오지 못했습니다.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchVerdicts();
    }, []);

    const subjects = [
        { id: 'all', label: '전체' },
        { id: 'korean', label: '국어', icon: <RiQuillPenLine /> },
        { id: 'social', label: '사회', icon: <RiGlobalLine /> },
        { id: 'science', label: '과학', icon: <RiFlaskLine /> },
        { id: 'moral', label: '도덕', icon: <RiScales3Line /> },
    ];

    const getSubjectInfo = (category) => {
        const lowerCat = category?.toLowerCase();
        const found = subjects.find(s => s.id === lowerCat);
        return found || { label: category || '기타', icon: <RiChatQuoteLine /> };
    };

    const grades = [
        { id: 'all', label: '청소년' },
        { id: 'elementary_low', label: '초등 저학년' },
        { id: 'elementary_high', label: '초등 고학년' },
        { id: 'middle', label: '중학교' },
        { id: 'high', label: '고등학교' },
    ];

    const getGradeLabel = (level) => {
        const normalized = level?.toLowerCase(); 
        const found = grades.find(g => g.id === normalized || g.id === normalized?.replace('_', '')); 
        if (found) return found.label;
        if (normalized?.includes('elementary')) return '초등학교';
        if (normalized?.includes('middle')) return '중학교';
        if (normalized?.includes('high')) return '고등학교';
        return '전체';
    };

    const filteredVerdicts = verdicts.filter(item => {
        const title = item.title || "";
        const topic = item.topic || "";
        const category = item.category || "";
        const level = item.level || "";

        const matchesKeyword = title.includes(searchKeyword) || topic.includes(searchKeyword);
        const matchesSubject = selectedSubject === 'all' || category.toLowerCase() === selectedSubject;
        const matchesGrade = selectedGrade === 'all' || level.toLowerCase().replace('_', '') === selectedGrade.replace('_', '');
        
        return matchesKeyword && matchesSubject && matchesGrade;
    });

    return (
        <div className="page-container">
            {/* 상단 배너 */}
            <section className="verdicts-banner-card">
                <div className="verdicts-banner-header">
                    <div className="verdict-icon-box">
                        <RiMedalLine />
                    </div>
                    <h1 className="verdicts-main-title">우수 판결문</h1>
                </div>
                <p className="verdicts-sub-desc">
                    AI 배심원이 평가한 우수 토론 사례를 통해 논리력을 키워보세요
                </p>
            </section>

            {/* 필터 섹션 */}
            <section className="verdicts-filter-section">
                <div className="verdicts-filter-card">
                    <div className="filter-search-row">
                        <div className="search-input-box">
                            <RiSearchLine className="search-icon" />
                            <input 
                                type="text" 
                                placeholder="판결문 제목이나 주제를 검색해보세요" 
                                value={searchKeyword}
                                onChange={(e) => setSearchKeyword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="filter-group">
                        <div className="filter-label-row">
                            <RiFilterLine className="filter-icon" />
                            <span className="filter-label">과목</span>
                        </div>
                        <div className="filter-btn-group">
                            {subjects.map((sub) => (
                                <button
                                    key={sub.id}
                                    className={`filter-chip ${selectedSubject === sub.id ? 'active' : ''}`}
                                    onClick={() => setSelectedSubject(sub.id)}
                                >
                                    {sub.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="filter-group">
                        <div className="filter-label-row">
                            <RiBookOpenLine className="filter-icon" />
                            <span className="filter-label">학년</span>
                        </div>
                        <div className="filter-btn-group">
                            {grades.map((grd) => (
                                <button
                                    key={grd.id}
                                    className={`filter-chip ${selectedGrade === grd.id ? 'active' : ''}`}
                                    onClick={() => setSelectedGrade(grd.id)}
                                >
                                    {grd.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <hr className="filter-divider" />
                    <div className="filter-count-row">
                        총 <strong>{filteredVerdicts.length}</strong>개의 우수 판결문이 있습니다.
                    </div>
                </div>
            </section>

            {/* 판결문 리스트 섹션 */}
            <section className="verdicts-list-section">
                {isLoading ? (
                    <div className="loading-state">판결문을 불러오는 중...</div>
                ) : error ? (
                    <div className="empty-state">{error}</div>
                ) : filteredVerdicts.length === 0 ? (
                    <div className="empty-state">조건에 맞는 판결문이 없습니다.</div>
                ) : (
                    <div className="verdicts-grid">
                        {filteredVerdicts.map((item) => {
                            const subjectInfo = getSubjectInfo(item.category);
                            const contentPreview = item.summary || "판결문 요약 정보가 없습니다.";
                            const score = item.rating ? item.rating.toFixed(1) : "0.0";
                            
                            const rawBestPlayer = item.best_player || "익명";
                            const bestPlayer = rawBestPlayer.replace(/\s*\(ID:.*?\)/g, "").trim();

                            const dateObj = item.finished_at ? new Date(item.finished_at) : new Date();
                            const formattedDate = `${dateObj.getFullYear()}. ${dateObj.getMonth() + 1}. ${dateObj.getDate()}`;

                            return (
                                <div 
                                    key={item.debate_room_id} 
                                    className="verdict-card"
                                    onClick={() => setSelectedRoomId(item.debate_room_id)}
                                >
                                    <div className="verdict-score-badge">
                                        <RiTrophyLine />
                                        <span>{score}점</span>
                                    </div>

                                    <div className="verdict-card-header">
                                        <div className={`verdict-icon-wrapper ${item.category?.toLowerCase()}`}>
                                            {subjectInfo.icon}
                                        </div>
                                        <div className="verdict-info-col">
                                            <h3 className="verdict-title">{item.title}</h3>
                                            <span className="verdict-topic">{item.topic}</span>
                                        </div>
                                    </div>

                                    <div className="verdict-content-box">
                                        <p>{contentPreview}</p>
                                    </div>

                                    <div className="verdict-tags-row">
                                        <span className="tag-badge subject">
                                            {subjectInfo.icon}
                                            {subjectInfo.label}
                                        </span>
                                        <span className="tag-badge grade">
                                            <RiBookOpenLine />
                                            {getGradeLabel(item.level)}
                                        </span>
                                    </div>

                                    {/* [추가] 구분선 */}
                                    <hr className="verdict-card-divider" />

                                    {/* [추가] 우승자 정보 섹션 */}
                                    <div className="verdict-footer">
                                        <div className="verdict-winner-group">
                                            <div className="winner-icon-box">
                                                <RiVipCrownLine />
                                            </div>
                                            <div className="winner-info-col">
                                                <span className="winner-label">MVP</span>
                                                <div className="winner-name">
                                                    {bestPlayer}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="verdict-date">
                                            {formattedDate}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </section>

            {selectedRoomId && (
                <VerdictDetailModal 
                    roomId={selectedRoomId} 
                    onClose={() => setSelectedRoomId(null)} 
                />
            )}
        </div>
    )
}
export default VerdictsPage