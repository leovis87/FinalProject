import { NavLink } from "react-router-dom";
import { RiHome4Line, RiUser3Line, RiDashboardLine, RiCloseLine } from "react-icons/ri"; // RiCloseLine 추가
import { useAuth } from "../contexts/AuthContext";
import Avatar from "./Avatar";
import "../styles/Sidebar.css";

// isOpen, onClose props 추가
function Sidebar({ isOpen, onClose }) {
    const { user } = useAuth();

    const maxExp = user?.next_level_exp || 100;
    const currentExp = user?.exp || 0;
    const expPercentage = Math.min((currentExp / maxExp) * 100, 100);

    return (
        // 모바일 상태 클래스 추가
        <div className={`sidebar ${isOpen ? 'open' : ''}`}>
            
            {/* 모바일용 닫기 버튼 */}
            <button className="sidebar-close-btn" onClick={onClose}>
                <RiCloseLine />
            </button>

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
                                <div className="sidebar-status-row" style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                                    <div className="sidebar-level-badge">
                                        Lv. {user.level || 1}
                                    </div>
                                    {user.equipped_badge && (
                                        <div className="sidebar-equipped-badge" style={{
                                            display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 8px',
                                            borderRadius: '10px', backgroundColor: '#f8fafc', border: '1px solid #cbd5e1',
                                            fontSize: '0.75rem', color: '#475569', fontWeight: '600'
                                        }}>
                                            <span>{user.equipped_badge.icon}</span>
                                            <span>{user.equipped_badge.name}</span>
                                        </div>
                                    )}
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
export default Sidebar;