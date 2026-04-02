import './App.css';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage, SignupPage, ProtectedRoute } from './features/auth';
import { Header } from './features/common/components';
import Dashboard from './pages/Dashboard';

const LandingPage = () => (
  <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
    <div className="flex flex-col items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-primary-900 mb-4">Application Hub</h1>
        <p className="text-lg text-primary-700 mb-8">
          Welcome to your application management platform
        </p>
        <div className="flex gap-4 justify-center">
          <a
            href="/login"
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Get Started
          </a>
          <a
            href="#learn"
            className="px-6 py-2 border border-primary-600 text-primary-600 rounded-lg hover:bg-primary-50 transition-colors"
          >
            Learn More
          </a>
        </div>
      </div>
    </div>
  </div>
);

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
      <Header />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
