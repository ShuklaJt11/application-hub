import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AuthTokens } from '@/types';

const apiState = vi.hoisted(() => ({
  postMock: vi.fn(),
}));

vi.mock('@/api', () => ({
  apiClient: {
    get: apiState.postMock,
    post: apiState.postMock,
  },
  getRefreshToken: vi.fn(() => 'refresh-token'),
}));

import { authService } from './auth';

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('logs in with skipAuthToken enabled', async () => {
    const tokens: AuthTokens = {
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
    };
    apiState.postMock.mockResolvedValueOnce({ data: tokens });

    await expect(
      authService.login({ email: 'user@example.com', password: 'secret123' })
    ).resolves.toEqual(tokens);

    expect(apiState.postMock).toHaveBeenCalledWith(
      '/auth/login',
      { email: 'user@example.com', password: 'secret123' },
      expect.objectContaining({ skipAuthToken: true })
    );
  });

  it('signs up with skipAuthToken enabled', async () => {
    const tokens: AuthTokens = {
      access_token: 'access-token',
      refresh_token: 'refresh-token',
      token_type: 'bearer',
    };
    apiState.postMock.mockResolvedValueOnce({ data: tokens });

    await expect(
      authService.signup({
        username: 'username',
        first_name: 'User',
        last_name: 'Name',
        email: 'user@example.com',
        password: 'Password123',
      })
    ).resolves.toEqual(tokens);

    expect(apiState.postMock).toHaveBeenCalledWith(
      '/auth/signup',
      {
        username: 'username',
        first_name: 'User',
        last_name: 'Name',
        email: 'user@example.com',
        password: 'Password123',
      },
      expect.objectContaining({ skipAuthToken: true })
    );
  });

  it('fetches the current authenticated user', async () => {
    apiState.postMock.mockResolvedValueOnce({
      data: {
        id: 'user-1',
        email: 'user@example.com',
        username: 'user123',
        first_name: 'User',
        last_name: 'Name',
        full_name: 'User Name',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
    });

    await expect(authService.getCurrentUser()).resolves.toEqual({
      id: 'user-1',
      email: 'user@example.com',
      username: 'user123',
      first_name: 'User',
      last_name: 'Name',
      full_name: 'User Name',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    });

    expect(apiState.postMock).toHaveBeenCalledWith('/auth/me');
  });

  it('calls logout endpoint', async () => {
    apiState.postMock.mockResolvedValueOnce({ data: {} });

    await expect(authService.logout()).resolves.toBeUndefined();

    expect(apiState.postMock).toHaveBeenCalledWith(
      '/auth/logout',
      { refresh_token: 'refresh-token' },
      expect.objectContaining({ skipAuthRefresh: true, skipAuthToken: true })
    );
  });

  it('swallows logout endpoint errors', async () => {
    apiState.postMock.mockRejectedValueOnce(new Error('network error'));

    await expect(authService.logout()).resolves.toBeUndefined();
    expect(apiState.postMock).toHaveBeenCalledWith(
      '/auth/logout',
      { refresh_token: 'refresh-token' },
      expect.objectContaining({ skipAuthRefresh: true, skipAuthToken: true })
    );
  });
});
