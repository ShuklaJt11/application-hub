/**
 * Type definitions for API responses and models
 */

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Application {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  url?: string;
  created_at: string;
  updated_at: string;
}

export interface Reminder {
  id: string;
  application_id: string;
  title: string;
  description?: string;
  due_date: string;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string | null;
  token_type: 'bearer';
  expires_in?: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface APIError {
  detail: string | Record<string, unknown>;
}
