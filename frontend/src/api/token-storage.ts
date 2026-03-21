/**
 * Auth token storage helpers.
 */

import type { AuthTokens } from '@/types';

const ACCESS_TOKEN_KEY = 'apphub_access_token';
const REFRESH_TOKEN_KEY = 'apphub_refresh_token';

const hasStorage = () => typeof window !== 'undefined' && !!window.localStorage;

export const tokenStorageKeys = {
  access: ACCESS_TOKEN_KEY,
  refresh: REFRESH_TOKEN_KEY,
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

export const setAuthTokens = (tokens: AuthTokens): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);

  if (tokens.refresh_token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }
};

export const clearAuthTokens = (): void => {
  if (!hasStorage()) {
    return;
  }

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};
