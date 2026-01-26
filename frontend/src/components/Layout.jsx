import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom"; // useLocation 추가
import Header from "./Header";
import Sidebar from "./Sidebar";
import NicknameModal from "./modals/NicknameModal";
import { useAuth } from "../contexts/AuthContext";
import "../styles/Layout.css";

function Layout() {
    const { isAuthenticated, user, isLoading } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false); // 사이드바 상태
    const location = useLocation(); // 현재 경로 확인용

    // 페이지 이동 시 사이드바 자동 닫기 (모바일 UX)
    useEffect(() => {
        setIsSidebarOpen(false);
    }, [location.pathname]);

    if (isLoading) return null; 
    
    const showNicknameModal = isAuthenticated && user && !user.nickname;

    return (
        <div className="layout-container">
            {/* Header에 사이드바 토글 함수 전달 */}
            <Header onMenuClick={() => setIsSidebarOpen(true)} />
            
            <div className="content-wrapper">
                {isAuthenticated && (
                    <>
                        {/* 모바일용 오버레이 (사이드바 열렸을 때 배경 어둡게) */}
                        <div 
                            className={`sidebar-overlay ${isSidebarOpen ? 'active' : ''}`}
                            onClick={() => setIsSidebarOpen(false)}
                        />
                        {/* Sidebar에 상태 및 닫기 함수 전달 */}
                        <Sidebar 
                            isOpen={isSidebarOpen} 
                            onClose={() => setIsSidebarOpen(false)} 
                        />
                    </>
                )}
                
                <main>
                    <Outlet />
                </main>
            </div>
            {showNicknameModal && <NicknameModal />}
        </div>
    );
}
export default Layout;