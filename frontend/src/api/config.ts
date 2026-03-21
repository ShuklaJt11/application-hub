/**
 * API Configuration
 * Centralized API client setup with environment variables
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10);

export const apiConfig = {
  baseURL: API_URL,
  timeout: API_TIMEOUT,
};

export default apiConfig;
