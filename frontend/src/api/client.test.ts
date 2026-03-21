import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AxiosHeaders, type AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { apiClient } from './client';
import { normalizeApiError } from './error-handler';
import { clearAuthTokens, getAccessToken, getRefreshToken, setAuthTokens } from './token-storage';

vi.mock('./error-handler', () => ({
  normalizeApiError: vi.fn((error: unknown) => ({ normalized: true, source: error })),
}));

vi.mock('./token-storage', () => ({
  clearAuthTokens: vi.fn(),
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  setAuthTokens: vi.fn(),
}));

type RequestInterceptorStore = {
  handlers: Array<{
    fulfilled: (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig;
  }>;
};

type ResponseInterceptorStore = {
  handlers: Array<{
    rejected: (error: AxiosError) => Promise<unknown>;
  }>;
};

type RetryableConfigInput = Partial<InternalAxiosRequestConfig> & {
  _retry?: boolean;
  skipAuthRefresh?: boolean;
};

const getRequestHandler = () => {
  const store = apiClient.interceptors.request as unknown as RequestInterceptorStore;
  return store.handlers[0].fulfilled;
};

const getResponseErrorHandler = () => {
  const store = apiClient.interceptors.response as unknown as ResponseInterceptorStore;
  return store.handlers[0].rejected;
};

const createAxiosError = (status: number, config: RetryableConfigInput = {}): AxiosError => {
  return {
    config: {
      headers: new AxiosHeaders(),
      ...config,
    } as InternalAxiosRequestConfig,
    response: {
      status,
    },
  } as AxiosError;
};

describe('api client interceptors', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('adds Authorization header when access token exists', () => {
    vi.mocked(getAccessToken).mockReturnValue('token-123');

    const requestHandler = getRequestHandler();
    const config = {
      headers: new AxiosHeaders(),
    } as InternalAxiosRequestConfig;

    const result = requestHandler(config);
    const authHeader = (result.headers as AxiosHeaders).get('Authorization');

    expect(authHeader).toBe('Bearer token-123');
  });

  it('does not add Authorization header when skipAuthToken is true', () => {
    vi.mocked(getAccessToken).mockReturnValue('token-123');

    const requestHandler = getRequestHandler();
    const config = {
      headers: new AxiosHeaders(),
      skipAuthToken: true,
    } as InternalAxiosRequestConfig;

    const result = requestHandler(config);

    expect((result.headers as AxiosHeaders).get('Authorization')).toBeUndefined();
  });

  it('does not add Authorization header when access token is missing', () => {
    vi.mocked(getAccessToken).mockReturnValue(null);

    const requestHandler = getRequestHandler();
    const config = {
      headers: new AxiosHeaders(),
    } as InternalAxiosRequestConfig;

    const result = requestHandler(config);

    expect((result.headers as AxiosHeaders).get('Authorization')).toBeUndefined();
  });

  it('returns normalized error for non-401 responses', async () => {
    const responseHandler = getResponseErrorHandler();
    const error = createAxiosError(500, { url: '/applications' });

    await expect(responseHandler(error)).rejects.toEqual({
      normalized: true,
      source: error,
    });

    expect(normalizeApiError).toHaveBeenCalledWith(error);
  });

  it('clears tokens and rejects on 401 when refresh token is missing', async () => {
    vi.mocked(getRefreshToken).mockReturnValue(null);

    const responseHandler = getResponseErrorHandler();
    const error = createAxiosError(401, { url: '/applications' });

    await expect(responseHandler(error)).rejects.toEqual({
      normalized: true,
      source: error,
    });

    expect(clearAuthTokens).toHaveBeenCalledTimes(1);
    expect(setAuthTokens).not.toHaveBeenCalled();
  });

  it('does not refresh for auth endpoints', async () => {
    const responseHandler = getResponseErrorHandler();
    const error = createAxiosError(401, { url: '/auth/login' });

    await expect(responseHandler(error)).rejects.toEqual({
      normalized: true,
      source: error,
    });

    expect(getRefreshToken).not.toHaveBeenCalled();
    expect(clearAuthTokens).not.toHaveBeenCalled();
  });

  it('does not refresh when retry is already attempted', async () => {
    const responseHandler = getResponseErrorHandler();
    const error = createAxiosError(401, {
      url: '/applications',
      _retry: true,
    });

    await expect(responseHandler(error)).rejects.toEqual({
      normalized: true,
      source: error,
    });

    expect(getRefreshToken).not.toHaveBeenCalled();
  });

  it('does not refresh when skipAuthRefresh is enabled', async () => {
    const responseHandler = getResponseErrorHandler();
    const error = createAxiosError(401, {
      url: '/applications',
      skipAuthRefresh: true,
    });

    await expect(responseHandler(error)).rejects.toEqual({
      normalized: true,
      source: error,
    });

    expect(getRefreshToken).not.toHaveBeenCalled();
  });

  it('returns normalized error when config is missing', async () => {
    const responseHandler = getResponseErrorHandler();
    const error = {
      response: { status: 401 },
    } as AxiosError;

    await expect(responseHandler(error)).rejects.toEqual({
      normalized: true,
      source: error,
    });

    expect(getRefreshToken).not.toHaveBeenCalled();
  });
});
