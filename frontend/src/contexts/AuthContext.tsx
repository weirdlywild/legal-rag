'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api/client';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'auth_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token on mount
  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        try {
          const response = await apiClient.post('/auth/validate', { token });
          if (response.data.valid) {
            setIsAuthenticated(true);
          } else {
            localStorage.removeItem(TOKEN_KEY);
          }
        } catch {
          localStorage.removeItem(TOKEN_KEY);
        }
      }
      setIsLoading(false);
    };

    validateToken();
  }, []);

  const login = async (password: string) => {
    try {
      const response = await apiClient.post('/auth/login', { password });
      if (response.data.success && response.data.token) {
        localStorage.setItem(TOKEN_KEY, response.data.token);
        setIsAuthenticated(true);
        return { success: true };
      }
      return { success: false, error: 'Login failed' };
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Invalid password';
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      try {
        await apiClient.post('/auth/logout', { token });
      } catch {
        // Ignore errors on logout
      }
    }
    localStorage.removeItem(TOKEN_KEY);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
