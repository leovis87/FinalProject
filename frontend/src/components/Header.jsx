import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { RiTrophyLine, RiStarLine, RiFlashlightLine } from "react-icons/ri";
import Logo from "./Logo";

function Header() {
    const { isAuthenticated, user } = useAuth();

    return (
        <header className={`header ${isAuthenticated ? "logged-in": ""}`}>
            {isAuthenticated ? (
                // 로그인 상태
                <>
                    <Link to="/">
                        <Logo />
                    </Link>

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

function getTierClass(tierName) {
    switch(tierName) {
        case "옹알이": return "tier-ong";
        case "입문자": return "tier-beginner";
        case "아마추어": return "tier-amateur";
        case "프로": return "tier-pro";
        case "마스터": return "tier-master";
        default: return "";
    }
}

export default Header