import { Routes, Route } from "react-router-dom"
import Layout from "./components/Layout"
import MainPage from "./pages/MainPage"
import DebatePage from "./pages/DebatePage"
import SocialCallbackPage from "./pages/SocialCallbackPage"
import MyPage from "./pages/MyPage"
import { AuthProvider } from "./contexts/AuthContext"
import DebateFindPage from "./pages/DebateFindPage"
import DebateCreatePage from "./pages/DebateCreatePage"
import HistoryPage from './pages/HistoryPage'
import VerdictsPage from "./pages/VerdictsPage";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<MainPage />} />
          <Route path="find" element={<DebateFindPage />} />
          <Route path="create" element={<DebateCreatePage />} />
          <Route path="/verdicts" element={<VerdictsPage />} />
          <Route path="mypage" element={<MyPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Route>
        <Route path="debate/room/:roomId" element={<DebatePage />} />
        <Route path="/social/callback" element={<SocialCallbackPage />} />
      </Routes>
    </AuthProvider>
  )
}
export default App
