import Cookies from 'js-cookie';
import React, { createContext, useContext, useState, useEffect } from 'react';

import { apiFetch } from '../lib/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const token = Cookies.get('jwt');
      if (token) {
        try {
          const userData = await apiFetch('/api/auth/me');
          setUser(userData);
        } catch (error) {
          console.error('Auth check failed', error);
          Cookies.remove('jwt');
        }
      }
      setLoading(false);
    }
    loadUser();
  }, []);

  const login = (userData) => setUser(userData);
  const logout = () => {
    setUser(null);
    Cookies.remove('jwt');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
