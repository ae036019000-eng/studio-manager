import { useQuery } from '@tanstack/react-query';
import { reportsApi, rentalsApi } from '../services/api';
import Card, { StatCard } from '../components/Card';
import Table from '../components/Table';
import type { Rental } from '../types';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: reportsApi.getDashboard,
  });

  const { data: upcomingReturns = [], isLoading: returnsLoading } = useQuery({
    queryKey: ['upcoming-returns'],
    queryFn: rentalsApi.getUpcomingReturns,
  });

  const { data: activeRentals = [], isLoading: activeLoading } = useQuery({
    queryKey: ['active-rentals'],
    queryFn: rentalsApi.getActive,
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

  const rentalColumns = [
    { key: 'dress_name', header: 'שמלה' },
    { key: 'customer_name', header: 'לקוח/ה' },
    {
      key: 'end_date',
      header: 'תאריך החזרה',
      render: (r: Rental) => formatDate(r.end_date),
    },
    {
      key: 'customer_phone',
      header: 'טלפון',
    },
  ];

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
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-6 mb-6 lg:mb-10">
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
          title="הכנסות החודש"
          value={formatCurrency(stats?.monthlyRevenue || 0)}
          icon="◈"
          color="amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upcoming Returns */}
        <Card className="p-8" hover={false}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-gold-500 text-xl">◇</span>
            <h2 className="font-serif text-2xl font-semibold text-champagne-800">
              החזרות קרובות
            </h2>
          </div>
          <p className="text-champagne-700 text-sm mb-6">7 ימים קרובים</p>
          {returnsLoading ? (
            <div className="text-center py-8">
              <div className="text-gold-400 animate-pulse">◈</div>
            </div>
          ) : upcomingReturns.length === 0 ? (
            <div className="text-center py-8 text-champagne-600">
              אין החזרות קרובות
            </div>
          ) : (
            <Table
              columns={rentalColumns}
              data={upcomingReturns}
              keyField="id"
              emptyMessage="אין החזרות קרובות"
            />
          )}
        </Card>

        {/* Active Rentals */}
        <Card className="p-8" hover={false}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-gold-500 text-xl">◆</span>
            <h2 className="font-serif text-2xl font-semibold text-champagne-800">
              השכרות פעילות
            </h2>
          </div>
          <p className="text-champagne-700 text-sm mb-6">5 אחרונות</p>
          {activeLoading ? (
            <div className="text-center py-8">
              <div className="text-gold-400 animate-pulse">◈</div>
            </div>
          ) : (
            <Table
              columns={[
                { key: 'dress_name', header: 'שמלה' },
                { key: 'customer_name', header: 'לקוח/ה' },
                {
                  key: 'start_date',
                  header: 'מתאריך',
                  render: (r: Rental) => formatDate(r.start_date),
                },
                {
                  key: 'end_date',
                  header: 'עד תאריך',
                  render: (r: Rental) => formatDate(r.end_date),
                },
              ]}
              data={activeRentals.slice(0, 5)}
              keyField="id"
              emptyMessage="אין השכרות פעילות"
            />
          )}
        </Card>
      </div>
    </div>
  );
}
