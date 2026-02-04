import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const menuItems = [
  { path: '/', label: 'דשבורד', icon: '◈' },
  { path: '/dresses', label: 'שמלות', icon: '❖' },
  { path: '/customers', label: 'לקוחות', icon: '✦' },
  { path: '/rentals', label: 'השכרות', icon: '◆' },
  { path: '/calendar', label: 'לוח שנה', icon: '▣' },
  { path: '/reports', label: 'דוחות', icon: '◇' },
  { path: '/settings', label: 'הגדרות', icon: '⚙' },
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-cream-100">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-champagne-200 z-50 px-4 py-3 flex items-center justify-between">
        <img src="/logo.jpg" alt="Rachel" className="h-8 object-contain" />
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-champagne-100 transition-colors"
        >
          <svg className="w-6 h-6 text-champagne-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {isMobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/30 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - Desktop & Mobile */}
      <aside className={`
        fixed lg:relative top-0 right-0 h-full w-72 bg-white border-l border-champagne-200 shadow-soft z-50
        transform transition-transform duration-300 ease-out
        ${isMobileMenuOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
        lg:flex-shrink-0
      `}>
        {/* Logo/Brand */}
        <div className="p-6 lg:p-8 border-b border-champagne-100 mt-14 lg:mt-0">
          <img src="/logo.jpg" alt="Rachel" className="h-12 lg:h-16 object-contain" />
          <p className="text-champagne-700 text-sm mt-2 tracking-widest uppercase">
            השכרת שמלות יוקרה
          </p>
          <div className="gold-accent mt-4 w-16"></div>
        </div>

        {/* Navigation */}
        <nav className="mt-4 lg:mt-6 px-3 lg:px-4">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center gap-3 lg:gap-4 px-4 lg:px-5 py-3 lg:py-4 mb-2 rounded-xl transition-all duration-300 group ${
                  isActive
                    ? 'bg-gradient-to-l from-gold-50 to-gold-100 text-gold-700 shadow-sm'
                    : 'text-champagne-600 hover:bg-champagne-50 hover:text-champagne-800'
                }`}
              >
                <span className={`text-lg transition-transform duration-300 ${
                  isActive ? 'text-gold-500' : 'text-champagne-600 group-hover:text-gold-400'
                } group-hover:scale-110`}>
                  {item.icon}
                </span>
                <span className={`font-medium tracking-wide ${
                  isActive ? 'font-semibold' : ''
                }`}>
                  {item.label}
                </span>
                {isActive && (
                  <div className="mr-auto w-1.5 h-1.5 rounded-full bg-gold-500"></div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer decoration */}
        <div className="absolute bottom-0 left-0 right-0 p-6 hidden lg:block">
          <div className="gold-accent"></div>
          <p className="text-center text-champagne-600 text-xs mt-4 tracking-wider">
            © 2024 Rachel
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto pt-14 lg:pt-0">
        <div className="p-4 lg:p-10 max-w-7xl mx-auto animate-fade-in">
          {children}
        </div>
      </main>

    </div>
  );
}
