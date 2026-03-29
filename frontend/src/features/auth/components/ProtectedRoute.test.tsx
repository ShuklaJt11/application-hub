import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

const useAuthMock = vi.fn();

vi.mock('../context', () => ({
  useAuth: () => useAuthMock(),
}));

import ProtectedRoute from './ProtectedRoute';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state while auth is resolving', () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
    });

    render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route
            path="/private"
            element={
              <ProtectedRoute>
                <div>secret content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Loading...')).toBeTruthy();
    expect(screen.queryByText('secret content')).toBeNull();
  });

  it('redirects unauthenticated users to login', () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    });

    render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route
            path="/private"
            element={
              <ProtectedRoute>
                <div>secret content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>login screen</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('login screen')).toBeTruthy();
    expect(screen.queryByText('secret content')).toBeNull();
  });

  it('renders children for authenticated users', () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    });

    render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route
            path="/private"
            element={
              <ProtectedRoute>
                <div>secret content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('secret content')).toBeTruthy();
  });
});
