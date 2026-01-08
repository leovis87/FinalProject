import { useEffect } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"

function SocialCallbackPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { login } = useAuth();

    useEffect(() => {
        const accessToken = searchParams.get("access_token");
        if (accessToken) {
            login(accessToken);
            navigate("/", { replace: true });
        }
    }, [searchParams, navigate, login])

    return (
        <div>로그인 처리 중...</div>
    )
}
export default SocialCallbackPage