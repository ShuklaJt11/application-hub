import { beforeEach, describe, expect, it } from 'vitest';

import {
  clearAuthTokens,
  getAccessToken,
  getRefreshToken,
  setAuthTokens,
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

  it('keeps existing refresh token when response does not include it', () => {
    localStorage.setItem(tokenStorageKeys.refresh, 'existing-refresh');

    setAuthTokens({
      access_token: 'updated-access',
      token_type: 'bearer',
    });

    expect(getAccessToken()).toBe('updated-access');
    expect(getRefreshToken()).toBe('existing-refresh');
  });

  it('clears both tokens', () => {
    localStorage.setItem(tokenStorageKeys.access, 'a');
    localStorage.setItem(tokenStorageKeys.refresh, 'r');

    clearAuthTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});
