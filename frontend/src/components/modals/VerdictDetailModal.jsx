import { useEffect, useState } from "react";
import { debateApi } from "../../api/debateApi";
import { 
    RiCloseLine, 
    RiMedalLine, 
    RiTeamLine, 
    RiFileTextLine, 
    RiBarChartFill 
} from "react-icons/ri";
import "../../styles/VerdictDetailModal.css";

function VerdictDetailModal({ roomId, onClose }) {
    const [verdict, setVerdict] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetail = async () => {
            try {
                const response = await debateApi.getDebateVerdict(roomId);
                setVerdict(response.data || response);
            } catch (error) {
                console.error("판결문 상세 조회 실패:", error);
            } finally {
                setLoading(false);
            }
        };
        
        if (roomId) fetchDetail();
    }, [roomId]);

    // 배경 클릭 시 닫기
    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) onClose();
    };

    if (loading) {
        return (
            <div className="modal-overlay" onClick={handleBackdropClick}>
                <div className="verdict-modal-container loading">
                    <div className="spinner"></div>
                    <p>판결문을 분석 정보를 불러오는 중입니다...</p>
                </div>
            </div>
        );
    }

    if (!verdict) return null;

    return (
        <div className="modal-overlay" onClick={handleBackdropClick}>
            <div className="verdict-modal-container">
                <button className="modal-close-btn" onClick={onClose}>
                    <RiCloseLine />
                </button>

                <div className="verdict-modal-header">
                    <div className="modal-title-badge">
                        <RiMedalLine /> AI 최종 판결
                    </div>
                    <h2>토론 분석 결과</h2>
                    <p className="decided-date">
                        판결 일시: {new Date(verdict.decided_at).toLocaleDateString()}
                    </p>
                </div>

                <div className="verdict-modal-body">
                    {/* 1. MVP 선정 */}
                    {verdict.best_player && (
                        <div className="detail-section mvp-section">
                            <div className="section-label"><RiMedalLine /> 오늘의 MVP</div>
                            <div className="mvp-content">
                                <span className="mvp-name">{verdict.best_player}</span>
                                <span className="mvp-desc">님, 논리적인 주장으로 토론을 이끌어주셨습니다! 🏆</span>
                            </div>
                        </div>
                    )}

                    {/* 2. 전체 요약 */}
                    <div className="detail-section">
                        <div className="section-label"><RiFileTextLine /> 토론 전체 요약</div>
                        <div className="summary-box">
                            {verdict.summary || "요약 정보가 없습니다."}
                        </div>
                    </div>

                    {/* 3. 팀별 평가 (찬성/반대) */}
                    <div className="team-eval-grid">
                        <TeamEvalCard team="찬성" data={verdict.pro_eval} type="pro" />
                        <TeamEvalCard team="반대" data={verdict.con_eval} type="con" />
                    </div>
                </div>
            </div>
        </div>
    );
}

function TeamEvalCard({ team, data, type }) {
    if (!data) return null;

    return (
        <div className={`team-eval-card ${type}`}>
            <div className="eval-header">
                <span className="team-badge"><RiTeamLine /> {team} 측</span>
                <span className="total-score">{data.total_score || 0}점</span>
            </div>

            <div className="score-chart">
                <ScoreRow label="주장 명확성" score={data.scores?.clarity} max={25} />
                <ScoreRow label="근거 적합성" score={data.scores?.evidence} max={30} />
                <ScoreRow label="상호작용" score={data.scores?.interaction} max={25} />
                <ScoreRow label="토론 태도" score={data.scores?.attitude} max={20} />
            </div>

            <div className="eval-feedback">
                <strong><RiBarChartFill /> 심사평</strong>
                <p>{data.feedback_text}</p>
            </div>
        </div>
    );
}

function ScoreRow({ label, score = 0, max }) {
    const percent = Math.min(100, (score / max) * 100);
    return (
        <div className="score-row">
            <span className="score-label">{label}</span>
            <div className="progress-bg">
                <div className="progress-fill" style={{ width: `${percent}%` }}></div>
            </div>
            <span className="score-value">{score}</span>
        </div>
    );
}

export default VerdictDetailModal;