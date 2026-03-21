import { describe, expect, it } from 'vitest';

import { AxiosError, AxiosHeaders } from 'axios';

import { isApiClientError, normalizeApiError } from './error-handler';

describe('error-handler', () => {
  it('normalizes axios errors with string detail', () => {
    const error = new AxiosError(
      'Request failed',
      'ERR_BAD_REQUEST',
      { headers: new AxiosHeaders() },
      undefined,
      {
        status: 400,
        statusText: 'Bad Request',
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: { detail: 'Invalid payload' },
      }
    );

    const normalized = normalizeApiError(error);

    expect(normalized.message).toBe('Invalid payload');
    expect(normalized.status).toBe(400);
    expect(normalized.code).toBe('ERR_BAD_REQUEST');
    expect(normalized.isAuthError).toBe(false);
    expect(normalized.isNetworkError).toBe(false);
    expect(isApiClientError(normalized)).toBe(true);
  });

  it('normalizes axios validation detail arrays', () => {
    const error = new AxiosError(
      'Validation failed',
      'ERR_BAD_REQUEST',
      { headers: new AxiosHeaders() },
      undefined,
      {
        status: 422,
        statusText: 'Unprocessable Entity',
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: {
          detail: [{ msg: 'Email is required', type: 'value_error.missing' }],
        },
      }
    );

    const normalized = normalizeApiError(error);

    expect(normalized.message).toBe('Email is required');
    expect(normalized.status).toBe(422);
  });

  it('normalizes unknown values safely', () => {
    const normalized = normalizeApiError('bad');

    expect(normalized.message).toBe('An unknown error occurred.');
    expect(normalized.isNetworkError).toBe(false);
    expect(normalized.isAuthError).toBe(false);
    expect(isApiClientError(normalized)).toBe(true);
  });

  it('marks axios errors without response as network errors', () => {
    const error = new AxiosError('Network Error', 'ERR_NETWORK', {
      headers: new AxiosHeaders(),
    });

    const normalized = normalizeApiError(error);

    expect(normalized.message).toBe('Network Error');
    expect(normalized.status).toBeUndefined();
    expect(normalized.isNetworkError).toBe(true);
    expect(normalized.isAuthError).toBe(false);
  });

  it('normalizes native Error instances', () => {
    const normalized = normalizeApiError(new Error('Boom'));

    expect(normalized.message).toBe('Boom');
    expect(normalized.isNetworkError).toBe(false);
    expect(normalized.isAuthError).toBe(false);
  });

  it('returns false for invalid type guard candidates', () => {
    expect(isApiClientError(null)).toBe(false);
    expect(isApiClientError({ message: 'x' })).toBe(false);
  });
});
