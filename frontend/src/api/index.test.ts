import { describe, expect, it } from 'vitest';

import { apiClient, apiConfig, tokenStorageKeys } from './index';

describe('api index exports', () => {
  it('re-exports apiConfig with expected shape', () => {
    expect(apiConfig).toHaveProperty('baseURL');
    expect(apiConfig).toHaveProperty('timeout');
  });

  it('re-exports apiClient instance', () => {
    expect(apiClient).toBeTruthy();
    expect(typeof apiClient.get).toBe('function');
    expect(typeof apiClient.post).toBe('function');
  });

  it('re-exports token storage keys', () => {
    expect(tokenStorageKeys.access).toBe('apphub_access_token');
    expect(tokenStorageKeys.refresh).toBe('apphub_refresh_token');
  });
});
