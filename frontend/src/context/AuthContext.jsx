import { createContext, useContext, useState, useEffect, useCallback } from "react";

const AuthContext = createContext(null);

// TODO: Remove DEV_MODE mock when Week 2 auth is implemented
const DEV_MODE = true;
const MOCK_USER = {
  id: 1,
  name: "Dev Admin",
  email: "admin@dev.local",
  role: "admin",  // Change to "agent" or "customer" to preview other dashboards
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(DEV_MODE ? MOCK_USER : null);
  const [token, setToken] = useState(() => DEV_MODE ? "dev-token" : localStorage.getItem("token"));
  const [loading, setLoading] = useState(false);

  const logout = useCallback(() => {
    if (DEV_MODE) return;
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback((accessToken, userData) => {
    if (DEV_MODE) return;
    localStorage.setItem("token", accessToken);
    setToken(accessToken);
    setUser(userData);
  }, []);

  useEffect(() => {
    if (DEV_MODE) return;
    if (!token) {
      setLoading(false);
      return;
    }

    // Verify token by fetching current user
    fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Invalid token");
        return res.json();
      })
      .then((data) => setUser(data))
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [token, logout]);

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    isAuthenticated: DEV_MODE || !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
