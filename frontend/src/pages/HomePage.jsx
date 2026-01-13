import { useState } from "react";
import { MdSearch } from "react-icons/md";
import { FiBookOpen } from "react-icons/fi";
import { useAuth } from "../contexts/AuthContext";
import SearchPanel from "../components/panels/SearchPanel";
import VerdictsPanel from "../components/panels/VerdictsPanel";
import "../styles/HomePage.css";

function HomePage() {
    const { user } = useAuth();
    const [activePanel, setActivePanel] = useState(null);

    const togglePanel = (panelName) => {
        if (activePanel === panelName) {
            setActivePanel(null); // 이미 열려있으면 닫기
        } else {
            setActivePanel(panelName); // 해당 패널 열기
        }
    };

    return (
        <div className="home-container">
            {/* 왼쪽 사이드바 */}
            <div className="sidebar-left">
                <nav className="floating-nav">
                    <button 
                        className={`nav-btn main ${activePanel === 'search' ? 'active' : ''}`}
                        onClick={() => togglePanel('search')}
                    >
                        <div className="nav-icon-wrapper">
                            <MdSearch />
                        </div>
                        <span className="nav-text">토론 찾기</span>
                    </button>
                    <button 
                        className={`nav-btn sub ${activePanel === 'verdicts' ? 'active' : ''}`}
                        onClick={() => togglePanel('verdicts')}
                    >
                        <div className="nav-icon-wrapper">
                            <FiBookOpen />
                        </div>
                        <span className="nav-text sub">판결문</span>
                    </button>
                </nav>
            </div>
            
            {/* 중앙 */}
            <main className="center-area">
                <div className="character-section">
                    <div className="character-wrapper">
                        <img 
                            src={`https://api.dicebear.com/9.x/notionists/svg?seed=${user?.nickname || 'User'}&backgroundColor=transparent`} 
                            alt="My Character" 
                            className="character-img"
                        />
                    </div>
                    <div className="nickname-badge">
                        <span className="level-badge">LV.1</span>
                        <span className="user-nickname">{user?.nickname || "Guest"}</span>
                    </div>
                </div>
            </main>

            <SearchPanel 
                isOpen={activePanel === 'search'} 
                onClose={() => setActivePanel(null)} 
            />
            
            <VerdictsPanel 
                isOpen={activePanel === 'verdicts'} 
                onClose={() => setActivePanel(null)} 
            />

            {/* 오른쪽 사이드바 */}
            <div className="sidebar-right">
                {/* 추후 구현 */}
                현재 관전자 수가 많은 토론, 반응이 많은 토론 판결문
            </div>
        </div>
    )
}
export default HomePage