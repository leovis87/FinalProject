import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
    RiCloseLine, 
    RiSearchLine, 
    RiLockPasswordLine, 
    RiEyeLine, 
    RiEyeOffLine,
    RiTimeLine,
    RiUser3Line
} from "react-icons/ri";
import CreateRoomModal from "../modals/CreateRoomModal";
import "../../styles/SlidePanel.css";
import "../../styles/SearchPanel.css";

const LEVEL_OPTIONS = [
    { id: 'all', label: '전체' },
    { id: 'elementary_low', label: '초등 (저)' },
    { id: 'elementary_high', label: '초등 (고)' },
    { id: 'middle', label: '중등' },
    { id: 'high', label: '고등' },
];

const CATEGORY_OPTIONS = [
    { id: 'all', label: '전체' },
    { id: 'korean', label: '국어' },
    { id: 'social', label: '사회' },
    { id: 'moral', label: '도덕' },
    { id: 'ethics', label: '윤리' },
];

function SearchPanel({ isOpen, onClose }) {
    const navigate = useNavigate();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    
    // 필터 상태 관리
    const [selectedLevel, setSelectedLevel] = useState('all');
    const [selectedCategory, setSelectedCategory] = useState('all');
    
    // 검색어 상태 관리
    const [searchQuery, setSearchQuery] = useState('');

    // 토론방 데이터 상태
    const [debateRooms, setDebateRooms] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    // 토론방 목록 불러오기
    useEffect(() => {
        if (isOpen) {
            fetchDebateRooms();
        }
    }, [isOpen]);

    const fetchDebateRooms = async () => {
        setIsLoading(true);
        try {
            const response = await fetch("http://localhost:8000/api/debates/");
            if (response.ok) {
                const data = await response.json();
                setDebateRooms(data);
            } else {
                console.error("토론방 목록 조회 실패");
            }
        } catch (error) {
            console.error("API 호출 오류:", error);
        } finally {
            setIsLoading(false);
        }
    };

    // 필터링
    const filteredRooms = debateRooms.filter(room => {
        // 1. 학년 필터
        if (selectedLevel !== 'all' && room.level !== selectedLevel) return false;
        
        // 2. 카테고리 필터
        if (selectedCategory !== 'all' && room.category !== selectedCategory) return false;
        
        // 3. 검색어 필터 (제목 또는 주제)
        if (searchQuery) {
            const query = searchQuery.toLowerCase().trim();
            const titleMatch = room.title?.toLowerCase().includes(query);
            const topicMatch = room.topic?.toLowerCase().includes(query);
            
            // 제목이나 주제 둘 중 하나라도 포함되어 있지 않으면 제외
            if (!titleMatch && !topicMatch) return false;
        }
        
        return true;
    });

    const handleRoomClick = (roomId) => {
        navigate(`/debate/room/${roomId}`);
        onClose();
    };

    // --- 헬퍼 함수들 ---
    const getStatusInfo = (status) => {
        switch (status) {
            case 'waiting':
                return { label: '대기 중', className: 'waiting' };
            case 'in_progress_intro':
                return { label: '입론 중', className: 'progress' };
            case 'in_progress_rebuttal':
                return { label: '반론 중', className: 'progress' };
            case 'in_progress_rerebuttal':
                return { label: '재반론 중', className: 'progress' };
            case 'in_progress_conclusion':
                return { label: '최종 발언', className: 'progress' };
            case 'in_progress_voting':
                return { label: '평가 중', className: 'voting' };
            case 'finished':
                return { label: '종료', className: 'finished' };
            default:
                return { label: '-', className: 'unknown' };
        }
    };

    const getLevelLabel = (level) => LEVEL_OPTIONS.find(opt => opt.id === level)?.label || level;
    const getCategoryLabel = (cat) => CATEGORY_OPTIONS.find(opt => opt.id === cat)?.label || cat;

    return (
        <div className={`slide-panel-container ${isOpen ? 'open' : ''}`}>
            {/* --- 헤더 영역 --- */}
            <div className="panel-header-area">
                <div>
                    <h2 className="panel-title">토론 찾기</h2>
                    <p className="panel-desc">원하는 유형의 토론을 자유롭게 즐겨요.</p>
                    <button className="panel-close-btn" onClick={onClose}>
                        <RiCloseLine size={28} />
                    </button>
                </div>
            </div>

            {/* 메인 컨텐츠 바디 */}
            <div className="panel-content-body no-scroll">
                {/* --- 필터 영역 --- */}
                <div className="debate-filter-area">
                    {/* 학년/난이도 필터 */}
                    <div className="filter-section">
                        <h3 className="filter-title">학년</h3>
                        <div className="filter-card-list">
                            {LEVEL_OPTIONS.map((option) => (
                                <button
                                    key={option.id}
                                    className={`filter-card ${selectedLevel === option.id ? 'active' : ''}`}
                                    onClick={() => setSelectedLevel(option.id)}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* 카테고리 필터 */}
                    <div className="filter-section">
                        <h3 className="filter-title">주제</h3>
                        <div className="filter-card-list">
                            {CATEGORY_OPTIONS.map((option) => (
                                <button
                                    key={option.id}
                                    className={`filter-card ${selectedCategory === option.id ? 'active' : ''}`}
                                    onClick={() => setSelectedCategory(option.id)}
                                >
                                    {option.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* --- 검색 및 생성 툴바 --- */}
                <div className="debate-option-tools">
                    <div className="debate-search">
                        <RiSearchLine className="search-icon" />
                        <input 
                            type="text" 
                            placeholder="토론 주제나 방 제목을 검색해보세요" 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <button 
                        className="debate-create-btn"
                        onClick={() => setIsCreateModalOpen(true)}
                    >
                        <span>방 만들기</span>
                    </button>
                </div>

                {/* --- 토론방 목록 --- */}
                <div className="debate-list">
                    {isLoading ? (
                        <div className="empty-state">로딩 중...</div>
                    ) : filteredRooms.length === 0 ? (
                        <div className="empty-state">
                            <p>조건에 맞는 토론방이 없습니다.</p>
                            <p className="sub-text">새로운 토론방을 만들어보세요!</p>
                        </div>
                    ) : (
                        <div className="room-list-container">
                            {filteredRooms.map((room) => {
                                const statusInfo = getStatusInfo(room.status);
                                const currentUsers = room.current_users || 1; 

                                return (
                                    <div
                                        key={room.debate_room_id}
                                        className="debate-room-card"
                                        onClick={() => handleRoomClick(room.debate_room_id)}
                                    >
                                        {/* 1. 왼쪽: 상태, 제목, 논제 */}
                                        <div className="card-section left">
                                            <span className={`status-pill ${statusInfo.className}`}>
                                                {statusInfo.label}
                                            </span>
                                            <h3 className="card-title">{room.title}</h3>
                                            <p className="card-topic">
                                                <span className="topic-label">논제</span> {room.topic}
                                            </p>
                                        </div>

                                        {/* 2. 가운데: 학년, 카테고리 (가로 정렬) */}
                                        <div className="card-section center">
                                            <span className="meta-pill">{getLevelLabel(room.level)}</span>
                                            <span className="meta-pill category">{getCategoryLabel(room.category)}</span>
                                        </div>

                                        {/* 3. 오른쪽: 인원, 턴, 아이콘 */}
                                        <div className="card-section right">
                                            <div className="info-item" title="참여 인원 / 최대 인원">
                                                <RiUser3Line />
                                                <span className="info-text">
                                                    {currentUsers} / {room.max_users}
                                                </span>
                                            </div>

                                            <div className="info-item" title="총 턴 수">
                                                <RiTimeLine />
                                                <span className="info-text">{room.max_turns}턴</span>
                                            </div>

                                            <div className="info-icons">
                                                {room.is_private && (
                                                    <RiLockPasswordLine className="icon-private" title="비공개 방" />
                                                )}
                                                {room.allow_observers ? (
                                                    <RiEyeLine className="icon-observer" title="관전 허용" />
                                                ) : (
                                                    <RiEyeOffLine className="icon-observer disabled" title="관전 불가" />
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            </div>

            {isCreateModalOpen && (
                <CreateRoomModal onClose={() => setIsCreateModalOpen(false)} />
            )}
        </div>
    );
}
export default SearchPanel;