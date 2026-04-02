import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

const useAuthMock = vi.fn();

vi.mock('@/features/auth', () => ({
  useAuth: () => useAuthMock(),
}));

import Sidebar from './Sidebar';

const renderSidebar = () =>
  render(
    <MemoryRouter>
      <Sidebar />
    </MemoryRouter>
  );

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render for unauthenticated users', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: false });

    renderSidebar();

    expect(screen.queryByLabelText('Sidebar navigation')).toBeNull();
    expect(screen.queryByRole('link', { name: 'Dashboard' })).toBeNull();
  });

  it('renders required links for authenticated users', () => {
    useAuthMock.mockReturnValue({ isAuthenticated: true });

    renderSidebar();

    expect(screen.getByLabelText('Sidebar navigation')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Dashboard' }).getAttribute('href')).toBe('/dashboard');
    expect(screen.getByRole('link', { name: 'Applications' }).getAttribute('href')).toBe(
      '#applications'
    );
    expect(screen.getByRole('link', { name: 'Reminders' }).getAttribute('href')).toBe('#reminders');
  });

  it('opens and collapses the sidebar from the drawer toggle', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({ isAuthenticated: true });

    renderSidebar();

    const toggleButton = screen.getByRole('button', { name: 'Expand sidebar' });

    expect(toggleButton.getAttribute('aria-expanded')).toBe('false');

    await user.click(toggleButton);

    expect(
      screen.getByRole('button', { name: 'Collapse sidebar' }).getAttribute('aria-expanded')
    ).toBe('true');

    await user.click(screen.getByRole('button', { name: 'Collapse sidebar' }));

    expect(
      screen.getByRole('button', { name: 'Expand sidebar' }).getAttribute('aria-expanded')
    ).toBe('false');
  });

  it('closes the expanded sidebar on Escape', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({ isAuthenticated: true });

    renderSidebar();

    await user.click(screen.getByRole('button', { name: 'Expand sidebar' }));

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: 'Expand sidebar' }).getAttribute('aria-expanded')
      ).toBe('false');
    });
  });

  it('collapses the drawer after a navigation item is clicked', async () => {
    const user = userEvent.setup();
    useAuthMock.mockReturnValue({ isAuthenticated: true });

    renderSidebar();

    await user.click(screen.getByRole('button', { name: 'Expand sidebar' }));
    await user.click(screen.getByRole('link', { name: 'Applications' }));

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: 'Expand sidebar' }).getAttribute('aria-expanded')
      ).toBe('false');
    });
  });
});
