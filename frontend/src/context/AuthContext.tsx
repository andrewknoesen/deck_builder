import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
    id: string;
    email: string;
    name: string;
    picture?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('google_id_token'));

    useEffect(() => {
        // Ideally verify token with backend /users/me here
        if (token) {
            // Mock user for now if we don't fetch
            // In real app, fetch /api/v1/users/me
        }
    }, [token]);

    const login = (newToken: string) => {
        localStorage.setItem('google_id_token', newToken);
        setToken(newToken);
        // Decode token or fetch user
    };

    const logout = () => {
        localStorage.removeItem('google_id_token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
