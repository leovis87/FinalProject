import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RiArrowLeftLine, RiSparkling2Line } from "react-icons/ri";
import { debateApi } from "../api/debateApi";
import "../styles/VerdictsPage.css"; // 새로 만든 CSS 파일 import

function VerdictsPage() {
    const navigate = useNavigate();
    const [verdicts, setVerdicts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const levelLabels = {
        all: "제한 없음",
        elementary_low: "초등 (저)",
        elementary_high: "초등 (고)",
        middle: "중등",
        high: "고등",
    };
    const categoryLabels = {
        korean: "국어",
        social: "사회",
        moral: "도덕",
        ethics: "윤리",
    };

    useEffect(() => {
        const fetchVerdicts = async () => {
            setIsLoading(true);
            setError("");
            try {
                // 페이지니까 더 많이 불러오기 (예: 20개)
                const response = await debateApi.getPopularVerdicts(20);
                const data = response.data || response; // axios 설정에 따라 data 구조 확인
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

    // 상세 페이지 등으로 이동하는 핸들러 (필요 시 구현)
    const handleCardClick = (roomId) => {
        // navigate(`/verdicts/${roomId}`); // 예시
        console.log("Clicked room:", roomId);
    };

    return (
        <div className="verdicts-page-container">
            {/* 헤더 영역 */}
            <div className="verdicts-page-header">
                <h2 className="verdicts-title">인기 판결문</h2>
                <p className="verdicts-subtitle">
                    AI 배심원이 평가한 우수 토론 판결문을 모아봤습니다.<br/>
                    논리적인 주장과 근거를 확인하고 토론 실력을 키워보세요.
                </p>
            </div>

            {/* 콘텐츠 영역 */}
            <div className="verdicts-grid">
                {isLoading && <div className="state-msg">열심히 불러오는 중... 🏃‍♂️</div>}
                
                {!isLoading && error && <div className="state-msg error">{error}</div>}
                
                {!isLoading && !error && verdicts.length === 0 && (
                    <div className="state-msg">
                        <p>등록된 인기 판결문이 없습니다.</p>
                    </div>
                )}
                
                {!isLoading && verdicts.map((item) => (
                    <article 
                        key={item.debate_room_id} 
                        className="verdict-item-card"
                        onClick={() => handleCardClick(item.debate_room_id)}
                    >
                        <div className="card-top-row">
                            <div className="card-tags">
                                <span className="verdict-tag category">
                                    {categoryLabels[item.category] || item.category}
                                </span>
                                <span className="verdict-tag">
                                    {levelLabels[item.level] || item.level}
                                </span>
                            </div>
                            <div className="card-rating">
                                <RiSparkling2Line />
                                <span>{item.rating ? item.rating.toFixed(1) : "0.0"}</span>
                            </div>
                        </div>
                        
                        <div className="card-content">
                            <h3>{item.title}</h3>
                            <div className="card-topic">
                                {item.topic}
                            </div>
                            {item.summary && (
                                <p className="card-summary">
                                    {item.summary}
                                </p>
                            )}
                        </div>
                    </article>
                ))}
            </div>
        </div>
    );
}

export default VerdictsPage;