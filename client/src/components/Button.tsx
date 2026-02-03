interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export default function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  ...props
}: ButtonProps) {
  const baseClasses = `
    font-medium rounded-xl transition-all duration-300 ease-out
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    transform hover:scale-[1.02] active:scale-[0.98]
  `;

  const variantClasses = {
    primary: `
      bg-gradient-to-r from-gold-500 to-gold-600 text-white
      hover:from-gold-600 hover:to-gold-700
      focus:ring-gold-400 shadow-gold hover:shadow-lg
    `,
    secondary: `
      bg-champagne-50 text-champagne-700 border border-champagne-300
      hover:bg-champagne-100 hover:border-champagne-400
      focus:ring-champagne-300
    `,
    danger: `
      bg-gradient-to-r from-red-400 to-red-500 text-white
      hover:from-red-500 hover:to-red-600
      focus:ring-red-300 shadow-sm hover:shadow-md
    `,
    success: `
      bg-gradient-to-r from-emerald-400 to-emerald-500 text-white
      hover:from-emerald-500 hover:to-emerald-600
      focus:ring-emerald-300 shadow-sm hover:shadow-md
    `,
    ghost: `
      text-champagne-600 hover:text-gold-600
      hover:bg-gold-50 focus:ring-gold-200
    `,
  };

  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
