import axios, { AxiosRequestConfig, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add API key and user token to all requests
apiClient.interceptors.request.use((config) => {
  if (API_KEY) {
    config.headers['X-API-Key'] = API_KEY;
  }

  // Add user token if available (for user-specific document access)
  if (typeof window !== 'undefined') {
    const userToken = localStorage.getItem('auth_token');
    if (userToken) {
      config.headers['X-User-Token'] = userToken;
    }
  }

  return config;
});

// Handle 401 errors (expired/invalid token) by clearing auth and reloading
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      // Only redirect for document/query endpoints that require user token
      const url = error.config?.url || '';
      const requiresUserToken = url.includes('/documents') || url.includes('/query');

      if (requiresUserToken && localStorage.getItem('auth_token')) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

// Custom instance for orval
export const customInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  const source = axios.CancelToken.source();
  const promise = apiClient({
    ...config,
    cancelToken: source.token,
  }).then(({ data }) => data);

  // @ts-ignore - Add cancel method for react-query
  promise.cancel = () => {
    source.cancel('Query was cancelled');
  };

  return promise;
};

// Error handling helper
export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export const isApiError = (error: unknown): error is AxiosError<ApiError> => {
  return axios.isAxiosError(error);
};

export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error) && error.response?.data) {
    const data = error.response.data;
    if (typeof data === 'object' && 'detail' in data) {
      const detail = (data as any).detail;
      if (typeof detail === 'string') {
        return detail;
      }
      if (typeof detail === 'object' && 'message' in detail) {
        return detail.message;
      }
    }
    if ('message' in data) {
      return data.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};
