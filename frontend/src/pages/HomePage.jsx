import { useState } from "react";
import { MdSearch } from "react-icons/md";
import { FiBookOpen } from "react-icons/fi";
import { useAuth } from "../contexts/AuthContext";
import SearchPanel from "../components/panels/SearchPanel";
import VerdictsPanel from "../components/panels/VerdictsPanel";
import "../styles/HomePage.css";
// 이미지 임포트 (경로가 정확한지 확인해주세요)
import backgroundImage from '../assets/back.png';

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
        <div 
            className="home-container" 
            // 여기에서 임포트한 backgroundImage 변수를 사용합니다.
            style={{ 
                backgroundImage: `url(${backgroundImage})`, 
                backgroundSize: 'cover', 
                backgroundPosition: 'center',
                // 필요하다면 컨테이너가 화면을 꽉 채우도록 설정 (보통 CSS에서 처리하지만 확실하게 하기 위해)
                minHeight: '100vh',
                width: '100%'
            }}
        >
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