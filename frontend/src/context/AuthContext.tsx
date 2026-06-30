import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { auth as authApi } from "../lib/api";
import {
  clearTokens,
  getAccessToken,
  isLoggedIn,
  setTokens,
} from "../lib/auth";

interface AuthContextValue {
  loggedIn: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    setLoggedIn(true);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.register(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    setLoggedIn(true);
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setLoggedIn(false);
  }, []);

  // Keep loggedIn in sync if token is cleared externally (e.g. by auto-refresh failure)
  useEffect(() => {
    const handleStorage = () => {
      setLoggedIn(!!getAccessToken());
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  return (
    <AuthContext.Provider
      value={{ loggedIn, loading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// oxlint-disable-next-line react/only-export-components -- hook companion to AuthProvider, idiomatic context pattern
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
