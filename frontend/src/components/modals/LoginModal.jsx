import { useState, useEffect } from "react";
import { RiKakaoTalkFill, RiCloseLine } from "react-icons/ri";
import { SiNaver } from "react-icons/si";
import { useAuth } from "../../contexts/AuthContext";
import Logo from "../Logo";
import "../../styles/Modal.css"

function LoginModal({ onClose }) {
    const { login } = useAuth();
    const [testUsers, setTestUsers] = useState([]);

    // 모달이 열릴 때 테스트 유저 목록 불러오기
    useEffect(() => {
        const fetchTestUsers = async () => {
            try {
                const response = await fetch("/api/users/test-users");
                if (response.ok) {
                    const data = await response.json();
                    setTestUsers(data);
                }
            } catch (error) {
                console.error("테스트 유저 목록 조회 실패:", error);
            }
        };
        fetchTestUsers();
    }, []);

    const handleSocialLogin = (provider) => {
        window.location.href = `/api/users/login/${provider}`
    }

    // 테스트 계정 선택 시 로그인 처리
    const handleTestLogin = async (e) => {
        const email = e.target.value;
        if (!email) return;

        try {
            const response = await fetch("/api/users/login/test", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email }),
            });

            if (response.ok) {
                const data = await response.json();
                login(data.access_token);
                onClose();
            } else {
                alert("테스트 로그인 실패");
            }
        } catch (error) {
            console.error("로그인 오류:", error);
            alert("로그인 중 오류가 발생했습니다.");
        }
    };

    const handleContentClick = (e) => {
        e.stopPropagation();
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={handleContentClick}>
                <button className="modal-close-btn" onClick={onClose}>
                    <RiCloseLine size={24} />
                </button>
                
                <div className="modal-body">
                    <div className="modal-logo-wrapper">
                        <Logo />
                        <div className="logo-divider"></div>
                    </div>

                    <div className="modal-inner-content">
                        <h2 className="modal-title">환영합니다!</h2>
                        <p className="modal-desc">SNS 계정으로 간편하게 시작하세요</p>
                        
                        <div className="social-login-area">
                            <button
                                className="social-btn kakao-btn"
                                onClick={() => handleSocialLogin('kakao')}
                            >
                                <RiKakaoTalkFill size={20} /> 카카오 로그인
                            </button>
                            <button
                                className="social-btn naver-btn"
                                onClick={() => handleSocialLogin('naver')}
                            >
                                <SiNaver size={18} /> 네이버 로그인
                            </button>

                            {/* 테스트 계정 선택 박스 */}
                            {testUsers.length > 0 && (
                                <div style={{ width: '100%' }}>
                                    <select
                                        className="social-btn"
                                        onChange={handleTestLogin}
                                        defaultValue=""
                                        style={{
                                            backgroundColor: '#f1f3f5',
                                            color: '#495057',
                                            border: '1px solid #dee2e6',
                                            textAlign: 'center',
                                            justifyContent: 'center',
                                            cursor: 'pointer',
                                            appearance: 'none',
                                            WebkitAppearance: 'none'
                                        }}
                                    >
                                        <option value="" disabled>테스트 계정 로그인</option>
                                        {testUsers.map((user) => (
                                            <option key={user.user_id} value={user.email}>
                                                {user.nickname || user.name} ({user.email})
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}
                        </div>

                        <p className="login-agreement">
                            로그인이 이루어지면 DebateHigh가 공지하는 
                            서비스 이용약관 및 개인정보 처리방침에 동의하게 됩니다.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
export default LoginModal