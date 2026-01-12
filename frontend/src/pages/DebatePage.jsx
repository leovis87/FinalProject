import "../styles/DebatePage.css"

function DebatePage() {
    return (
        <div className="debate-container">
            {/* 왼쪽 찬성 팀 */}
            <div className="team-panel pro-team">
                <div className="team-header">
                    <h2>찬성</h2>
                </div>
                <div className="user-list">

                </div>
            </div>
            {/* 메인 */}
            <div className="chat-area">
                sdfsdf
            </div>
            {/* 오른쪽 반대 팀 */}
            <div className="team-panel con-team">
                <div className="team-header">
                    <h2>반대</h2>
                </div>
            </div>
        </div>
    )
}
export default DebatePage