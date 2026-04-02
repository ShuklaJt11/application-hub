/**
 * Authentication API service
 * Handles login, signup, and logout API calls
 */

import { apiClient, getRefreshToken } from '@/api';
import type { AuthTokens, LoginCredentials, User } from '@/types';

export interface SignupCredentials extends LoginCredentials {
  username: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string | null;
  token_type: 'bearer';
  expires_in?: number;
}

export const authService = {
  /**
   * Login user with email and password
   */
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const response = await apiClient.post<AuthTokens>('/auth/login', credentials, {
      skipAuthToken: true,
    } as Record<string, unknown>);
    return response.data;
  },

  /**
   * Sign up new user
   */
  signup: async (credentials: SignupCredentials): Promise<AuthTokens> => {
    const response = await apiClient.post<AuthTokens>('/auth/signup', credentials, {
      skipAuthToken: true,
    } as Record<string, unknown>);
    return response.data;
  },

  /**
   * Fetch the authenticated user profile.
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Logout user (clear tokens)
   */
  logout: async (): Promise<void> => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      return;
    }

    try {
      await apiClient.post('/auth/logout', { refresh_token: refreshToken }, {
        skipAuthRefresh: true,
        skipAuthToken: true,
      } as Record<string, unknown>);
    } catch {
      // Ignore logout errors, tokens will be cleared on client side
    }
  },
};
