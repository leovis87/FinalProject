import { Link, NavLink, useNavigate } from "react-router-dom"
import Logo from "./Logo"
import { useAuth } from "../contexts/AuthContext"

function Header() {
    const { isAuthenticated, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        if (window.confirm("로그아웃 하시겠습니까?")) {
            logout();
            navigate("/");
        }
    };

    return (
        <div className={`header ${isAuthenticated ? "logged-in" : ""}`}>
            
            <div className="header-left">
                <Link to="/">
                    <Logo />
                </Link>
            </div>

            {isAuthenticated && (
                <nav className="header-center">
                    <NavLink 
                        to="/" 
                        className={({ isActive }) => isActive ? "active" : ""}
                    >
                        탐색
                    </NavLink>
                    <Link to="/nav1">목차1</Link>
                    <Link to="/nav2">목차2</Link>
                </nav>
            )}

            {isAuthenticated && (
                <div className="header-right">
                    <button className="logout-btn" onClick={handleLogout}>
                        로그아웃
                    </button>
                </div>
            )}
        </div>
    )
}
export default Header