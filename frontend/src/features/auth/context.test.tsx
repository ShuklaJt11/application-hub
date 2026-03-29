import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { AuthTokens, LoginCredentials } from '@/types';

let accessToken: string | null = null;
let refreshToken: string | null = null;

const authServiceState = vi.hoisted(() => ({
  loginMock: vi.fn<(credentials: LoginCredentials) => Promise<AuthTokens>>(),
  signupMock: vi.fn(),
  logoutMock: vi.fn(),
}));

const apiState = vi.hoisted(() => ({
  clearAuthTokensMock: vi.fn(() => {
    accessToken = null;
    refreshToken = null;
  }),
  getAccessTokenMock: vi.fn(() => accessToken),
  setAuthTokensMock: vi.fn((tokens: AuthTokens) => {
    accessToken = tokens.access_token;
    refreshToken = tokens.refresh_token ?? null;
  }),
}));

vi.mock('./services/auth', () => ({
  authService: {
    login: authServiceState.loginMock,
    signup: authServiceState.signupMock,
    logout: authServiceState.logoutMock,
  },
}));

vi.mock('@/api', () => ({
  clearAuthTokens: apiState.clearAuthTokensMock,
  getAccessToken: apiState.getAccessTokenMock,
  setAuthTokens: apiState.setAuthTokensMock,
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
              full_name: 'User Name',
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
      full_name: 'User Name',
      email: 'user@example.com',
      password: 'Password123',
    });
    expect(apiState.setAuthTokensMock).toHaveBeenCalledWith({
      access_token: 'signup-access-token',
      refresh_token: 'signup-refresh-token',
      token_type: 'bearer',
    });
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

  it('clears tokens on logout even when the API call fails', async () => {
    accessToken = 'existing-access-token';
    refreshToken = 'existing-refresh-token';
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
    expect(apiState.clearAuthTokensMock).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('is-authenticated').textContent).toBe('false');

    consoleErrorSpy.mockRestore();
  });
});
