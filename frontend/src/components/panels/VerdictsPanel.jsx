import { RiCloseLine } from "react-icons/ri";
import "../../styles/SlidePanel.css";

function VerdictsPanel({ isOpen, onClose }) {
    return (
        <div className={`slide-panel-container ${isOpen ? 'open' : ''}`}>
            <div className="panel-header-area sub">
                <h2 className="panel-title">판결문</h2>
                <p className="panel-desc">관심있는 토론의 판결문을 확인해 보세요.</p>
                <button className="panel-close-btn" onClick={onClose}>
                    <RiCloseLine size={28} />
                </button>
            </div>
        </div>
    );
}

export default VerdictsPanel