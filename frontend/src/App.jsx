import { Routes, Route } from "react-router-dom"
import Layout from "./components/Layout"
import MainPage from "./pages/MainPage"
import DebatePage from "./pages/DebatePage"
import SocialCallbackPage from "./pages/SocialCallbackPage"
import { AuthProvider } from "./contexts/AuthContext"

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<MainPage />} />
        </Route>
        <Route path="debate/room/:roomId" element={<DebatePage />} />
        <Route path="/social/callback" element={<SocialCallbackPage />} />
      </Routes>
    </AuthProvider>
  )
}
export default App