import { NavLink } from "react-router-dom";
import { RiHome4Line, RiUser3Line, RiDashboardLine } from "react-icons/ri";
import { useAuth } from "../contexts/AuthContext";
import Avatar from "./Avatar";
import "../styles/Sidebar.css";

function Sidebar() {
    const { user } = useAuth();

    const maxExp = user?.next_level_exp || 100;
    const currentExp = user?.exp || 0;
    const expPercentage = Math.min((currentExp / maxExp) * 100, 100);

    return (
        <div className="sidebar">
            {/* 유저 정보 카드 영역 */}
            <div className="user-info-card">
                {user ? (
                    <>
                        <div className="user-profile-row">
                            <div className="sidebar-avatar">
                                <Avatar seed={user.nickname} />
                            </div>
                            <div className="sidebar-profile-text">
                                <div className="sidebar-nickname">{user.nickname}</div>
                                <div className="sidebar-level-badge">
                                    Lv. {user.level || 1}
                                </div>
                            </div>
                        </div>
                        <div className="sidebar-xp-container">
                            <div className="sidebar-xp-header">
                                <span>EXP</span>
                                <span>{currentExp} / {maxExp}</span>
                            </div>
                            <div className="sidebar-xp-track">
                                <div 
                                    className="sidebar-xp-fill" 
                                    style={{ width: `${expPercentage}%` }}
                                ></div>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="sidebar-loading">로그인 정보 로딩 중...</div>
                )}
            </div>

            <nav className="sidebar-menu">
                <NavLink
                    to="/"
                    className={({ isActive }) => isActive ? "menu-item active" : "menu-item"}
                    end
                >
                    <span className="menu-icon"><RiHome4Line /></span>
                    <span>홈</span>
                </NavLink>
                <NavLink 
                    to="/find"
                    className={({ isActive }) => isActive ? "menu-item active" : "menu-item"}
                >
                    <span className="menu-icon"><RiUser3Line /></span>
                    <span>토론 찾기</span>
                </NavLink>
                <NavLink 
                    to="/verdicts"
                    className={({ isActive }) => isActive ? "menu-item active" : "menu-item"}
                >
                    <span className="menu-icon"><RiUser3Line /></span>
                    <span>우수 판결문</span>
                </NavLink>
                <NavLink 
                    to="/mypage" 
                    className={({ isActive }) => isActive ? "menu-item active" : "menu-item"}
                >
                    <span className="menu-icon"><RiUser3Line /></span>
                    <span>마이페이지</span>
                </NavLink>
                <NavLink to="/history" className="menu-item">
                    <span className="menu-icon"><RiDashboardLine /></span>
                    <span>기록 보관소</span>
                </NavLink> 
            </nav>
        </div>
    )
}
export default Sidebar