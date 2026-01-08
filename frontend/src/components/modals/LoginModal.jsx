import { RiKakaoTalkFill, RiCloseLine } from "react-icons/ri";
import { SiNaver } from "react-icons/si";
import Logo from "../Logo";
import "../../styles/LoginModal.css"

function LoginModal({ onClose }) {
    const handleSocialLogin = (provider) => {
        window.location.href = `http://localhost:8000/api/users/login/${provider}`
    }

    const handleContentClick = (e) => {
        e.stopPropagation();
    }

    return (
        <div className="lm-overlay" onClick={onClose}>
            <div className="lm-content" onClick={handleContentClick}>
                <button className="modal-close-btn" onClick={onClose}>
                    <RiCloseLine size={24} />
                </button>
                
                <div className="lm-body">
                    <div className="modal-logo-wrapper">
                        <Logo />
                        <div className="logo-divider"></div>
                    </div>

                    <div className="login-wrap">
                        <h2>환영합니다!</h2>
                        <p className="login-desc">SNS 계정으로 간편하게 시작하세요</p>
                        
                        <div className="social-login">
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