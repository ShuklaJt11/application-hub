import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const navigateMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock('../context', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');

  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

import LoginPage from './LoginPage';

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthMock.mockReturnValue({
      login: vi.fn().mockResolvedValue(undefined),
      isLoading: false,
      error: null,
      isAuthenticated: false,
    });
  });

  it('renders login form fields', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('Email Address')).toBeTruthy();
    expect(screen.getByLabelText('Password')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeTruthy();
  });

  it('shows validation errors before submission', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Email is required')).toBeTruthy();
    expect(await screen.findByText('Password is required')).toBeTruthy();
  });

  it('submits credentials and redirects to dashboard', async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockResolvedValue(undefined);
    useAuthMock.mockReturnValue({
      login: loginMock,
      isLoading: false,
      error: null,
      isAuthenticated: false,
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Email Address'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'secret123');
    await user.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'secret123',
      });
    });

    expect(navigateMock).toHaveBeenCalledWith('/dashboard');
  });

  it('redirects authenticated users immediately', async () => {
    useAuthMock.mockReturnValue({
      login: vi.fn(),
      isLoading: false,
      error: null,
      isAuthenticated: true,
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('renders auth error from context', () => {
    useAuthMock.mockReturnValue({
      login: vi.fn(),
      isLoading: false,
      error: 'Invalid credentials',
      isAuthenticated: false,
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Invalid credentials')).toBeTruthy();
  });
});
