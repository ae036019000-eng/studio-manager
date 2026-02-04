import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const menuItems = [
  { path: '/', label: 'דשבורד' },
  { path: '/dresses', label: 'שמלות' },
  { path: '/customers', label: 'לקוחות' },
  { path: '/rentals', label: 'השכרות' },
  { path: '/calendar', label: 'לוח שנה' },
  { path: '/reports', label: 'דוחות' },
  { path: '/settings', label: 'הגדרות' },
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with menu button */}
      <div className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-40 px-4 py-3 flex items-center justify-center">
        {/* Menu button on right */}
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="absolute right-4 p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {isMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
        {/* Large centered logo */}
        <img src="/logo.jpg" alt="Rachel" className="h-20 object-contain" />
      </div>

      {/* Menu Overlay */}
      {isMenuOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40"
          onClick={() => setIsMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 right-0 h-full w-64 bg-white border-l border-gray-200 z-50
        transform transition-transform duration-300 ease-out
        ${isMenuOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        {/* Logo/Brand */}
        <div className="p-8 border-b border-gray-100 flex flex-col items-center">
          <img src="/logo.jpg" alt="Rachel" className="h-24 object-contain" />
          <p className="text-gray-400 text-xs mt-3 tracking-widest uppercase">
            השכרת שמלות
          </p>
        </div>

        {/* Navigation */}
        <nav className="mt-4 px-3">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={`block px-4 py-3 mb-1 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <span className="font-medium text-sm">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main content */}
      <main className="pt-28">
        <div className="p-4 lg:p-8 max-w-6xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
