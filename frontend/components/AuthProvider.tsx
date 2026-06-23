"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi, clearToken, getToken, setToken, type AuthResponse, type User } from "@/lib/api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  googleLogin: (credential: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const accept = useCallback((result: AuthResponse) => {
    setToken(result.accessToken);
    setUser(result.user);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    authApi.me().then(setUser).catch(() => clearToken()).finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    login: async (email, password) => accept(await authApi.login({ email, password })),
    register: async (name, email, password) => accept(await authApi.register({ name, email, password })),
    googleLogin: async (credential) => accept(await authApi.google(credential)),
    logout: () => { clearToken(); setUser(null); },
  }), [user, loading, accept]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
