import { useState } from "react"
import { RiRobot2Line, RiBookOpenLine, RiBarChartBoxLine } from "react-icons/ri";
import "../styles/MainPage.css"
import LoginModal from "../components/modals/LoginModal"
import HomePage from "./HomePage"
import { useAuth } from "../contexts/AuthContext"

function MainPage() {
    const { isAuthenticated } = useAuth();
    const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

    if (isAuthenticated) {
        return <HomePage />;
    }

    const openLoginModal = () => {
        setIsLoginModalOpen(true);
    };

    const closeLoginModal = () => {
        setIsLoginModalOpen(false);
    };

    return (
        <div className="main-container">
            <section className="banner-section">
                <div className="brand-intro">
                    <div className="brand-text">
                        <h1>토론의 시작부터 끝까지,<br />AI 파트너와 함께</h1>
                        <p>
                            학습 파트너와 함께 온라인 토론을 진행해 보세요.<br />
                            실시간 분석을 통해 토론 역량을 강화할 수 있습니다.
                        </p>
                        <div className="banner-btns">
                            <button className="btn-primary" onClick={openLoginModal}>
                                지금 참여하기
                            </button>
                            <button className="btn-guide">이용가이드</button>
                        </div>
                    </div>
                </div>
            </section>

            <section className="features-section">
                <div className="features-header">
                    <h2>더 스마트한 토론의 시작</h2>
                    <p>DebateHigh만의 차별화된 시스템을 경험해보세요.</p>
                </div>

                <div className="features-container">
                    <div className="feature-card">
                        <div className="icon-wrapper">
                            <RiBookOpenLine />
                        </div>
                        <h3>교과 연계 맞춤 주제</h3>
                        <p>
                            초등부터 고등까지 학년과 과목을 선택하세요.<br/>
                            AI가 최신 트렌드와 교과 과정을 분석해<br/>
                            가장 적합한 토론 주제를 추천해 드립니다.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="icon-wrapper">
                            <RiRobot2Line />
                        </div>
                        <h3>편파 없는 AI 사회자</h3>
                        <p>
                            특별한 기술이 적용된 AI 사회자가<br/>
                            이슈 정리부터 욕설 및 비방 필터링까지,<br/>
                            공정하고 쾌적한 토론 진행을 책임집니다.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="icon-wrapper">
                            <RiBarChartBoxLine />
                        </div>
                        <h3>데이터 기반 승패 판정</h3>
                        <p>
                            모호한 무승부는 존재하지 않습니다.<br/>
                            실시간 팩트체크와 논리적 타당성 분석을 통해<br/>
                            명확한 승패와 상세 피드백을 제공합니다.
                        </p>
                    </div>
                </div>
            </section>

            {isLoginModalOpen && <LoginModal onClose={closeLoginModal} />}
        </div>
    )
}
export default MainPage