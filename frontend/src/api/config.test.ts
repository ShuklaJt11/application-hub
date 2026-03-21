import { describe, expect, it } from 'vitest';

import apiConfig, { apiConfig as namedApiConfig } from './config';

describe('api config', () => {
  it('exports default and named config with the same values', () => {
    expect(apiConfig).toEqual(namedApiConfig);
  });

  it('uses normalized baseURL and numeric timeout', () => {
    expect(typeof apiConfig.baseURL).toBe('string');
    expect(apiConfig.baseURL.endsWith('/')).toBe(false);
    expect(typeof apiConfig.timeout).toBe('number');
    expect(apiConfig.timeout).toBeGreaterThan(0);
  });
});
