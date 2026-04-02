/**
 * Auth token storage helpers.
 */

import type { User } from '@/types';
import type { AuthTokens } from '@/types';

const ACCESS_TOKEN_KEY = 'apphub_access_token';
const REFRESH_TOKEN_KEY = 'apphub_refresh_token';
const USER_KEY = 'apphub_user';

const hasStorage = () => typeof window !== 'undefined' && !!window.localStorage;

export const authStorageEventName = 'apphub-auth-storage-change';

const notifyAuthStorageChanged = () => {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(new CustomEvent(authStorageEventName));
};

export const tokenStorageKeys = {
  access: ACCESS_TOKEN_KEY,
  refresh: REFRESH_TOKEN_KEY,
  user: USER_KEY,
} as const;

export const getAccessToken = (): string | null => {
  if (!hasStorage()) {
    return null;
  }

  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  if (!hasStorage()) {
    return null;
  }

  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const getStoredUser = (): User | null => {
  if (!hasStorage()) {
    return null;
  }

  const value = localStorage.getItem(USER_KEY);
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value) as User;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
};

export const setAuthTokens = (tokens: AuthTokens): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);

  if (tokens.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  notifyAuthStorageChanged();
};

export const clearAuthTokens = (): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  notifyAuthStorageChanged();
};

export const setStoredUser = (user: User): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.setItem(USER_KEY, JSON.stringify(user));
  notifyAuthStorageChanged();
};

export const clearStoredUser = (): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.removeItem(USER_KEY);
  notifyAuthStorageChanged();
};

export const clearAuthSession = (): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  notifyAuthStorageChanged();
};
