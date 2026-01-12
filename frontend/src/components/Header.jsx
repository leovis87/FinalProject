import { Link, useNavigate } from "react-router-dom"
import Logo from "./Logo"
import { useAuth } from "../contexts/AuthContext"

function Header() {
    const { isAuthenticated, logout, user } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        if (window.confirm("로그아웃 하시겠습니까?")) {
            logout();
            navigate("/");
        }
    };

    return (
        <div className={`header ${isAuthenticated ? "logged-in" : ""}`}>
            {isAuthenticated ? (
                <>
                    <div className="header-left">
                        <div className="user-nickname-display">
                            <span className="welcome-text">Welcome, </span>
                            <span className="nickname-text">{user?.nickname || "Guest"}</span>
                        </div>
                    </div>

                    <div className="header-right">
                        <button className="logout-btn" onClick={handleLogout}>
                            로그아웃
                        </button>
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