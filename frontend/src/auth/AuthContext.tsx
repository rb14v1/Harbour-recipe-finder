import React, { createContext, useContext, useEffect, useState } from "react";
import * as authApi from "../api/auth";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .fetchMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await authApi.login(email, password);
    localStorage.setItem("access_token", tokens.access);
    localStorage.setItem("refresh_token", tokens.refresh);
    const me = await authApi.fetchMe();
    setUser(me);
  }

  async function register(email: string, password: string, firstName = "", lastName = "") {
    const result = await authApi.register(email, password, firstName, lastName);
    localStorage.setItem("access_token", result.access);
    localStorage.setItem("refresh_token", result.refresh);
    setUser(result.user);
  }

  async function logout() {
    const refresh = localStorage.getItem("refresh_token");
    try {
      if (refresh) await authApi.logout(refresh);
    } catch {
      // ignore network/already-invalid errors on logout
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
