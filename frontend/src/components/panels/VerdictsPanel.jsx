import { useEffect, useState } from "react";
import { RiCloseLine, RiSparkling2Line } from "react-icons/ri";
import { debateApi } from "../../api/debateApi";
import "../../styles/SlidePanel.css";
import "../../styles/VerdictsPanel.css";

function VerdictsPanel({ isOpen, onClose }) {
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
        if (!isOpen) return;

        const fetchVerdicts = async () => {
            setIsLoading(true);
            setError("");
            try {
                // debateApi를 사용하여 데이터 조회 (토큰 처리는 axiosClient가 담당)
                const response = await debateApi.getPopularVerdicts(8);
                const data = response.data;
                setVerdicts(Array.isArray(data) ? data : []);
            } catch (err) {
                console.error(err);
                setError("판결문 목록을 불러오지 못했습니다.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchVerdicts();
    }, [isOpen]);

    if (!isOpen) {
        return null;
    }

    return (
        <div className="verdicts-modal-overlay">
            <button type="button" className="verdicts-modal-backdrop" onClick={onClose} aria-label="닫기" />
            <div className="verdicts-modal">
                <div className="panel-header-area sub">
                    <h2 className="panel-title">판결문</h2>
                    <p className="panel-desc">관심있는 토론의 판결문을 확인해 보세요.</p>
                    <button className="panel-close-btn" onClick={onClose}>
                        <RiCloseLine size={28} />
                    </button>
                </div>
                <div className="panel-content-body verdicts-body">
                    {isLoading && (
                        <div className="verdicts-state">불러오는 중...</div>
                    )}
                    {!isLoading && error && (
                        <div className="verdicts-state error">{error}</div>
                    )}
                    {!isLoading && !error && verdicts.length === 0 && (
                        <div className="verdicts-state">표시할 인기 판결문이 없습니다.</div>
                    )}
                    {!isLoading && !error && verdicts.length > 0 && (
                        <div className="verdicts-list">
                            {verdicts.map((item) => (
                                <article key={item.debate_room_id} className="verdict-card">
                                    <div className="verdict-card-main">
                                        <div className="verdict-card-title">{item.title}</div>
                                        <div className="verdict-card-topic">{item.topic}</div>
                                        {item.summary && (
                                            <p className="verdict-card-summary">{item.summary}</p>
                                        )}
                                        <div className="verdict-card-meta">
                                            <span className="verdict-pill">{categoryLabels[item.category] || item.category}</span>
                                            <span className="verdict-pill">{levelLabels[item.level] || item.level}</span>
                                        </div>
                                    </div>
                                    <div className="verdict-score">
                                        <RiSparkling2Line />
                                        <span>{item.rating.toFixed(1)}</span>
                                        <small>AI 평점</small>
                                    </div>
                                </article>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default VerdictsPanel
