import { Link, useLocation } from 'react-router-dom';

const menuItems = [
  { path: '/', label: 'דשבורד', icon: '◈' },
  { path: '/dresses', label: 'שמלות', icon: '❖' },
  { path: '/customers', label: 'לקוחות', icon: '✦' },
  { path: '/rentals', label: 'השכרות', icon: '◆' },
  { path: '/calendar', label: 'לוח שנה', icon: '▣' },
  { path: '/reports', label: 'דוחות', icon: '◇' },
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex min-h-screen bg-cream-100">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-l border-champagne-200 flex-shrink-0 shadow-soft">
        {/* Logo/Brand */}
        <div className="p-8 border-b border-champagne-100">
          <h1 className="font-serif text-3xl font-semibold text-gold-gradient">
            Studio Elegance
          </h1>
          <p className="text-champagne-700 text-sm mt-2 tracking-widest uppercase">
            השכרת שמלות יוקרה
          </p>
          <div className="gold-accent mt-4 w-16"></div>
        </div>

        {/* Navigation */}
        <nav className="mt-6 px-4">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-4 px-5 py-4 mb-2 rounded-xl transition-all duration-300 group ${
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
        <div className="absolute bottom-0 left-0 right-0 p-6">
          <div className="gold-accent"></div>
          <p className="text-center text-champagne-600 text-xs mt-4 tracking-wider">
            © 2024 Studio Elegance
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-10 max-w-7xl mx-auto animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
