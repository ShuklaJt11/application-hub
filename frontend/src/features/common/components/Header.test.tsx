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
  });

  it('opens mobile menu and closes with Escape', async () => {
    const user = userEvent.setup();

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Toggle menu' }));

    expect(screen.getAllByRole('link', { name: 'Login' }).length).toBeGreaterThan(0);
    const backdrop = document.querySelector('div[aria-hidden="true"]');
    expect(backdrop).toBeTruthy();
    expect(backdrop?.className).toContain('backdrop-blur-sm');

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() => {
      expect(document.querySelector('#mobile-header-menu')).toBeNull();
    });
  });

  it('closes mobile menu on outside click', async () => {
    const user = userEvent.setup();

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Toggle menu' }));
    expect(document.querySelector('#mobile-header-menu')).toBeTruthy();

    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(document.querySelector('#mobile-header-menu')).toBeNull();
    });
  });

  it('closes mobile menu when backdrop is clicked', async () => {
    const user = userEvent.setup();

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Toggle menu' }));
    expect(document.querySelector('#mobile-header-menu')).toBeTruthy();

    const backdrop = document.querySelector('div[aria-hidden="true"]');
    expect(backdrop).toBeTruthy();
    fireEvent.click(backdrop as HTMLElement);

    await waitFor(() => {
      expect(document.querySelector('#mobile-header-menu')).toBeNull();
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

    await user.click(screen.getByRole('button', { name: 'Logout' }));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
    });
    expect(navigateMock).toHaveBeenCalledWith('/login');
  });

  it('shows loading-state logout label when auth is loading', () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: true,
      logout: logoutMock,
    });

    renderHeader();

    expect(screen.getByRole('button', { name: 'Logging out...' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Logging out...' })).toHaveProperty('disabled', true);
  });

  it('closes mobile menu when authenticated profile link is clicked', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      logout: logoutMock,
    });

    renderHeader();

    await user.click(screen.getByRole('button', { name: 'Toggle menu' }));
    expect(document.querySelector('#mobile-header-menu')).toBeTruthy();

    const profileLinks = screen.getAllByRole('link', { name: 'Profile' });
    await user.click(profileLinks[1]);

    await waitFor(() => {
      expect(document.querySelector('#mobile-header-menu')).toBeNull();
    });
  });
});
