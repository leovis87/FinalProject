import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

   const fetchMe = useCallback(async (token) => {
        try {
            // 외부 IP 대신 상대 경로 사용 (Vite 프록시 활용)
            const response = await fetch("/api/users/me", {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                setIsAuthenticated(true);
            } else {
                logout();
            }
        } catch (error) {
            console.error("Failed to fetch user:", error);
            logout();
        } finally {
            setIsLoading(false);
        }
    }, []);

    const refreshUser = useCallback(() => {
        const token = localStorage.getItem("access_token");
        if (token) {
            fetchMe(token);
        }
    }, [fetchMe]);

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (token) {
            fetchMe(token);
        } else {
            setIsLoading(false);
        }
    }, [fetchMe]);

    const login = (token) => {
        localStorage.setItem("access_token", token);
        fetchMe(token);
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        setIsAuthenticated(false);
        setUser(null);
    };

    const updateLocalNickname = (newNickname) => {
        if (user) {
            setUser({ ...user, nickname: newNickname });
        }
    }

    return (
        <AuthContext.Provider value={{ isAuthenticated, user, isLoading, login, logout, updateLocalNickname, refreshUser }}>
            {!isLoading && children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
