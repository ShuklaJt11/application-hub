/**
 * Axios API client with auth and refresh-token handling.
 */

import axios, { AxiosError, AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';

import type { AuthTokens } from '@/types';

import apiConfig from './config';
import { normalizeApiError } from './error-handler';
import { clearAuthSession, getAccessToken, getRefreshToken, setAuthTokens } from './token-storage';

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
  skipAuthRefresh?: boolean;
  skipAuthToken?: boolean;
};

const shouldSkipRefresh = (url?: string): boolean => {
  if (!url) {
    return false;
  }

  return /\/auth\/(login|signup|refresh|logout)$/.test(url);
};

const refreshClient = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
});

const refreshAccessToken = async (refreshToken: string): Promise<string | null> => {
  try {
    const response = await refreshClient.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const tokens = response.data;
    setAuthTokens(tokens);
    return tokens.access_token;
  } catch {
    clearAuthSession();
    return null;
  }
};

let refreshPromise: Promise<string | null> | null = null;

export const apiClient = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const requestConfig = config as RetryableRequestConfig;
  if (requestConfig.skipAuthToken) {
    return requestConfig;
  }

  const accessToken = getAccessToken();
  if (!accessToken) {
    return requestConfig;
  }

  const headers = AxiosHeaders.from(requestConfig.headers);
  headers.set('Authorization', `Bearer ${accessToken}`);
  requestConfig.headers = headers;

  return requestConfig;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const requestConfig = error.config as RetryableRequestConfig | undefined;
    const status = error.response?.status;

    if (
      !requestConfig ||
      status !== 401 ||
      requestConfig._retry ||
      requestConfig.skipAuthRefresh ||
      shouldSkipRefresh(requestConfig.url)
    ) {
      return Promise.reject(normalizeApiError(error));
    }

    requestConfig._retry = true;

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearAuthSession();
      return Promise.reject(normalizeApiError(error));
    }

    refreshPromise ??= refreshAccessToken(refreshToken).finally(() => {
      refreshPromise = null;
    });

    const newAccessToken = await refreshPromise;
    if (!newAccessToken) {
      return Promise.reject(normalizeApiError(error));
    }

    const headers = AxiosHeaders.from(requestConfig.headers);
    headers.set('Authorization', `Bearer ${newAccessToken}`);
    requestConfig.headers = headers;

    return apiClient(requestConfig);
  }
);

export default apiClient;
