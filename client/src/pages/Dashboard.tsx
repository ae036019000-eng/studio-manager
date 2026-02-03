import { useQuery } from '@tanstack/react-query';
import { reportsApi, rentalsApi, appointmentsApi, whatsappHelper } from '../services/api';
import Card, { StatCard } from '../components/Card';
import type { Rental, Appointment } from '../types';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: reportsApi.getDashboard,
  });

  const { data: upcomingReturns = [], isLoading: returnsLoading } = useQuery({
    queryKey: ['upcoming-returns'],
    queryFn: rentalsApi.getUpcomingReturns,
  });

  const { data: todayAppointments = [], isLoading: appointmentsLoading } = useQuery({
    queryKey: ['today-appointments'],
    queryFn: appointmentsApi.getToday,
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gold-400 text-4xl animate-pulse">◈</div>
      </div>
    );
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('he-IL');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
    }).format(amount);
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      fitting: 'מדידה',
      pickup: 'איסוף',
      return: 'החזרה',
      other: 'אחר',
    };
    return labels[type] || type;
  };

  const sendReturnReminder = (rental: Rental) => {
    if (!rental.customer_phone) return;
    const date = formatDate(rental.end_date);
    const message = whatsappHelper.messages.returnReminder(
      rental.customer_name || 'לקוח/ה יקר/ה',
      rental.dress_name || 'השמלה',
      date
    );
    const link = whatsappHelper.getLink(rental.customer_phone, message);
    window.open(link, '_blank');
  };

  return (
    <div className="animate-slide-up pb-20 lg:pb-0">
      {/* Header */}
      <div className="mb-6 lg:mb-10">
        <h1 className="font-serif text-2xl lg:text-4xl font-semibold text-champagne-800 mb-1 lg:mb-2">
          דשבורד
        </h1>
        <p className="text-champagne-700 text-sm lg:text-base">סקירה כללית של הסטודיו</p>
        <div className="gold-accent mt-3 lg:mt-4 w-16 lg:w-20"></div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 lg:gap-4 mb-6 lg:mb-10">
        <StatCard
          title="סה״כ שמלות"
          value={stats?.totalDresses || 0}
          icon="❖"
          color="gold"
        />
        <StatCard
          title="שמלות פנויות"
          value={stats?.availableDresses || 0}
          icon="✓"
          color="emerald"
        />
        <StatCard
          title="השכרות פעילות"
          value={stats?.activeRentals || 0}
          icon="◆"
          color="sky"
        />
        <StatCard
          title="פגישות היום"
          value={stats?.todayAppointments || 0}
          icon="▣"
          color="rose"
        />
        <StatCard
          title="הכנסות החודש"
          value={formatCurrency(stats?.monthlyRevenue || 0)}
          icon="◈"
          color="amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-8">
        {/* Today's Appointments */}
        <Card className="p-4 lg:p-8" hover={false}>
          <div className="flex items-center gap-2 lg:gap-3 mb-4 lg:mb-6">
            <span className="text-gold-500 text-lg lg:text-xl">▣</span>
            <h2 className="font-serif text-lg lg:text-2xl font-semibold text-champagne-800">
              פגישות היום
            </h2>
          </div>
          {appointmentsLoading ? (
            <div className="text-center py-8">
              <div className="text-gold-400 animate-pulse">◈</div>
            </div>
          ) : todayAppointments.length === 0 ? (
            <div className="text-center py-8 text-champagne-600 text-sm">
              אין פגישות היום
            </div>
          ) : (
            <div className="space-y-3">
              {todayAppointments.map((apt: Appointment) => (
                <div key={apt.id} className="p-3 bg-gradient-to-l from-champagne-50 to-transparent rounded-lg border border-champagne-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gold-600 bg-gold-50 px-2 py-0.5 rounded-full">
                          {getTypeLabel(apt.type)}
                        </span>
                        {apt.time && (
                          <span className="text-xs text-champagne-600">{apt.time}</span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-champagne-800 mt-1">
                        {apt.customer_name || 'ללא לקוח'}
                      </p>
                      {apt.dress_name && (
                        <p className="text-xs text-champagne-600">{apt.dress_name}</p>
                      )}
                    </div>
                    {apt.customer_phone && (
                      <a
                        href={whatsappHelper.getLink(apt.customer_phone, `שלום ${apt.customer_name}, `)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-600 hover:text-green-700 p-2"
                      >
                        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Upcoming Returns */}
        <Card className="p-4 lg:p-8" hover={false}>
          <div className="flex items-center gap-2 lg:gap-3 mb-4 lg:mb-6">
            <span className="text-gold-500 text-lg lg:text-xl">◇</span>
            <h2 className="font-serif text-lg lg:text-2xl font-semibold text-champagne-800">
              החזרות קרובות
            </h2>
          </div>
          <p className="text-champagne-600 text-xs mb-4">7 ימים קרובים</p>
          {returnsLoading ? (
            <div className="text-center py-8">
              <div className="text-gold-400 animate-pulse">◈</div>
            </div>
          ) : upcomingReturns.length === 0 ? (
            <div className="text-center py-8 text-champagne-600 text-sm">
              אין החזרות קרובות
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingReturns.slice(0, 5).map((rental: Rental) => (
                <div key={rental.id} className="p-3 bg-gradient-to-l from-champagne-50 to-transparent rounded-lg border border-champagne-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-champagne-800">{rental.dress_name}</p>
                      <p className="text-xs text-champagne-600">{rental.customer_name}</p>
                      <p className="text-xs text-gold-600 mt-1">{formatDate(rental.end_date)}</p>
                    </div>
                    {rental.customer_phone && (
                      <button
                        onClick={() => sendReturnReminder(rental)}
                        className="text-green-600 hover:text-green-700 p-2"
                        title="שלח תזכורת"
                      >
                        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
