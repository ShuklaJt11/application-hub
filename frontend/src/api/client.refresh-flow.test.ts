import { describe, expect, it, vi } from 'vitest';

type MockRequestConfig = {
  headers?: unknown;
  url?: string;
  _retry?: boolean;
  skipAuthRefresh?: boolean;
};

type MockResponseError = {
  config?: MockRequestConfig;
  response?: { status?: number };
};

type MockRequestInterceptor = (config: MockRequestConfig) => MockRequestConfig;
type MockResponseRejectedInterceptor = (error: MockResponseError) => Promise<unknown>;

type MockApiClientFn = ((config: MockRequestConfig) => Promise<unknown>) & {
  interceptors: {
    request: {
      use: (fulfilled: MockRequestInterceptor) => number;
    };
    response: {
      use: (fulfilled: unknown, rejected: MockResponseRejectedInterceptor) => number;
    };
  };
};

type MockAxiosState = {
  createMock: ReturnType<typeof vi.fn>;
  refreshPostMock: ReturnType<typeof vi.fn>;
  retryRequestMock: ReturnType<typeof vi.fn>;
  responseRejected?: MockResponseRejectedInterceptor;
};

const axiosState = vi.hoisted<MockAxiosState>(() => {
  const refreshPostMock = vi.fn();
  const retryRequestMock = vi.fn();

  const state: MockAxiosState = {
    createMock: vi.fn(),
    refreshPostMock,
    retryRequestMock,
    responseRejected: undefined,
  };

  const apiClient = vi.fn((config: MockRequestConfig) =>
    retryRequestMock(config)
  ) as unknown as MockApiClientFn;
  apiClient.interceptors = {
    request: {
      use: vi.fn(() => 0),
    },
    response: {
      use: vi.fn((_fulfilled: unknown, rejected: MockResponseRejectedInterceptor) => {
        state.responseRejected = rejected;
        return 0;
      }),
    },
  };

  const refreshClient = {
    post: refreshPostMock,
  };

  state.createMock
    .mockImplementationOnce(() => refreshClient)
    .mockImplementationOnce(() => apiClient);

  return state;
});

class MockAxiosHeaders {
  private readonly values = new Map<string, string>();

  static from(headers?: unknown): MockAxiosHeaders {
    if (headers instanceof MockAxiosHeaders) {
      return headers;
    }

    const instance = new MockAxiosHeaders();
    if (headers && typeof headers === 'object') {
      const entries = Object.entries(headers as Record<string, unknown>);
      entries.forEach(([key, value]) => {
        if (typeof value === 'string') {
          instance.set(key, value);
        }
      });
    }

    return instance;
  }

  set(key: string, value: string): void {
    this.values.set(key.toLowerCase(), value);
  }

  get(key: string): string | undefined {
    return this.values.get(key.toLowerCase());
  }
}

const tokenStorageMocks = vi.hoisted(() => ({
  clearAuthTokens: vi.fn(),
  getAccessToken: vi.fn(() => null),
  getRefreshToken: vi.fn(() => 'refresh-token'),
  setAuthTokens: vi.fn(),
}));

const normalizeApiErrorMock = vi.hoisted(() =>
  vi.fn((error: unknown) => ({ normalized: true, source: error }))
);

vi.mock('axios', () => {
  return {
    default: {
      create: axiosState.createMock,
      isAxiosError: () => true,
    },
    AxiosHeaders: MockAxiosHeaders,
    AxiosError: class MockAxiosError extends Error {},
  };
});

vi.mock('./token-storage', () => tokenStorageMocks);
vi.mock('./error-handler', () => ({ normalizeApiError: normalizeApiErrorMock }));

describe('api client refresh flow', () => {
  it('refreshes token and retries original request on 401', async () => {
    axiosState.refreshPostMock.mockResolvedValueOnce({
      data: {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      },
    });
    axiosState.retryRequestMock.mockResolvedValueOnce({ data: { ok: true } });

    await import('./client');

    const rejected = axiosState.responseRejected;
    expect(rejected).toBeDefined();

    const originalError: MockResponseError = {
      config: {
        headers: new MockAxiosHeaders(),
        url: '/applications',
      },
      response: {
        status: 401,
      },
    };

    const retriedResponse = await rejected!(originalError);

    expect(axiosState.refreshPostMock).toHaveBeenCalledWith('/auth/refresh', {
      refresh_token: 'refresh-token',
    });
    expect(tokenStorageMocks.setAuthTokens).toHaveBeenCalledWith({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'bearer',
    });
    expect(tokenStorageMocks.clearAuthTokens).not.toHaveBeenCalled();
    expect(axiosState.retryRequestMock).toHaveBeenCalledTimes(1);

    const retriedConfig = axiosState.retryRequestMock.mock.calls[0][0] as MockRequestConfig;
    expect(retriedConfig._retry).toBe(true);
    const retriedHeaders = retriedConfig.headers as MockAxiosHeaders;
    expect(retriedHeaders.get('Authorization')).toBe('Bearer new-access-token');
    expect(retriedResponse).toEqual({ data: { ok: true } });
  });
});
