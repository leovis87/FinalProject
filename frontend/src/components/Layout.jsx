import { Outlet } from "react-router-dom"
import Header from "./Header"
import Footer from "./Footer"
import "../styles/Layout.css"

function Layout() {
    return (
        <div className="layout-container">
            <Header />
            <main>
                <Outlet />
            </main>
        </div>
    )
}
export default Layout