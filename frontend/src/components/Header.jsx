import { Link, useLocation, useNavigate } from "react-router-dom"
import { RiVipCrown2Fill, RiUserLine, RiHomeLine } from "react-icons/ri";
import { MdLogout } from "react-icons/md";
import Logo from "./Logo"
import { useAuth } from "../contexts/AuthContext"

function Header() {
    const { isAuthenticated, logout, user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        if (window.confirm("로그아웃 하시겠습니까?")) {
            logout();
            navigate("/");
        }
    };

    const isMyPage = location.pathname.startsWith("/mypage");
    const handlePrimaryNav = () => {
        navigate(isMyPage ? "/" : "/mypage");
    };

    const level = user?.level ?? 1;
    const exp = user?.exp ?? 0;
    const requiredXp = 100 + 20 * (level - 1) + 5 * ((level - 1) ** 2);
    const xpPercent = requiredXp > 0 ? Math.min(100, Math.round((exp / requiredXp) * 100)) : 0;

    return (
        <div className={`header ${isAuthenticated ? "logged-in" : ""}`}>
            {isAuthenticated ? (
                <>
                    <div className="header-left-profile">
                        <div className="profile-avatar">
                            <img 
                                src={`https://api.dicebear.com/9.x/notionists/svg?seed=${user?.nickname || 'User'}&backgroundColor=transparent`} 
                                alt="Profile"
                                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }}
                            />
                        </div>
                        <div className="profile-info">
                            <div className="profile-name">{user?.nickname || "Guest"}
                            {user.tier && (
                                <span className={`tier-badge header-tier tier-${user.tier}`}>
                                    {user.tier}
                                </span>
                            )}
                            </div>
                            <div className="level-bar-container">
                                <div className="level-divider"></div>
                                <span className="level-text">레벨 {level}</span>
                                <div className="progress-track">
                                    <div className="progress-fill" style={{ width: `${xpPercent}%` }}></div>
                                    <span className="xp-overlay">{exp} / {requiredXp}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="header-right-tools">
                        <div className="resource-display">
                            <div className="resource-item">
                                <RiVipCrown2Fill color="#a855f7" size={25} />
                                <span className="resource-count" style={{color: '#a855f7'}}>0</span>
                            </div>
                        </div>

                        <div className="icon-actions">
                            <button className="icon-btn" onClick={handlePrimaryNav}>
                                {isMyPage ? <RiHomeLine size={24} /> : <RiUserLine size={24} />}
                            </button>
                            <button className="icon-btn" onClick={handleLogout}><MdLogout size={25} /></button>
                        </div>
                    </div>
                </>
            ) : (
                <Link to="/" className="header-logo-center">
                    <Logo />
                </Link>
            )}
        </div>
    )
}
export default Header
