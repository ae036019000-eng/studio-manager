import { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export default function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-champagne-900/30 backdrop-blur-sm transition-opacity animate-fade-in"
          onClick={onClose}
        />

        {/* Modal */}
        <div
          className={`
            relative bg-white rounded-2xl shadow-soft-lg w-full ${sizeClasses[size]}
            transform transition-all animate-scale-in
            border border-champagne-100
          `}
        >
          {/* Header */}
          <div className="px-8 py-6 border-b border-champagne-100">
            <div className="flex items-center justify-between">
              <h3 className="font-serif text-2xl font-semibold text-champagne-800">{title}</h3>
              <button
                onClick={onClose}
                className="w-10 h-10 rounded-xl flex items-center justify-center
                         text-champagne-400 hover:text-champagne-600
                         hover:bg-champagne-100 transition-all duration-300"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="gold-accent mt-4 w-12"></div>
          </div>

          {/* Content */}
          <div className="px-8 py-6">{children}</div>
        </div>
      </div>
    </div>
  );
}
