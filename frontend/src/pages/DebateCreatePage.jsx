import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    RiArrowLeftLine, 
    RiMagicLine,
    RiLock2Line,
    RiEyeLine,
    RiQuillPenLine,   // 국어
    RiGlobalLine,     // 사회
    RiFlaskLine,      // 과학
    RiScales3Line,    // 도덕
    RiChatQuoteLine,  // 기본
    RiBookOpenLine,   // 학년
    RiTimerLine,      // 턴
    RiGroupLine       // 인원
} from "react-icons/ri";
import { debateApi } from '../api/debateApi';
import { useAuth } from '../contexts/AuthContext';
import "../styles/DebateCreatePage.css";
import "../styles/DebateFindPage.css";

function DebateCreatePage() {
    const navigate = useNavigate();
    const { user } = useAuth();

    const [formData, setFormData] = useState({
        title: "",
        category: "korean",
        topic: "",
        topic_description: "",
        level: "all",
        max_users: 2,
        creator_role: "pro", 
        max_turns: 4,
        is_private: false,
        room_password: "",
        allow_observers: false
    });

    const [isTitleInitialized, setIsTitleInitialized] = useState(false);

    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isRecommending, setIsRecommending] = useState(false);
    const [recommendedTopics, setRecommendedTopics] = useState([]);
    const [rejectionInfo, setRejectionInfo] = useState(null);

    useEffect(() => {
        if (user?.nickname && !isTitleInitialized) {
            setFormData(prev => ({
                ...prev,
                title: prev.title ? prev.title : `${user.nickname}님의 토론방`
            }));
            setIsTitleInitialized(true);
        }
    }, [user, isTitleInitialized]);

    const handlePublicToggle = (e) => {
        setFormData(prev => ({
            ...prev,
            is_private: !e.target.checked
        }));
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
        if (error) setError("");
    };

    const handleCountChange = (count) => {
        setFormData(prev => ({ ...prev, max_users: count }));
    };

    const handleRoleChange = (role) => {
        setFormData(prev => ({ ...prev, creator_role: role }));
    };

    const handleAiRecommend = async () => {
        if (!formData.topic.trim()) {
            alert("원하는 주제의 키워드를 '토론 주제' 칸에 먼저 입력해주세요.\n(예: 환경, AI, 동물원)");
            return;
        }

        setIsRecommending(true);
        setError("");
        setRecommendedTopics([]);
        setRejectionInfo(null);

        try {
            const data = await debateApi.getAiRecommendations({
                user_query: formData.topic,
                level: formData.level,
                subject: formData.category,
                n_topics: 3
            });

            if (data.mode === 'REJECTED') {
                setRejectionInfo({
                    reason: data.reason_ko,
                    examples: data.examples_ko || []
                });
            } else if (data.topics?.length > 0) {
                setRecommendedTopics(data.topics);
            } else {
                alert("적절한 주제를 찾지 못했습니다.");
            }
        } catch (err) {
            console.error(err);
            alert("주제 추천 중 오류가 발생했습니다.");
        } finally {
            setIsRecommending(false);
        }
    };

    const selectRecommendedTopic = (recTopic) => {
        setFormData(prev => ({
            ...prev,
            topic: recTopic.topic_text,
            topic_description: recTopic.one_line_context
        }));
        setRecommendedTopics([]);
    };

    const handleRejectionExampleClick = (example) => {
        setFormData(prev => ({
            ...prev,
            topic: example
        }));
        setRejectionInfo(null);
    };

    const validateForm = () => {
        if (!formData.title.trim()) return "방 제목을 입력해주세요.";
        if (!formData.topic.trim()) return "토론 주제를 입력해주세요.";
        if (!formData.topic_description.trim()) return "주제 설명을 입력해주세요.";
        if (formData.is_private && !formData.room_password) return "비공개 방은 비밀번호가 필요합니다.";
        if (formData.is_private && formData.room_password.length < 4) return "비밀번호는 4자리여야 합니다.";
        return null;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const validationError = validateForm();
        if (validationError) {
            setError(validationError);
            return;
        }

        if (isSubmitting) return;
        setIsSubmitting(true);

        try {
            const data = await debateApi.createRoom(formData);
            alert("토론방이 생성되었습니다!");
            navigate(`/debate/room/${data.debate_room_id}`, { replace: true });
        } catch (err) {
            const errorMsg = err.response?.data?.detail || "토론방 생성 실패";
            setError(Array.isArray(errorMsg) ? JSON.stringify(errorMsg) : errorMsg);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancel = () => {
        navigate(-1);
    };

    // --- 미리보기 헬퍼 함수 ---
    const getSubjectInfo = (category) => {
        switch(category) {
            case 'korean': return { label: '국어', icon: <RiQuillPenLine /> };
            case 'social': return { label: '사회', icon: <RiGlobalLine /> };
            case 'science': return { label: '과학', icon: <RiFlaskLine /> };
            case 'moral': return { label: '도덕', icon: <RiScales3Line /> };
            default: return { label: '기타', icon: <RiChatQuoteLine /> };
        }
    };

    const getGradeLabel = (level) => {
        switch(level) {
            case 'elementary_low': return '초등 저학년';
            case 'elementary_high': return '초등 고학년';
            case 'middle': return '중학교';
            case 'high': return '고등학교';
            default: return '청소년';
        }
    };

    const getModeLabel = (maxUsers) => {
        const half = Math.floor(maxUsers / 2);
        return `${half}:${half} 토론`;
    };

    const previewSubject = getSubjectInfo(formData.category);

    return (
        <div className="create-container">
            <div className="create-header">
                <div className="create-header-content">
                    <button
                    className="back-btn"
                        onClick={handleCancel}
                        title="이전으로 가기"
                    >
                        <RiArrowLeftLine />
                    </button>
                    <div className="header-titles">
                        <h2 className="create-title">토론방 만들기</h2>
                        <p className="create-subtitle">나만의 토론방을 만들어보세요</p>
                    </div>
                </div>
            </div>

            <div className="create-body">
                <form className="create-card">
                    <div className="form-section">
                        <div className="form-group">
                            <label>방 제목 *</label>
                            <input
                                type="text"
                                name="title"
                                value={formData.title}
                                onChange={handleChange}
                                placeholder="예: 토론 매너 지켜주세요!"
                                autoFocus
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group half">
                                <label>학년 *</label>
                                <select name="level" value={formData.level} onChange={handleChange}>
                                    <option value="all">청소년</option>
                                    <option value="elementary_low">초등학교 저학년</option>
                                    <option value="elementary_high">초등학교 고학년</option>
                                    <option value="middle">중학교</option>
                                    <option value="high">고등학교</option>
                                </select>
                            </div>

                            <div className="form-group half">
                                <label>카테고리 *</label>
                                <select name="category" value={formData.category} onChange={handleChange}>
                                    <option value="korean">국어</option>
                                    <option value="social">사회</option>
                                    <option value="science">과학</option>
                                    <option value="moral">도덕</option>
                                </select>
                            </div>
                        </div>

                        <div className="form-group">
                            <div className="label-row">
                                <label>토론 주제 *</label>
                                <button type="button" className="ai-btn" onClick={handleAiRecommend} disabled={isRecommending}>
                                    <RiMagicLine /> {isRecommending ? "생성 중..." : "AI 추천받기"}
                                </button>
                            </div>
                            <input
                                type="text"
                                name="topic"
                                value={formData.topic}
                                onChange={handleChange}
                                placeholder="주제 키워드를 입력하거나 AI에게 추천 받아보세요."
                            />
                            {recommendedTopics.length > 0 && (
                                <div className="ai-recommend-box">
                                    {recommendedTopics.map((item, i) => (
                                        <div key={i} className="ai-topic-item" onClick={() => selectRecommendedTopic(item)}>
                                            <strong>{item.topic_text}</strong>
                                            <span>{item.one_line_context}</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {rejectionInfo && (
                                <div className="ai-rejection-box" style={{ marginTop: '12px', padding: '12px', backgroundColor: '#fff5f5', borderRadius: '8px', border: '1px solid #feb2b2' }}>
                                    <div style={{ color: '#c53030', fontWeight: '600', marginBottom: '8px', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <RiLock2Line />
                                        <span>{rejectionInfo.reason}</span>
                                    </div>
                                    {rejectionInfo.examples && rejectionInfo.examples.length > 0 && (
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                                            <span style={{ fontSize: '0.85rem', color: '#742a2a' }}>추천 검색어:</span>
                                            {rejectionInfo.examples.map((ex, idx) => (
                                                <button
                                                    key={idx}
                                                    type="button"
                                                    onClick={() => handleRejectionExampleClick(ex)}
                                                    style={{
                                                        padding: '4px 10px',
                                                        backgroundColor: 'white',
                                                        border: '1px solid #fc8181',
                                                        borderRadius: '15px',
                                                        color: '#c53030',
                                                        fontSize: '0.85rem',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s'
                                                    }}
                                                >
                                                    {ex}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className="form-group">
                            <label>주제 설명</label>
                            <textarea
                                name="topic_description"
                                value={formData.topic_description}
                                onChange={handleChange}
                                placeholder="참가자들이 주제를 이해할 수 있도록 배경을 설명해주세요."
                                rows={3}
                            />
                        </div>

                        <div className="form-divider" />

                        <div className="form-group">
                            <label>토론 인원</label>
                            <div className="btn-group">
                                {[2, 4, 6].map(num => (
                                    <button
                                        key={num}
                                        type="button"
                                        className={`select-btn ${formData.max_users === num ? 'active' : ''}`}
                                        onClick={() => handleCountChange(num)}
                                    >
                                        {num/2}:{num/2}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="form-group">
                            <label>나의 입장</label>
                            <div className="btn-group">
                                <button
                                    type="button"
                                    className={`select-btn pro ${formData.creator_role === 'pro' ? 'active' : ''}`}
                                    onClick={() => handleRoleChange('pro')}
                                >
                                    찬성
                                </button>
                                <button
                                    type="button"
                                    className={`select-btn con ${formData.creator_role === 'con' ? 'active' : ''}`}
                                    onClick={() => handleRoleChange('con')}
                                >
                                    반대
                                </button>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>진행 턴 수</label>
                            <select name="max_turns" value={formData.max_turns} onChange={handleChange}>
                                <option value="4">4 턴 (짧게)</option>
                                <option value="6">6 턴 (보통)</option>
                                <option value="8">8 턴 (길게)</option>
                            </select>
                        </div>

                        <div className="form-divider" />

                        {/* --- 설정 토글 영역 --- */}
                        <div className="toggle-cards-container">
                            <div className={`toggle-card ${!formData.is_private ? 'active' : ''}`}>
                                <div className="toggle-card-info">
                                    <div className="toggle-icon-box">
                                        <RiLock2Line />
                                    </div>
                                    <div className="toggle-text-group">
                                        <span className="toggle-title">공개 여부</span>
                                        <span className="toggle-desc">
                                            {formData.is_private 
                                                ? "비공개 시 비밀번호를 입력해야 입장 가능합니다" 
                                                : "공개 시 모든 사용자가 입장 가능합니다"}
                                        </span>
                                    </div>
                                </div>
                                <label className="custom-switch">
                                    <input 
                                        type="checkbox" 
                                        checked={!formData.is_private} 
                                        onChange={handlePublicToggle}
                                    />
                                    <span className="slider round"></span>
                                </label>
                            </div>

                            {formData.is_private && (
                                <div className="password-input-area animate-in">
                                    <input
                                        type="password"
                                        name="room_password"
                                        value={formData.room_password}
                                        onChange={handleChange}
                                        placeholder="입장 비밀번호 숫자 4자리를 입력해주세요"
                                        maxLength={4}
                                    />
                                </div>
                            )}

                            <div className={`toggle-card ${formData.allow_observers ? 'active' : ''}`}>
                                <div className="toggle-card-info">
                                    <div className="toggle-icon-box">
                                        <RiEyeLine />
                                    </div>
                                    <div className="toggle-text-group">
                                        <span className="toggle-title">관전 허용</span>
                                        <span className="toggle-desc">
                                            다른 사용자가 토론을 관전할 수 있습니다
                                        </span>
                                    </div>
                                </div>
                                <label className="custom-switch">
                                    <input 
                                        type="checkbox" 
                                        name="allow_observers"
                                        checked={formData.allow_observers}
                                        onChange={handleChange}
                                    />
                                    <span className="slider round"></span>
                                </label>
                            </div>
                        </div>

                        {/* --- 미리보기 섹션 --- */}
                        <div className="preview-section animate-in">
                            <h3 className="preview-label">목록 미리보기</h3>
                            <div className="room-list-card">
                                <div className="find-room-item" style={{ borderBottom: 'none', cursor: 'default' }}>
                                    <div className={`room-icon-wrapper ${formData.category}`}>
                                        {previewSubject.icon}
                                    </div>

                                    <div className="room-info-content">
                                        <div className="room-header-row">
                                            <h3 className="room-item-title">{formData.title || "방 제목 예시"}</h3>
                                        </div>
                                        <p className="room-item-topic">{formData.topic || "토론 주제"}</p>
                                        <p className="room-item-desc">{formData.topic_description || "주제에 대한 설명이 여기에 표시됩니다."}</p>

                                        <div className="room-tags-row">
                                            <span className="tag-badge subject">
                                                {previewSubject.icon}
                                                {previewSubject.label}
                                            </span>

                                            <span className="tag-badge grade">
                                                <RiBookOpenLine />
                                                {getGradeLabel(formData.level)}
                                            </span>

                                            <span className="tag-badge turn">
                                                <RiTimerLine />
                                                {formData.max_turns}턴
                                            </span>

                                            <span className="tag-badge mode">
                                                <RiGroupLine />
                                                {getModeLabel(formData.max_users)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="room-right-action">
                                        <span className="status-badge status-waiting">
                                            대기중
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {error && <p className="error-text" style={{color: '#e74c3c', marginTop: '20px', textAlign: 'center'}}>{error}</p>}

                        <div className="create-footer-actions" style={{marginTop: '30px', display: 'flex', gap: '12px'}}>
                            <button type="button" onClick={handleCancel} className="footer-btn cancel">취소</button>
                            <button type="submit" className="footer-btn submit" onClick={handleSubmit} disabled={isSubmitting}>
                                {isSubmitting ? "생성 중..." : "방 생성하기"}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default DebateCreatePage;