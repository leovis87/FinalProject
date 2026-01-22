import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RiCloseLine, RiTeamFill } from "react-icons/ri";
import "../../styles/Modal.css";

function JoinRoomModal({ room, onClose }) {
    const navigate = useNavigate();
    const [isSubmitting, setIsSubmitting] = useState(false);

    const proTeamCount = room.participants.filter(p => p.role === "pro").length;
    const conTeamCount = room.participants.filter(p => p.role === "con").length;
    const maxTeamSize = room.max_users / 2;

    const handleJoin = async (role) => {
        if (isSubmitting) return;
        setIsSubmitting(true);

        try {
            // 관전자 입장
            if (role === 'observer') {
                navigate(`/debate/room/${room.debate_room_id}`);
                onClose();
                return;
            }

            // 참가자 입장
            const token = localStorage.getItem("access_token");
            const response = await fetch(`http://61.40.108.149:8000/api/debates/${room.debate_room_id}/join?role=${role}`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (response.ok) {
                alert("참가되었습니다!");
                navigate(`/debate/room/${room.debate_room_id}`);
                onClose();
            } else {
                const err = await response.json();
                alert(err.detail || "참가 실패");
            }
        } catch (err) {
            console.error(err);
            alert("서버 통신 오류");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ width: '500px' }}>
                <button className="modal-close-btn" onClick={onClose}>
                    <RiCloseLine size={24} />
                </button>

                <div className="modal-body">
                    <h2 className="modal-title" style={{ marginBottom: '10px' }}>{room.title}</h2>
                    <p className="modal-desc">참가할 진영을 선택해주세요.</p>

                    <div style={{ display: 'flex', gap: '20px', width: '100%', marginBottom: '30px' }}>
                        {/* 찬성 버튼 */}
                        <button 
                            className="social-btn"
                            style={{ backgroundColor: '#eff6ff', color: '#1e40af', border: '1px solid #dbeafe', flexDirection: 'column', padding: '20px', height: 'auto', gap: '10px' }}
                            onClick={() => handleJoin('pro')}
                            disabled={proTeamCount >= maxTeamSize}
                        >
                            <div style={{ fontSize: '18px', fontWeight: '800' }}>찬성</div>
                            <div style={{ fontSize: '14px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <RiTeamFill /> {proTeamCount} / {maxTeamSize}
                            </div>
                            {proTeamCount >= maxTeamSize && <span style={{fontSize: '12px', color: '#ef4444'}}>(만원)</span>}
                        </button>

                        {/* 반대 버튼 */}
                        <button 
                            className="social-btn"
                            style={{ backgroundColor: '#fef2f2', color: '#b91c1c', border: '1px solid #fee2e2', flexDirection: 'column', padding: '20px', height: 'auto', gap: '10px' }}
                            onClick={() => handleJoin('con')}
                            disabled={conTeamCount >= maxTeamSize}
                        >
                            <div style={{ fontSize: '18px', fontWeight: '800' }}>반대</div>
                            <div style={{ fontSize: '14px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                <RiTeamFill /> {conTeamCount} / {maxTeamSize}
                            </div>
                            {conTeamCount >= maxTeamSize && <span style={{fontSize: '12px', color: '#ef4444'}}>(만원)</span>}
                        </button>
                    </div>

                    {/* 관전 버튼 (옵션) */}
                    {(room.allow_observers || proTeamCount + conTeamCount >= room.max_users) && (
                        <button 
                            onClick={() => handleJoin('observer')}
                            style={{ background: 'none', border: 'none', color: '#666', textDecoration: 'underline', cursor: 'pointer' }}
                        >
                            그냥 구경만 할래요 (관전 입장)
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

export default JoinRoomModal;