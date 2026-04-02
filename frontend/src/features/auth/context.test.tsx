import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AuthTokens, LoginCredentials, User } from '@/types';

let accessToken: string | null = null;
let refreshToken: string | null = null;
let storedUser: User | null = null;

const authServiceState = vi.hoisted(() => ({
  loginMock: vi.fn<(credentials: LoginCredentials) => Promise<AuthTokens>>(),
  signupMock: vi.fn(),
  logoutMock: vi.fn(),
  getCurrentUserMock: vi.fn<() => Promise<User>>(),
}));

const apiState = vi.hoisted(() => ({
  clearAuthSessionMock: vi.fn(() => {
    accessToken = null;
    refreshToken = null;
    storedUser = null;
  }),
  getAccessTokenMock: vi.fn(() => accessToken),
  getRefreshTokenMock: vi.fn(() => refreshToken),
  getStoredUserMock: vi.fn(() => storedUser),
  setAuthTokensMock: vi.fn((tokens: AuthTokens) => {
    accessToken = tokens.access_token;
    refreshToken = tokens.refresh_token ?? null;
  }),
  setStoredUserMock: vi.fn((user: User) => {
    storedUser = user;
  }),
}));

vi.mock('./services/auth', () => ({
  authService: {
    login: authServiceState.loginMock,
    signup: authServiceState.signupMock,
    logout: authServiceState.logoutMock,
    getCurrentUser: authServiceState.getCurrentUserMock,
  },
}));

vi.mock('@/api', () => ({
  authStorageEventName: 'apphub-auth-storage-change',
  clearAuthSession: apiState.clearAuthSessionMock,
  getAccessToken: apiState.getAccessTokenMock,
  getRefreshToken: apiState.getRefreshTokenMock,
  getStoredUser: apiState.getStoredUserMock,
  setAuthTokens: apiState.setAuthTokensMock,
  setStoredUser: apiState.setStoredUserMock,
}));

import { AuthProvider, useAuth } from './context';

const AuthHarness = () => {
  const auth = useAuth();

  return (
    <div>
      <div data-testid="is-authenticated">{String(auth.isAuthenticated)}</div>
      <div data-testid="is-loading">{String(auth.isLoading)}</div>
      <div data-testid="error">{auth.error ?? ''}</div>
      <button
        type="button"
        onClick={() => {
          void auth
            .login({ email: 'user@example.com', password: 'secret123' })
            .catch(() => undefined);
        }}
      >
        login
      </button>
      <button
        type="button"
        onClick={() => {
          void auth
            .signup({
              username: 'username',
              first_name: 'User',
              last_name: 'Name',
              email: 'user@example.com',
              password: 'Password123',
            })
            .catch(() => undefined);
        }}
      >
        signup
      </button>
      <button
        type="button"
        onClick={() => {
          void auth.logout().catch(() => undefined);
        }}
      >
        logout
      </button>
    </div>
  );
};

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    accessToken = null;
    refreshToken = null;
    storedUser = null;
    authServiceState.getCurrentUserMock.mockResolvedValue({
      id: 'user-1',
      email: 'user@example.com',
      username: 'user123',
      first_name: 'User',
      last_name: 'Name',
      full_name: 'User Name',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    });
  });

  it('exposes unauthenticated state by default', () => {
    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    );

    expect(screen.getByTestId('is-authenticated').textContent).toBe('false');
    expect(screen.getByTestId('is-loading').textContent).toBe('false');
  });

  it('stores tokens after login and updates auth state', async () => {
    authServiceState.loginMock.mockResolvedValueOnce({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'bearer',
    });

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    );

    await user.click(screen.getByRole('button', { name: 'login' }));

    expect(authServiceState.loginMock).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'secret123',
    });
    expect(apiState.setAuthTokensMock).toHaveBeenCalledWith({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'bearer',
    });
    expect(authServiceState.getCurrentUserMock).toHaveBeenCalledTimes(1);
    expect(apiState.setStoredUserMock).toHaveBeenCalledWith({
      id: 'user-1',
      email: 'user@example.com',
      username: 'user123',
      first_name: 'User',
      last_name: 'Name',
      full_name: 'User Name',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    });
    expect(screen.getByTestId('is-authenticated').textContent).toBe('true');
  });

  it('stores tokens after signup', async () => {
    authServiceState.signupMock.mockResolvedValueOnce({
      access_token: 'signup-access-token',
      refresh_token: 'signup-refresh-token',
      token_type: 'bearer',
    });

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    );

    await user.click(screen.getByRole('button', { name: 'signup' }));

    expect(authServiceState.signupMock).toHaveBeenCalledWith({
      username: 'username',
      first_name: 'User',
      last_name: 'Name',
      email: 'user@example.com',
      password: 'Password123',
    });
    expect(apiState.setAuthTokensMock).toHaveBeenCalledWith({
      access_token: 'signup-access-token',
      refresh_token: 'signup-refresh-token',
      token_type: 'bearer',
    });
    expect(authServiceState.getCurrentUserMock).toHaveBeenCalledTimes(1);
  });

  it('surfaces login errors and leaves user unauthenticated', async () => {
    authServiceState.loginMock.mockRejectedValueOnce(new Error('Login failed badly'));

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    );

    await user.click(screen.getByRole('button', { name: 'login' }));

    expect((await screen.findByTestId('error')).textContent).toBe('Login failed badly');
    expect(screen.getByTestId('is-authenticated').textContent).toBe('false');
  });

  it('restores an existing persisted session on mount', async () => {
    accessToken = 'persisted-access-token';
    refreshToken = 'persisted-refresh-token';

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('is-authenticated').textContent).toBe('true');
    });
  });

  it('clears tokens on logout even when the API call fails', async () => {
    accessToken = 'existing-access-token';
    refreshToken = 'existing-refresh-token';
    storedUser = {
      id: 'user-1',
      email: 'user@example.com',
      username: 'user123',
      first_name: 'User',
      last_name: 'Name',
      full_name: 'User Name',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    };
    authServiceState.logoutMock.mockRejectedValueOnce(new Error('logout failed'));

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    );

    await user.click(screen.getByRole('button', { name: 'logout' }));

    expect(authServiceState.logoutMock).toHaveBeenCalledTimes(1);
    expect(apiState.clearAuthSessionMock).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('is-authenticated').textContent).toBe('false');

    consoleErrorSpy.mockRestore();
  });
});
