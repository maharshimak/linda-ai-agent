/**
 * Auth Context
 * Provides authentication state and methods throughout the app
 */
import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, getStoredUser, setStoredUser } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(getStoredUser());
    const [loading, setLoading] = useState(true);
    const [videosToday, setVideosToday] = useState(0);
    const [dailyLimit, setDailyLimit] = useState(2);

    // Check auth status on mount
    useEffect(() => {
        const checkAuth = async () => {
            const storedUser = getStoredUser();
            if (storedUser) {
                try {
                    const userData = await authAPI.getMe();
                    setUser({ ...storedUser, ...userData });
                    setVideosToday(userData.videos_today);
                    setDailyLimit(userData.daily_limit);
                } catch (error) {
                    // Token invalid, clear auth
                    authAPI.logout();
                    setUser(null);
                }
            }
            setLoading(false);
        };

        checkAuth();
    }, []);

    const login = async (email, password) => {
        const data = await authAPI.login(email, password);
        setUser(data.user);

        // Get full user info
        const userData = await authAPI.getMe();
        setVideosToday(userData.videos_today);
        setDailyLimit(userData.daily_limit);

        return data;
    };

    const signup = async (email, password) => {
        const data = await authAPI.signup(email, password);
        setUser(data.user);
        setVideosToday(0);
        setDailyLimit(2);
        return data;
    };

    const logout = () => {
        authAPI.logout();
        setUser(null);
        setVideosToday(0);
    };

    const refreshUserInfo = async () => {
        try {
            const userData = await authAPI.getMe();
            setUser(prev => ({ ...prev, ...userData }));
            setVideosToday(userData.videos_today);
            setDailyLimit(userData.daily_limit);
        } catch (error) {
            console.error('Failed to refresh user info:', error);
        }
    };

    const value = {
        user,
        loading,
        isAuthenticated: !!user,
        isAdmin: user?.is_admin || false,
        videosToday,
        dailyLimit,
        videosRemaining: user?.is_admin ? 999 : Math.max(0, dailyLimit - videosToday),
        login,
        signup,
        logout,
        refreshUserInfo
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
