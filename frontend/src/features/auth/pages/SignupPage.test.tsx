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

import SignupPage from './SignupPage';

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthMock.mockReturnValue({
      signup: vi.fn().mockResolvedValue(undefined),
      isLoading: false,
      error: null,
      isAuthenticated: false,
    });
  });

  it('renders signup form fields', () => {
    render(
      <MemoryRouter>
        <SignupPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('Full Name')).toBeTruthy();
    expect(screen.getByLabelText('Email Address')).toBeTruthy();
    expect(screen.getByLabelText('Password')).toBeTruthy();
    expect(screen.getByLabelText('Confirm Password')).toBeTruthy();
  });

  it('shows validation error when passwords do not match', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <SignupPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full Name'), 'User Name');
    await user.type(screen.getByLabelText('Email Address'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'Password123');
    await user.type(screen.getByLabelText('Confirm Password'), 'Password456');
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    expect(await screen.findByText('Passwords do not match')).toBeTruthy();
  });

  it('submits signup data and redirects to dashboard', async () => {
    const user = userEvent.setup();
    const signupMock = vi.fn().mockResolvedValue(undefined);
    useAuthMock.mockReturnValue({
      signup: signupMock,
      isLoading: false,
      error: null,
      isAuthenticated: false,
    });

    render(
      <MemoryRouter>
        <SignupPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full Name'), 'User Name');
    await user.type(screen.getByLabelText('Email Address'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'Password123');
    await user.type(screen.getByLabelText('Confirm Password'), 'Password123');
    await user.click(screen.getByRole('button', { name: 'Sign Up' }));

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        full_name: 'User Name',
        email: 'user@example.com',
        password: 'Password123',
      });
    });

    expect(navigateMock).toHaveBeenCalledWith('/dashboard');
  });

  it('redirects authenticated users immediately', async () => {
    useAuthMock.mockReturnValue({
      signup: vi.fn(),
      isLoading: false,
      error: null,
      isAuthenticated: true,
    });

    render(
      <MemoryRouter>
        <SignupPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('renders auth error from context', () => {
    useAuthMock.mockReturnValue({
      signup: vi.fn(),
      isLoading: false,
      error: 'Signup failed',
      isAuthenticated: false,
    });

    render(
      <MemoryRouter>
        <SignupPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Signup failed')).toBeTruthy();
  });
});
