import { createContext, useContext, useEffect, useState } from "react";
import { api, clearSession, saveTokens } from "../services/api";
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    let live = true;
    const ended = () => setUser(null);
    window.addEventListener("session-ended", ended);
    if (sessionStorage.getItem("tokens"))
      api
        .get("/auth/me/")
        .then((r) => {
          if (live) setUser(r.data);
        })
        .catch(clearSession)
        .finally(() => {
          if (live) setLoading(false);
        });
    else setLoading(false);
    return () => {
      live = false;
      window.removeEventListener("session-ended", ended);
    };
  }, []);
  async function login(values) {
    const { data } = await api.post("/auth/login/", values);
    saveTokens({ access: data.access, refresh: data.refresh });
    setUser(data.user);
    return data.user;
  }
  async function logout() {
    try {
      const t = JSON.parse(sessionStorage.getItem("tokens") || "{}");
      if (t.refresh) await api.post("/auth/logout/", { refresh: t.refresh });
    } catch {
      // Local sign-out must still work when the server is unreachable.
    } finally {
      clearSession();
      setUser(null);
    }
  }
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  return useContext(AuthContext);
}
