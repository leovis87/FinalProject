import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { RiTrophyLine, RiStarLine, RiFlashlightLine, RiMenuLine } from "react-icons/ri"; // RiMenuLine 추가
import Logo from "./Logo";

// onMenuClick props 추가
function Header({ onMenuClick }) {
    const { isAuthenticated, user } = useAuth();

    return (
        <header className={`header ${isAuthenticated ? "logged-in": ""}`}>
            {isAuthenticated ? (
                // 로그인 상태
                <>
                    <div className="header-left-group">
                        {/* 모바일 메뉴 버튼 (CSS로 제어) */}
                        <button className="mobile-menu-btn" onClick={onMenuClick}>
                            <RiMenuLine />
                        </button>
                        <Link to="/">
                            <Logo />
                        </Link>
                    </div>

                    <div className="header-right-tools">
                        <div className="header-badge level">
                            <RiStarLine className="header-badge-icon" />
                            <span className="badge-text">레벨 {user?.level || 1}</span>
                        </div>

                        <div className="header-badge xp">
                            <RiFlashlightLine className="header-badge-icon" />
                            <span className="badge-text">{user?.exp || 0} XP</span>
                        </div>

                        <div className="header-badge win">
                            <RiTrophyLine className="header-badge-icon" />
                            <span className="badge-text">{user?.win_count || 0} 승</span>
                        </div>
                    </div>
                </>
            ) : (
                // 비로그인 상태
                <div>
                    <Logo />
                </div>
            )}
        </header>
    )
}

export default Header;