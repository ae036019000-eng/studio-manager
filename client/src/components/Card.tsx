interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export default function Card({ children, className = '', hover = true }: CardProps) {
  return (
    <div className={`
      bg-white rounded-2xl shadow-soft border border-champagne-100
      ${hover ? 'transition-all duration-400 ease-out hover:shadow-soft-lg hover:-translate-y-0.5' : ''}
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
  color?: 'gold' | 'emerald' | 'sky' | 'amber' | 'rose';
}

export function StatCard({ title, value, icon, color = 'gold' }: StatCardProps) {
  const colorClasses = {
    gold: 'from-gold-50 to-gold-100 text-gold-600 border-gold-200',
    emerald: 'from-emerald-50 to-emerald-100 text-emerald-600 border-emerald-200',
    sky: 'from-sky-50 to-sky-100 text-sky-600 border-sky-200',
    amber: 'from-amber-50 to-amber-100 text-amber-600 border-amber-200',
    rose: 'from-rose-50 to-rose-100 text-rose-600 border-rose-200',
  };

  const iconBgClasses = {
    gold: 'bg-gradient-to-br from-gold-100 to-gold-200',
    emerald: 'bg-gradient-to-br from-emerald-100 to-emerald-200',
    sky: 'bg-gradient-to-br from-sky-100 to-sky-200',
    amber: 'bg-gradient-to-br from-amber-100 to-amber-200',
    rose: 'bg-gradient-to-br from-rose-100 to-rose-200',
  };

  return (
    <Card className={`p-6 bg-gradient-to-br ${colorClasses[color]} border`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-champagne-600 font-medium tracking-wide">{title}</p>
          <p className="text-3xl font-serif font-bold mt-2 text-champagne-800">{value}</p>
        </div>
        <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl ${iconBgClasses[color]} shadow-inner-soft`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}
