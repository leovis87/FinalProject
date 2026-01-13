import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import "../../styles/Modal.css";

function NicknameModal() {
    const [nickname, setNickname] = useState("");
    const [error, setError] = useState("");
    const { updateLocalNickname } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const trimmedNickname = nickname.trim();

        if (!trimmedNickname) {
            setError("닉네임을 입력해주세요.");
            return;
        }

        if (trimmedNickname.length < 2) {
            setError("닉네임은 2글자 이상이어야 합니다.");
            return;
        }

        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("http://localhost:8000/api/users/me/nickname", {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ nickname: trimmedNickname })
            });

            if (response.ok) {
                updateLocalNickname(trimmedNickname);
            } else {
                setError("닉네임 설정에 실패했습니다.");
            }
        } catch (err) {
            console.error(err);
            setError("서버 오류가 발생했습니다.");
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-body">
                    <div className="modal-inner-content">
                        <h2 className="modal-title">닉네임 설정</h2>
                        <p className="modal-desc" style={{ marginBottom: '20px' }}>
                            서비스 이용을 위해 닉네임이 필요합니다.
                        </p>

                        <form onSubmit={handleSubmit} className="nickname-form-area">
                            <input
                                type="text"
                                className="nickname-input"
                                value={nickname}
                                onChange={(e) => {
                                    setNickname(e.target.value);
                                    if (error) setError("");
                                }}
                                placeholder="사용할 닉네임을 입력하세요 (2글자 이상)"
                            />
                            
                            {error && (
                                <p className="error-msg">
                                    {error}
                                </p>
                            )}

                            <button 
                                type="submit" 
                                className="social-btn submit-btn"
                            >
                                시작하기
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default NicknameModal;