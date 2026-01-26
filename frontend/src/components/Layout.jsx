import { Outlet } from "react-router-dom"
import Header from "./Header"
import Sidebar from "./Sidebar"
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
            <div className="content-wrapper">
                {isAuthenticated && <Sidebar />}
                <main>
                    <Outlet />
                </main>
            </div>
            {showNicknameModal && <NicknameModal />}
        </div>
    )
}
export default Layout