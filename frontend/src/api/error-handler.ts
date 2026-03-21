/**
 * Normalized API error helpers.
 */

import axios, { AxiosError } from 'axios';

export interface ApiClientError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
  isNetworkError: boolean;
  isAuthError: boolean;
  originalError: unknown;
}

const extractMessageFromDetail = (detail: unknown): string | null => {
  if (typeof detail === 'string' && detail.length > 0) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const firstItem = detail[0] as Record<string, unknown>;
    if (typeof firstItem?.msg === 'string') {
      return firstItem.msg;
    }
  }

  return null;
};

export const normalizeApiError = (error: unknown): ApiClientError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: unknown; message?: string }>;
    const status = axiosError.response?.status;
    const detail = axiosError.response?.data?.detail;
    const messageFromDetail = extractMessageFromDetail(detail);
    const message =
      messageFromDetail ||
      axiosError.response?.data?.message ||
      axiosError.message ||
      'An unexpected API error occurred.';

    return {
      message,
      status,
      code: axiosError.code,
      details: detail,
      isNetworkError: !axiosError.response,
      isAuthError: status === 401,
      originalError: error,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      isNetworkError: false,
      isAuthError: false,
      originalError: error,
    };
  }

  return {
    message: 'An unknown error occurred.',
    isNetworkError: false,
    isAuthError: false,
    originalError: error,
  };
};

export const isApiClientError = (error: unknown): error is ApiClientError => {
  if (!error || typeof error !== 'object') {
    return false;
  }

  const candidate = error as Partial<ApiClientError>;
  return (
    typeof candidate.message === 'string' &&
    typeof candidate.isNetworkError === 'boolean' &&
    typeof candidate.isAuthError === 'boolean'
  );
};
