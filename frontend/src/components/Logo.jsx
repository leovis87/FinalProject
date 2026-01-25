import logoIcon from "../assets/logo-icon.png";

function Logo() {
    return (
        <div className="logo">
            <img src={logoIcon} alt="DebateHigh Logo" className="logo-icon" />
            <h1>DebateHigh</h1>
        </div>
    )
}
export default Logo