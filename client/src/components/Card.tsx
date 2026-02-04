interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export default function Card({ children, className = '', hover = true }: CardProps) {
  return (
    <div className={`
      bg-white rounded-xl border border-gray-200
      ${hover ? 'transition-shadow duration-200 hover:shadow-md' : ''}
      ${className}
    `}>
      {children}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: string;
  color?: 'default' | 'success' | 'info' | 'warning' | 'danger';
}

export function StatCard({ title, value, icon, color = 'default' }: StatCardProps) {
  const colorClasses = {
    default: 'bg-gray-50 border-gray-200',
    success: 'bg-emerald-50 border-emerald-200',
    info: 'bg-blue-50 border-blue-200',
    warning: 'bg-amber-50 border-amber-200',
    danger: 'bg-red-50 border-red-200',
  };

  return (
    <Card className={`p-4 ${colorClasses[color]} border`}>
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs text-gray-500 font-medium truncate">{title}</p>
          <p className="text-xl font-semibold mt-1 text-gray-900 truncate">{value}</p>
        </div>
        <div className="w-10 h-10 rounded-lg flex-shrink-0 flex items-center justify-center text-lg bg-white border border-gray-200">
          {icon}
        </div>
      </div>
    </Card>
  );
}
