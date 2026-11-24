
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authAPI } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("orion_token");
    if (!token) { setLoading(false); return; }
    try {
      const { data } = await authAPI.me();
      setUser(data);
    } catch {
      localStorage.removeItem("orion_token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUser(); }, [loadUser]);

  const login = async (email, password) => {
    const { data } = await authAPI.login(email, password);
    localStorage.setItem("orion_token", data.access_token);
    await loadUser();
  };

  const register = async (name, email, password, institution) => {
    const { data } = await authAPI.register({ name, email, password, institution });
    localStorage.setItem("orion_token", data.access_token);
    await loadUser();
  };

  const logout = () => {
    localStorage.removeItem("orion_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
