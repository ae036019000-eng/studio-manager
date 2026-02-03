import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import Table from '../components/Table';
import type { PopularDress, ReturningCustomer, RevenueReport } from '../types';

export default function Reports() {
  const { data: revenue = [] } = useQuery({
    queryKey: ['revenue'],
    queryFn: () => reportsApi.getRevenue(),
  });

  const { data: popularDresses = [] } = useQuery({
    queryKey: ['popular-dresses'],
    queryFn: reportsApi.getPopularDresses,
  });

  const { data: returningCustomers = [] } = useQuery({
    queryKey: ['returning-customers'],
    queryFn: reportsApi.getReturningCustomers,
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('he-IL', {
      style: 'currency',
      currency: 'ILS',
    }).format(amount);
  };

  const formatMonth = (monthStr: string) => {
    if (!monthStr) return '';
    const [year, month] = monthStr.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1);
    return date.toLocaleDateString('he-IL', { year: 'numeric', month: 'long' });
  };

  const revenueColumns = [
    {
      key: 'month',
      header: 'חודש',
      render: (r: RevenueReport) => formatMonth(r.month),
    },
    {
      key: 'total',
      header: 'סה״כ הכנסות',
      render: (r: RevenueReport) => (
        <span className="font-semibold text-gold-600">{formatCurrency(r.total)}</span>
      ),
    },
    {
      key: 'payment_count',
      header: 'מספר תשלומים',
    },
  ];

  const dressColumns = [
    { key: 'name', header: 'שם השמלה' },
    { key: 'rental_count', header: 'מספר השכרות' },
    {
      key: 'total_revenue',
      header: 'סה״כ הכנסות',
      render: (d: PopularDress) => (
        <span className="font-semibold text-gold-600">{formatCurrency(d.total_revenue)}</span>
      ),
    },
  ];

  const customerColumns = [
    { key: 'name', header: 'שם' },
    { key: 'phone', header: 'טלפון' },
    { key: 'rental_count', header: 'מספר השכרות' },
    {
      key: 'total_spent',
      header: 'סה״כ הוצאות',
      render: (c: ReturningCustomer) => (
        <span className="font-semibold text-gold-600">{formatCurrency(c.total_spent)}</span>
      ),
    },
  ];

  return (
    <div className="animate-slide-up">
      {/* Header */}
      <div className="flex justify-between items-start mb-10">
        <div>
          <h1 className="font-serif text-4xl font-semibold text-champagne-800 mb-2">
            דוחות
          </h1>
          <p className="text-champagne-700">סטטיסטיקות וניתוח נתונים</p>
          <div className="gold-accent mt-4 w-16"></div>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" size="sm" onClick={() => reportsApi.exportData('rentals')}>
            ייצוא השכרות
          </Button>
          <Button variant="secondary" size="sm" onClick={() => reportsApi.exportData('customers')}>
            ייצוא לקוחות
          </Button>
          <Button variant="secondary" size="sm" onClick={() => reportsApi.exportData('payments')}>
            ייצוא תשלומים
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Revenue Report */}
        <Card className="p-8" hover={false}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-gold-500 text-xl">◈</span>
            <h2 className="font-serif text-2xl font-semibold text-champagne-800">
              הכנסות לפי חודש
            </h2>
          </div>
          <Table
            columns={revenueColumns}
            data={revenue}
            keyField="month"
            emptyMessage="אין נתוני הכנסות"
          />
        </Card>

        {/* Popular Dresses */}
        <Card className="p-8" hover={false}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-gold-500 text-xl">❖</span>
            <h2 className="font-serif text-2xl font-semibold text-champagne-800">
              שמלות פופולריות
            </h2>
          </div>
          <Table
            columns={dressColumns}
            data={popularDresses.filter((d: PopularDress) => d.rental_count > 0)}
            keyField="id"
            emptyMessage="אין נתונים"
          />
        </Card>

        {/* Returning Customers */}
        <Card className="p-8 lg:col-span-2" hover={false}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-gold-500 text-xl">✦</span>
            <h2 className="font-serif text-2xl font-semibold text-champagne-800">
              לקוחות חוזרים
            </h2>
          </div>
          <Table
            columns={customerColumns}
            data={returningCustomers}
            keyField="id"
            emptyMessage="אין לקוחות חוזרים"
          />
        </Card>
      </div>
    </div>
  );
}
