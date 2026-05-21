import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

import { authApi, clearToken, getToken, userApi } from '@/lib/apiClient';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    async function loadUser() {
      try {
        const userData = await userApi.getMe();
        setUser(userData.data);
      } catch {
        setUser(null);
      }
      setLoading(false);
    }
    loadUser();
  }, []);

  // Accepts a complete SDK response (has data.role) or incomplete data
  // (OAuth callback, legacy login action). Falls back to re-fetching from API
  // when the passed object does not contain a role.
  const login = useCallback(async (userData) => {
    if (userData?.role) {
      setUser(userData);
      return;
    }
    try {
      const freshUser = await userApi.getMe();
      setUser(freshUser.data);
    } catch {
      setUser(null);
    }
  }, []);

  const logout = async () => {
    setUser(null);
    clearToken();
    await authApi.logout();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
