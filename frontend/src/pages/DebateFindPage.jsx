import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
    RiSearchLine, 
    RiAddCircleLine, 
    RiFilterLine, 
    RiBookOpenLine,
    RiQuillPenLine,   // 국어
    RiGlobalLine,     // 사회
    RiFlaskLine,      // 과학
    RiScales3Line,    // 도덕
    RiChatQuoteLine,  // 기본
    RiTimerLine,      // 턴 수
    RiGroupLine       // 인원 모드
} from "react-icons/ri";
import { debateApi } from "../api/debateApi";
import { useAuth } from "../contexts/AuthContext"; // [추가] 사용자 정보 확인용
import JoinRoomModal from "../components/modals/JoinRoomModal"; // [추가] 참여 모달
import "../styles/DebateFindPage.css"

function DebateFindPage() {
    const navigate = useNavigate();
    const { user } = useAuth(); // [추가] 현재 로그인한 사용자 가져오기

    const [searchKeyword, setSearchKeyword] = useState("");
    const [selectedSubject, setSelectedSubject] = useState("all");
    const [selectedGrade, setSelectedGrade] = useState("all");

    const [rooms, setRooms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedRoom, setSelectedRoom] = useState(null); // [추가] 선택된 방 상태 관리

    useEffect(() => {
        const fetchRooms = async () => {
            try {
                setLoading(true);
                const response = await debateApi.getDebateRooms();
                setRooms(response.data || response); 
            } catch (error) {
                console.error("토론방 목록을 불러오는데 실패했습니다.", error);
            } finally {
                setLoading(false);
            }
        };

        fetchRooms();
    }, []);

    const filteredRooms = rooms.filter(room => {
        const matchesKeyword = room.topic.includes(searchKeyword) || room.title.includes(searchKeyword);
        const matchesSubject = selectedSubject === 'all' || room.category.toLowerCase() === selectedSubject;
        const matchesGrade = selectedGrade === 'all' || room.level.toLowerCase().replace('_', '') === selectedGrade.replace('_', '');
        return matchesKeyword && matchesSubject && matchesGrade;
    });

    // [추가] 방 클릭 핸들러
    const handleRoomClick = (room) => {
        // 이미 참여중인 방인지 확인
        const isParticipant = room.participants?.some(p => p.user_id === user?.user_id);
        
        if (isParticipant) {
            // 이미 참여자라면 바로 입장
            navigate(`/debate/room/${room.debate_room_id}`);
        } else {
            // 아니면 참여 모달 열기
            setSelectedRoom(room);
        }
    };

    // 과목
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
        return found || { label: category, icon: <RiChatQuoteLine /> };
    };

    // 학년
    const grades = [
        { id: 'all', label: '청소년' },
        { id: 'elementary_low', label: '초등학교 저학년' },
        { id: 'elementary_high', label: '초등학교 고학년' },
        { id: 'middle', label: '중학교' },
        { id: 'high', label: '고등학교' },
    ];

    const getGradeLabel = (level) => {
        const normalized = level?.toLowerCase(); 
        const found = grades.find(g => g.id === normalized || g.id === normalized.replace('_', '')); 
        
        if (found) return found.label;
        
        if (normalized?.includes('elementary')) return '초등학교';
        if (normalized?.includes('middle')) return '중학교';
        if (normalized?.includes('high')) return '고등학교';
        return '전체';
    };

    // 진행 상태
    const getStatusInfo = (status) => {
        switch (status) {
            case 'WAITING': return { label: '대기중', className: 'status-waiting' };
            case 'IN_PROGRESS': return { label: '진행중', className: 'status-progress' };
            case 'FINISHED': return { label: '종료', className: 'status-finished' };
            default: return { label: '대기중', className: 'status-waiting' };
        }
    };

    // 인원 모드
    const getModeLabel = (maxUsers) => {
        const half = Math.floor(maxUsers / 2);
        return `${half}:${half} 토론`;
    };

    return (
        <div className="page-container">
            <section className="find-intro-section">
                <div className="find-banner-card">
                    <div className="find-banner-content">
                        <div className="find-banner-header">
                            <div className="find-banner-icon-box">
                                <RiSearchLine />
                            </div>
                            <h2>토론 주제 선택</h2>
                        </div>
                        <p className="find-banner-desc">
                            관심 있는 주제를 선택하고, 논리적인 대결을 펼쳐보세요.
                        </p>
                        <button 
                            className="create-room-btn"
                            onClick={() => navigate('/create')}
                        >
                            <RiAddCircleLine size={20} />
                            <span>새 토론 방 만들기</span>
                        </button>
                    </div>
                </div>
            </section>

            <section className="find-filter-section">
                <div className="find-filter-card">
                    <div className="filter-search-row">
                        <div className="search-input-box">
                            <RiSearchLine className="search-icon" />
                            <input 
                                type="text" 
                                placeholder="관심있는 토론 주제나 방 제목을 검색해보세요" 
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
                        총 <strong>{filteredRooms.length}</strong>개의 토론 주제가 있습니다.
                    </div>
                </div>
            </section>

            <section className="room-list-section">
                <div className="room-list-card">
                    {loading ? (
                        <div className="loading-state">로딩 중...</div>
                    ) : filteredRooms.length === 0 ? (
                        <div className="empty-state">조건에 맞는 토론방이 없습니다.</div>
                    ): (
                        filteredRooms.map((room) => {
                            const subjectInfo = getSubjectInfo(room.category);
                            const statusInfo = getStatusInfo(room.status);

                            return (
                                <div
                                    key={room.debate_room_id}
                                    className="find-room-item"
                                    onClick={() => handleRoomClick(room)} // [추가] 클릭 이벤트 연결
                                    style={{ cursor: 'pointer' }}         // [추가] 포인터 커서
                                >
                                    <div className={`room-icon-wrapper ${room.category?.toLowerCase()}`}>
                                        {subjectInfo.icon}
                                    </div>

                                    <div className="room-info-content">
                                        <div className="room-header-row">
                                            <h3 className="room-item-title">{room.title}</h3>
                                        </div>
                                        <p className="room-item-topic">{room.topic}</p>
                                        <p className="room-item-desc">{room.topic_description}</p>

                                        <div className="room-tags-row">
                                            <span className="tag-badge subject">
                                                {subjectInfo.icon}
                                                {subjectInfo.label}
                                            </span>

                                            <span className="tag-badge grade">
                                                <RiBookOpenLine />
                                                {getGradeLabel(room.level)}
                                            </span>

                                            <span className="tag-badge turn">
                                                <RiTimerLine />
                                                {room.max_turns}턴
                                            </span>

                                            <span className="tag-badge mode">
                                                <RiGroupLine />
                                                {getModeLabel(room.max_users)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="room-right-action">
                                        <span className={`status-badge ${statusInfo.className}`}>
                                            {statusInfo.label}
                                        </span>
                                    </div>
                                </div>
                            )
                        })
                    )}
                </div>
            </section>

            {/* [추가] 참여 모달 렌더링 */}
            {selectedRoom && (
                <JoinRoomModal 
                    room={selectedRoom} 
                    onClose={() => setSelectedRoom(null)} 
                />
            )}
        </div>
    )
}
export default DebateFindPage