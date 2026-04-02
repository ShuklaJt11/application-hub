import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth';

const Header = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const mobileMenuContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isMobileMenuOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMobileMenuOpen(false);
      }
    };

    const handleDocumentMouseDown = (event: MouseEvent) => {
      const target = event.target as Node | null;

      if (
        target &&
        mobileMenuContainerRef.current &&
        !mobileMenuContainerRef.current.contains(target)
      ) {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleDocumentMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleDocumentMouseDown);
    };
  }, [isMobileMenuOpen]);

  const handleLogout = async () => {
    setIsMobileMenuOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <>
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-white/20 backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <header className="relative z-50 bg-white shadow-md">
        <div ref={mobileMenuContainerRef} className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="text-2xl font-bold text-primary-900">
              Application Hub
            </Link>

            <div className="hidden md:flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <a
                    href="#profile"
                    className="px-4 py-2 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors"
                  >
                    Profile
                  </a>
                  <button
                    onClick={handleLogout}
                    disabled={isLoading}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Logging out...' : 'Logout'}
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  className="px-4 py-2 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors"
                >
                  Login
                </Link>
              )}
            </div>

            <button
              type="button"
              onClick={() => setIsMobileMenuOpen((prev) => !prev)}
              className="md:hidden inline-flex items-center justify-center rounded-lg p-2 text-primary-900 hover:bg-primary-50"
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-header-menu"
            >
              <svg
                className="h-6 w-6"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          {isMobileMenuOpen && (
            <div
              id="mobile-header-menu"
              className="md:hidden absolute right-4 top-[calc(100%+0.5rem)] w-56 rounded-lg border border-primary-100 bg-white p-3 shadow-lg"
            >
              <div className="flex flex-col gap-3">
                {isAuthenticated ? (
                  <>
                    <a
                      href="#profile"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="px-4 py-2 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors"
                    >
                      Profile
                    </a>
                    <button
                      onClick={handleLogout}
                      disabled={isLoading}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed text-left"
                    >
                      {isLoading ? 'Logging out...' : 'Logout'}
                    </button>
                  </>
                ) : (
                  <Link
                    to="/login"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="px-4 py-2 text-primary-700 rounded-lg hover:bg-primary-50 transition-colors"
                  >
                    Login
                  </Link>
                )}
              </div>
            </div>
          )}
        </div>
      </header>
    </>
  );
};

export default Header;
