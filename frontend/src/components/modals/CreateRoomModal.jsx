import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import "../../styles/CreateRoomModal.css"

function CreateRoomModal({ onClose }) {
    const navigate = useNavigate();

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

    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // AI 추천 관련 상태
    const [isRecommending, setIsRecommending] = useState(false);
    const [recommendedTopics, setRecommendedTopics] = useState([]);

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

    // 주제 추천 요청 함수
    const handleAiRecommend = async () => {
        if (!formData.topic.trim()) {
            alert("원하는 주제의 키워드를 '토론 주제' 칸에 먼저 입력해주세요.\n(예: 환경, AI, 동물원)");
            return;
        }

        setIsRecommending(true);
        setError("");
        setRecommendedTopics([]);

        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("/rag/topics/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    user_query: formData.topic,   // 사용자가 입력한 키워드
                    level: formData.level,        // 선택된 학년/난이도
                    subject: formData.category,   // 선택된 카테고리
                    n_topics: 3                   // 추천받을 주제 개수
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.topics && data.topics.length > 0) {
                    setRecommendedTopics(data.topics);
                } else {
                    alert("적절한 토론 주제를 찾지 못했습니다. 다른 키워드로 시도해보세요.");
                }
            } else {
                console.error("AI Recommendation failed");
                alert("주제 추천 중 오류가 발생했습니다.");
            }
        } catch (err) {
            console.error(err);
            alert("서버 통신 오류가 발생했습니다.");
        } finally {
            setIsRecommending(false);
        }
    };

    // 추천된 주제 선택 시 폼에 적용
    const selectRecommendedTopic = (recTopic) => {
        setFormData(prev => ({
            ...prev,
            topic: recTopic.topic_text,
            topic_description: recTopic.one_line_context
        }));
        setRecommendedTopics([]);
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

        if (isSubmitting) return; // 중복 제출 방지
        setIsSubmitting(true);

        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("/api/debates/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const data = await response.json();
                alert("토론방이 생성되었습니다!");
                onClose();
                navigate(`/debate/room/${data.debate_room_id}`);
            } else {
                const errData = await response.json();
                if (Array.isArray(errData.detail)) {
                    const errorMsg = errData.detail.map(err =>
                        `${err.loc[err.loc.length - 1]}: ${err.msg}"`
                    ).join('\n');
                    setError(errorMsg);
                } else {
                    setError(errData.detail || "토론방 생성에 실패했습니다.");
                }
            }
        } catch (err) {
            console.error(err);
            setError("서버 오류가 발생했습니다.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return createPortal(
        <div className="create-modal-overlay">
            <div className="create-modal" onClick={e => e.stopPropagation()}>
                <div className="create-modal-header">
                    <h3 className="create-modal-title">방 만들기</h3>
                </div>
                
                <form onSubmit={handleSubmit} className="create-room-form">
                    <div className="form-scroll-area">
                        <div className="form-columns">
                            {/* --- 왼쪽 컬럼 --- */}
                            <div className="form-column left">
                                {/* 방 제목 */}
                                <div className="create-form-group">
                                    <label>방 제목</label>
                                    <input
                                        type="text"
                                        name="title"
                                        value={formData.title}
                                        onChange={handleChange}
                                        placeholder="토론방 제목을 입력하세요"
                                        autoFocus
                                    />
                                </div>

                                {/* 학년/난이도 */}
                                <div className="create-form-group">
                                    <label>학년/난이도</label>
                                    <select name="level" value={formData.level} onChange={handleChange}>
                                        <option value="all">제한 없음</option>
                                        <option value="elementary_low">초등 (저)</option>
                                        <option value="elementary_high">초등 (고)</option>
                                        <option value="middle">중등</option>
                                        <option value="high">고등</option>
                                    </select>
                                </div>

                                {/* 카테고리 */}
                                <div className="create-form-group">
                                    <label>카테고리</label>
                                    <select name="category" value={formData.category} onChange={handleChange}>
                                        <option value="korean">국어</option>
                                        <option value="social">사회</option>
                                        <option value="moral">도덕</option>
                                        <option value="ethics">윤리</option>
                                    </select>
                                </div>

                                {/* 토론 주제 + AI 추천 버튼 */}
                                <div className="create-form-group">
                                    <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        토론 주제
                                        <button 
                                            type="button" 
                                            className="ai-recommend-btn"
                                            onClick={handleAiRecommend}
                                            disabled={isRecommending}
                                            style={{ 
                                                fontSize: '0.8rem', 
                                                padding: '2px 8px', 
                                                cursor: 'pointer',
                                                backgroundColor: isRecommending ? '#ccc' : '#6c5ce7',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px'
                                            }}
                                        >
                                            {isRecommending ? "생성 중..." : "✨ AI에게 주제를 추천 받아보세요"}
                                        </button>
                                    </label>
                                    <input
                                        type="text"
                                        name="topic"
                                        value={formData.topic}
                                        onChange={handleChange}
                                        placeholder="키워드를 입력하고 추천 버튼을 눌러보세요"
                                    />
                                    
                                    {/* 추천 목록 표시 영역 */}
                                    {recommendedTopics.length > 0 && (
                                        <div className="recommendation-list" style={{ 
                                            marginTop: '8px', 
                                            border: '1px solid #ddd', 
                                            borderRadius: '4px',
                                            padding: '8px',
                                            backgroundColor: '#f8f9fa'
                                        }}>
                                            <p style={{ fontSize: '0.8rem', color: '#666', marginBottom: '4px' }}>
                                                💡 추천된 주제 (클릭하여 적용)
                                            </p>
                                            {recommendedTopics.map((item, idx) => (
                                                <div 
                                                    key={idx} 
                                                    onClick={() => selectRecommendedTopic(item)}
                                                    style={{
                                                        padding: '6px',
                                                        borderBottom: idx < recommendedTopics.length - 1 ? '1px solid #eee' : 'none',
                                                        cursor: 'pointer',
                                                        fontSize: '0.9rem'
                                                    }}
                                                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#eef2ff'}
                                                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                                >
                                                    <strong>{item.topic_text}</strong>
                                                    <div style={{ fontSize: '0.8rem', color: '#555', marginTop: '2px' }}>
                                                        {item.one_line_context}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* 주제 설명 */}
                                <div className="create-form-group textarea-group">
                                    <label>주제 설명</label>
                                    <textarea 
                                        name="topic_description"
                                        value={formData.topic_description}
                                        onChange={handleChange}
                                        placeholder="주제 선택 시 자동 완성되거나 직접 입력하세요"
                                        rows={3}
                                    />
                                </div>
                            </div>

                            {/* --- 오른쪽 컬럼 --- */}
                            <div className="form-column right">
                                {/* 토론 인원 */}
                                <div className="create-form-group">
                                    <label>토론 인원</label>
                                    <div className="selection-group">
                                        <button 
                                            type="button" 
                                            className={`selection-btn ${formData.max_users === 2 ? 'selected' : ''}`}
                                            onClick={() => handleCountChange(2)}
                                        >
                                            1 : 1
                                        </button>
                                        <button 
                                            type="button" 
                                            className={`selection-btn ${formData.max_users === 4 ? 'selected' : ''}`}
                                            onClick={() => handleCountChange(4)}
                                        >
                                            2 : 2
                                        </button>
                                        <button 
                                            type="button" 
                                            className={`selection-btn ${formData.max_users === 6 ? 'selected' : ''}`}
                                            onClick={() => handleCountChange(6)}
                                        >
                                            3 : 3
                                        </button>
                                    </div>
                                </div>

                                {/* 나의 입장 선택 */}
                                <div className="create-form-group">
                                    <label>나의 입장</label>
                                    <div className="selection-group">
                                        <button 
                                            type="button" 
                                            className={`selection-btn pro-btn ${formData.creator_role === 'pro' ? 'selected' : ''}`}
                                            onClick={() => handleRoleChange('pro')}
                                        >
                                            찬성
                                        </button>
                                        <button 
                                            type="button" 
                                            className={`selection-btn con-btn ${formData.creator_role === 'con' ? 'selected' : ''}`}
                                            onClick={() => handleRoleChange('con')}
                                        >
                                            반대
                                        </button>
                                    </div>
                                </div>

                                {/* 턴 수 */}
                                <div className="create-form-group">
                                    <label>턴 수</label>
                                    <select name="max_turns" value={formData.max_turns} onChange={handleChange}>
                                        <option value="4">4 턴</option>
                                        <option value="6">6 턴</option>
                                        <option value="8">8 턴</option>
                                    </select>
                                </div>

                                {/* 공개 여부 */}
                                <div className="create-form-group row-group">
                                    <label>공개 여부</label>
                                    <label className="text-toggle-switch">
                                        <input 
                                            type="checkbox" 
                                            name="is_private"
                                            checked={formData.is_private}
                                            onChange={handleChange}
                                        />
                                        <span className="toggle-slider" 
                                              data-on="비공개" 
                                              data-off="공개">
                                        </span>
                                    </label>
                                </div>

                                {/* 비밀번호 (비공개 선택 시 노출) */}
                                {formData.is_private && (
                                    <div className="create-form-group animate-slide-down">
                                        <label>비밀번호</label>
                                        <input
                                            type="password"
                                            name="room_password"
                                            value={formData.room_password}
                                            onChange={handleChange}
                                            placeholder="입장 비밀번호 숫자 4자리"
                                            maxLength={4}
                                        />
                                    </div>
                                )}

                                {/* 관전 여부 */}
                                <div className="create-form-group row-group">
                                    <label>관전 여부</label>
                                    <label className="text-toggle-switch observer">
                                        <input 
                                            type="checkbox" 
                                            name="allow_observers"
                                            checked={formData.allow_observers}
                                            onChange={handleChange}
                                        />
                                        <span className="toggle-slider" 
                                              data-on="허용" 
                                              data-off="비허용">
                                        </span>
                                    </label>
                                </div>
                            </div>
                        </div>
                        
                        {/* 에러 메시지 표시 영역 */}
                        {error && (
                            <div style={{ textAlign: 'center', marginTop: '10px' }}>
                                <p className="error-text">{error}</p>
                            </div>
                        )}
                    </div>

                    {/* 하단 버튼 영역 */}
                    <div className="create-modal-footer">
                        <button type="button" onClick={onClose} className="footer-btn cancel">
                            취소
                        </button>
                        <button type="submit" className="footer-btn submit">
                            방 생성하기
                        </button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
}

export default CreateRoomModal;