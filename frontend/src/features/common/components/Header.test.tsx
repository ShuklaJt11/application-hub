import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const navigateMock = vi.fn();
const logoutMock = vi.fn<() => Promise<void>>();
const useAuthMock = vi.fn();

vi.mock('@/features/auth', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');

  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

import Header from './Header';

const renderHeader = () =>
  render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>
  );

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    logoutMock.mockResolvedValue(undefined);
    useAuthMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      logout: logoutMock,
    });
  });

  it('shows Login for unauthenticated users', () => {
    renderHeader();

    expect(screen.getByRole('link', { name: 'Login' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Logout' })).toBeNull();
    expect(screen.queryByRole('link', { name: 'Profile' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Open user menu' })).toBeNull();
  });

  it('opens user menu and closes with Escape', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      logout: logoutMock,
    });

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Open user menu' }));
    expect(screen.getByRole('menu')).toBeTruthy();
    expect(screen.getByRole('menuitem', { name: 'Profile' })).toBeTruthy();
    expect(screen.getByRole('menuitem', { name: 'Logout' })).toBeTruthy();

    fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' });

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: 'Open user menu' }).getAttribute('aria-expanded')
      ).toBeNull();
    });
  });

  it('closes user menu on outside click', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      logout: logoutMock,
    });

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Open user menu' }));
    expect(screen.getByRole('menu')).toBeTruthy();

    const backdrop = document.querySelector('.MuiBackdrop-root');
    expect(backdrop).toBeTruthy();
    fireEvent.click(backdrop as HTMLElement);

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: 'Open user menu' }).getAttribute('aria-expanded')
      ).toBeNull();
    });
  });

  it('closes user menu when profile is selected', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      logout: logoutMock,
    });

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Open user menu' }));
    await user.click(screen.getByRole('menuitem', { name: 'Profile' }));

    await waitFor(() => {
      expect(screen.queryByRole('menuitem', { name: 'Profile' })).toBeNull();
    });
  });

  it('logs out authenticated users and navigates to login', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      logout: logoutMock,
    });

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Open user menu' }));
    await user.click(screen.getByRole('menuitem', { name: 'Logout' }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
    });
    expect(navigateMock).toHaveBeenCalledWith('/login');
  });

  it('shows loading-state logout label when auth is loading', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: true,
      logout: logoutMock,
    });

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Open user menu' }));

    expect(screen.getByText('Logging out...')).toBeTruthy();
    expect(
      screen.getByRole('menuitem', { name: 'Logging out...' }).getAttribute('aria-disabled')
    ).toBe('true');
  });
});
