/**
 * Authentication API service
 * Handles login, signup, and logout API calls
 */

import { apiClient } from '@/api';
import type { AuthTokens, LoginCredentials } from '@/types';

export interface SignupCredentials extends LoginCredentials {
  full_name: string;
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
   * Logout user (clear tokens)
   */
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Ignore logout errors, tokens will be cleared on client side
    }
  },
};
