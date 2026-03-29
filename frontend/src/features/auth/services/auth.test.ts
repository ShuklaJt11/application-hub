import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AuthTokens } from '@/types';

const apiState = vi.hoisted(() => ({
  postMock: vi.fn(),
}));

vi.mock('@/api', () => ({
  apiClient: {
    post: apiState.postMock,
  },
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
        full_name: 'User Name',
        email: 'user@example.com',
        password: 'Password123',
      })
    ).resolves.toEqual(tokens);

    expect(apiState.postMock).toHaveBeenCalledWith(
      '/auth/signup',
      {
        full_name: 'User Name',
        email: 'user@example.com',
        password: 'Password123',
      },
      expect.objectContaining({ skipAuthToken: true })
    );
  });

  it('calls logout endpoint', async () => {
    apiState.postMock.mockResolvedValueOnce({ data: {} });

    await expect(authService.logout()).resolves.toBeUndefined();

    expect(apiState.postMock).toHaveBeenCalledWith('/auth/logout');
  });

  it('swallows logout endpoint errors', async () => {
    apiState.postMock.mockRejectedValueOnce(new Error('network error'));

    await expect(authService.logout()).resolves.toBeUndefined();
    expect(apiState.postMock).toHaveBeenCalledWith('/auth/logout');
  });
});
