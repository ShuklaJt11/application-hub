import { beforeEach, describe, expect, it } from 'vitest';

import {
  clearAuthSession,
  clearAuthTokens,
  clearStoredUser,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  setAuthTokens,
  setStoredUser,
  tokenStorageKeys,
} from './token-storage';

describe('token-storage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and reads access and refresh tokens', () => {
    setAuthTokens({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
    });

    expect(getAccessToken()).toBe('access-1');
    expect(getRefreshToken()).toBe('refresh-1');
  });

  it('removes stale refresh token when response does not include it', () => {
    localStorage.setItem(tokenStorageKeys.refresh, 'existing-refresh');

    setAuthTokens({
      access_token: 'updated-access',
      token_type: 'bearer',
    });

    expect(getAccessToken()).toBe('updated-access');
    expect(getRefreshToken()).toBeNull();
  });

  it('clears both tokens', () => {
    localStorage.setItem(tokenStorageKeys.access, 'a');
    localStorage.setItem(tokenStorageKeys.refresh, 'r');

    clearAuthTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it('stores and reads the authenticated user', () => {
    setStoredUser({
      id: 'user-1',
      email: 'user@example.com',
      username: 'user123',
      first_name: 'Test',
      last_name: 'User',
      full_name: 'Test User',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    });

    expect(getStoredUser()).toEqual({
      id: 'user-1',
      email: 'user@example.com',
      username: 'user123',
      first_name: 'Test',
      last_name: 'User',
      full_name: 'Test User',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    });
  });

  it('clears the full auth session', () => {
    localStorage.setItem(tokenStorageKeys.access, 'a');
    localStorage.setItem(tokenStorageKeys.refresh, 'r');
    localStorage.setItem(tokenStorageKeys.user, JSON.stringify({ id: 'user-1' }));

    clearAuthSession();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(getStoredUser()).toBeNull();
  });

  it('clears only the stored user when requested', () => {
    localStorage.setItem(tokenStorageKeys.user, JSON.stringify({ id: 'user-1' }));

    clearStoredUser();

    expect(getStoredUser()).toBeNull();
  });
});
