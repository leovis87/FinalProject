import { Outlet } from "react-router-dom"
import Header from "./Header"
import Footer from "./Footer"
import NicknameModal from "./modals/NicknameModal"
import { useAuth } from "../contexts/AuthContext"
import "../styles/Layout.css"

function Layout() {
    const { isAuthenticated, user, isLoading } = useAuth();

    if (isLoading) return null; 
    
    const showNicknameModal = isAuthenticated && user && !user.nickname;

    return (
        <div className="layout-container">
            <Header />
            <main>
                <Outlet />
            </main>
            {showNicknameModal && <NicknameModal />}
        </div>
    )
}
export default Layout