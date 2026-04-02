/**
 * Authentication context and provider
 * Manages global auth state and provides auth methods
 */

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  authStorageEventName,
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  setAuthTokens,
  setStoredUser,
} from '@/api';
import { authService } from './services/auth';
import type { AuthTokens, User } from '@/types';
import type { SignupCredentials } from './services/auth';
import type { LoginCredentials } from '@/types';

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (credentials: SignupCredentials) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [accessToken, setAccessTokenState] = useState<string | null>(() => getAccessToken());
  const [refreshToken, setRefreshTokenState] = useState<string | null>(() => getRefreshToken());
  const [isLoading, setIsLoading] = useState(() => Boolean(getAccessToken()));
  const [error, setError] = useState<string | null>(null);

  const syncSessionFromStorage = useCallback(() => {
    setAccessTokenState(getAccessToken());
    setRefreshTokenState(getRefreshToken());
    setUser(getStoredUser());
  }, []);

  const restoreSession = useCallback(async () => {
    const storedAccessToken = getAccessToken();
    if (!storedAccessToken) {
      syncSessionFromStorage();
      setIsLoading(false);
      return;
    }

    setIsLoading(true);

    try {
      const currentUser = await authService.getCurrentUser();
      setStoredUser(currentUser);
      syncSessionFromStorage();
    } catch {
      clearAuthSession();
      syncSessionFromStorage();
    } finally {
      setIsLoading(false);
    }
  }, [syncSessionFromStorage]);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  useEffect(() => {
    const handleStorageChange = () => {
      syncSessionFromStorage();
    };

    window.addEventListener(authStorageEventName, handleStorageChange);

    return () => {
      window.removeEventListener(authStorageEventName, handleStorageChange);
    };
  }, [syncSessionFromStorage]);

  const establishSession = async (tokens: AuthTokens) => {
    setAuthTokens(tokens);
    try {
      const currentUser = await authService.getCurrentUser();
      setStoredUser(currentUser);
      syncSessionFromStorage();
    } catch (error) {
      clearAuthSession();
      syncSessionFromStorage();
      throw error;
    }
  };

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const tokens = await authService.login(credentials);
      await establishSession(tokens);
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
      await establishSession(tokens);
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
      clearAuthSession();
      syncSessionFromStorage();
      setIsLoading(false);
    }
  };

  const isAuthenticated = Boolean(accessToken && user);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        refreshToken,
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
