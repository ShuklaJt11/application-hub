/**
 * Authentication feature exports
 */

// Pages
export { default as LoginPage } from './pages/LoginPage';
export { default as SignupPage } from './pages/SignupPage';

// Components
export { default as ProtectedRoute } from './components/ProtectedRoute';

// Context and Hooks
export { AuthProvider, useAuth } from './context';

// Services
export { authService } from './services/auth';
export type { SignupCredentials } from './services/auth';

// Schemas
export { loginSchema, signupSchema } from './schemas';
export type { LoginFormData, SignupFormData } from './schemas';
