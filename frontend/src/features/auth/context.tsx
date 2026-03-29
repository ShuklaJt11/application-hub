/**
 * Authentication context and provider
 * Manages global auth state and provides auth methods
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { clearAuthTokens, getAccessToken, setAuthTokens } from '@/api';
import { authService } from './services/auth';
import type { User } from '@/types';
import type { SignupCredentials } from './services/auth';
import type { LoginCredentials } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (credentials: SignupCredentials) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if user is already authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (token) {
        // TODO: Fetch current user data from API
        // For now, we'll just mark as authenticated if we have a token
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const tokens = await authService.login(credentials);
      setAuthTokens(tokens);
      // TODO: Fetch user data after successful login
      setUser(null); // Placeholder
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (credentials: SignupCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const tokens = await authService.signup(credentials);
      setAuthTokens(tokens);
      // TODO: Set user data from response
      setUser(null); // Placeholder
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Signup failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      clearAuthTokens();
      setUser(null);
      setIsLoading(false);
    }
  };

  const isAuthenticated = !!getAccessToken();

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        signup,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
