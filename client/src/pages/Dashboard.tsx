import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportsApi, rentalsApi, appointmentsApi, customersApi, dressesApi, whatsappHelper } from '../services/api';
import Card, { StatCard } from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input, { Select, Textarea } from '../components/Input';
import type { Rental, Appointment, Customer, Dress } from '../types';

const appointmentTypes = [
  { value: 'fitting', label: 'מדידה' },
  { value: 'pickup', label: 'איסוף' },
  { value: 'return', label: 'החזרה' },
  { value: 'other', label: 'אחר' },
];

export default function Dashboard() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isNewCustomerMode, setIsNewCustomerMode] = useState(false);
  const [isWalkIn, setIsWalkIn] = useState(false);
  const [walkInName, setWalkInName] = useState('');
  const [formData, setFormData] = useState({
    customer_id: '',
    dress_id: '',
    type: 'fitting',
    date: '',
    time: '',
    notes: '',
  });
  const [newCustomerData, setNewCustomerData] = useState({
    name: '',
    phone: '',
  });

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

  const { data: tomorrowReminders = [] } = useQuery({
    queryKey: ['appointment-reminders'],
    queryFn: appointmentsApi.getReminders,
  });

  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: customersApi.getAll,
  });

  const { data: dresses = [] } = useQuery({
    queryKey: ['dresses'],
    queryFn: dressesApi.getAll,
  });

  const createAppointmentMutation = useMutation({
    mutationFn: appointmentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      queryClient.invalidateQueries({ queryKey: ['today-appointments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      closeModal();
    },
  });

  const createCustomerMutation = useMutation({
    mutationFn: customersApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      setFormData({ ...formData, customer_id: String(data.id) });
      setIsNewCustomerMode(false);
      setNewCustomerData({ name: '', phone: '' });
    },
  });

  const openModal = () => {
    setFormData({
      customer_id: '',
      dress_id: '',
      type: 'fitting',
      date: new Date().toISOString().split('T')[0],
      time: '',
      notes: '',
    });
    setIsNewCustomerMode(false);
    setNewCustomerData({ name: '', phone: '' });
    setIsWalkIn(false);
    setWalkInName('');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setIsNewCustomerMode(false);
    setIsWalkIn(false);
    setWalkInName('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let notes = formData.notes;
    if (isWalkIn && walkInName) {
      notes = `[לקוחה מזדמנת: ${walkInName}]${notes ? '\n' + notes : ''}`;
    }
    createAppointmentMutation.mutate({
      ...formData,
      notes,
      customer_id: formData.customer_id ? parseInt(formData.customer_id) : null,
      dress_id: formData.dress_id ? parseInt(formData.dress_id) : null,
    });
  };

  const handleCreateCustomer = () => {
    if (newCustomerData.name.trim()) {
      createCustomerMutation.mutate(newCustomerData);
    }
  };

  const handleCustomerChange = (value: string) => {
    if (value === 'new') {
      setIsNewCustomerMode(true);
      setIsWalkIn(false);
      setFormData({ ...formData, customer_id: '' });
    } else if (value === 'walk-in') {
      setIsNewCustomerMode(false);
      setIsWalkIn(true);
      setFormData({ ...formData, customer_id: '' });
    } else {
      setIsNewCustomerMode(false);
      setIsWalkIn(false);
      setFormData({ ...formData, customer_id: value });
    }
  };

  const customerOptions = [
    { value: '', label: 'בחר לקוח/ה' },
    { value: 'walk-in', label: 'לקוחה מזדמנת (ללא רישום)' },
    { value: 'new', label: '+ צור לקוחה חדשה' },
    ...customers.map((c: Customer) => ({ value: String(c.id), label: `${c.name}${c.phone ? ` - ${c.phone}` : ''}` })),
  ];

  const dressOptions = [
    { value: '', label: 'בחר שמלה (אופציונלי)' },
    ...dresses.map((d: Dress) => ({ value: String(d.id), label: d.name })),
  ];

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500 text-4xl animate-pulse">◈</div>
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

  const getDisplayName = (apt: Appointment) => {
    if (apt.customer_name) return apt.customer_name;
    if (apt.notes) {
      const match = apt.notes.match(/\[לקוחה מזדמנת: (.+?)\]/);
      if (match) return match[1];
    }
    return 'ללא לקוח';
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

  const sendAppointmentReminder = (apt: Appointment) => {
    const phone = apt.customer_phone;
    if (!phone) return;

    const date = new Date(apt.date).toLocaleDateString('he-IL');
    const name = getDisplayName(apt);
    let message = '';

    switch (apt.type) {
      case 'fitting':
        message = whatsappHelper.messages.fittingReminder(name, date, apt.time || undefined);
        break;
      case 'pickup':
        message = whatsappHelper.messages.pickupReminder(name, apt.dress_name || 'השמלה', date);
        break;
      case 'return':
        message = whatsappHelper.messages.returnReminder(name, apt.dress_name || 'השמלה', date);
        break;
      default:
        message = `שלום ${name},\nתזכורת לפגישה מחר (${date}).\n\nרחל - השכרת שמלות`;
    }

    const link = whatsappHelper.getLink(phone, message);
    window.open(link, '_blank');
  };

  return (
    <div className="animate-slide-up pb-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 lg:mb-10">
        <div>
          <h1 className="font-sans text-2xl lg:text-4xl font-semibold text-gray-900 mb-1 lg:mb-2">
            דשבורד
          </h1>
          <p className="text-gray-600 text-sm lg:text-base">סקירה כללית של הסטודיו</p>
        </div>
        <Button size="sm" onClick={openModal}>+ פגישה חדשה</Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 lg:gap-4 mb-6 lg:mb-10">
        <StatCard
          title="סה״כ שמלות"
          value={stats?.totalDresses || 0}
          icon="❖"
          color="default"
        />
        <StatCard
          title="שמלות פנויות"
          value={stats?.availableDresses || 0}
          icon="✓"
          color="success"
        />
        <StatCard
          title="השכרות פעילות"
          value={stats?.activeRentals || 0}
          icon="◆"
          color="info"
        />
        <StatCard
          title="פגישות היום"
          value={stats?.todayAppointments || 0}
          icon="▣"
          color="danger"
        />
        <StatCard
          title="הכנסות החודש"
          value={formatCurrency(stats?.monthlyRevenue || 0)}
          icon="◈"
          color="warning"
        />
      </div>

      {/* Tomorrow Reminders */}
      {tomorrowReminders.length > 0 && (
        <Card className="p-4 lg:p-6 mb-6 bg-amber-50 border-amber-200" hover={false}>
          <div className="flex items-center gap-2 mb-4">
            <span className="text-amber-600 text-lg">⏰</span>
            <h2 className="font-sans text-lg font-semibold text-gray-900">
              תזכורות למחר ({tomorrowReminders.length})
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {tomorrowReminders.map((apt: Appointment) => (
              <div key={apt.id} className="p-3 bg-white rounded-lg border border-amber-200 flex justify-between items-center">
                <div>
                  <span className="text-xs text-amber-600 font-medium">{getTypeLabel(apt.type)}</span>
                  <p className="text-sm font-medium text-gray-900">{getDisplayName(apt)}</p>
                  {apt.time && <p className="text-xs text-gray-500">{apt.time}</p>}
                </div>
                {apt.customer_phone && (
                  <button
                    onClick={() => sendAppointmentReminder(apt)}
                    className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                    title="שלח תזכורת בווצאפ"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-8">
        {/* Today's Appointments */}
        <Card className="p-4 lg:p-8" hover={false}>
          <div className="flex items-center gap-2 lg:gap-3 mb-4 lg:mb-6">
            <span className="text-gray-600 text-lg lg:text-xl">▣</span>
            <h2 className="font-sans text-lg lg:text-2xl font-semibold text-gray-900">
              פגישות היום
            </h2>
          </div>
          {appointmentsLoading ? (
            <div className="text-center py-8">
              <div className="text-gray-500 animate-pulse">◈</div>
            </div>
          ) : todayAppointments.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              אין פגישות היום
            </div>
          ) : (
            <div className="space-y-3">
              {todayAppointments.map((apt: Appointment) => (
                <div key={apt.id} className="p-3 bg-gradient-to-l from-gray-50 to-transparent rounded-lg border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-700 bg-gray-100 px-2 py-0.5 rounded-full">
                          {getTypeLabel(apt.type)}
                        </span>
                        {apt.time && (
                          <span className="text-xs text-gray-500">{apt.time}</span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-gray-900 mt-1">
                        {getDisplayName(apt)}
                      </p>
                      {apt.dress_name && (
                        <p className="text-xs text-gray-500">{apt.dress_name}</p>
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
            <span className="text-gray-600 text-lg lg:text-xl">◇</span>
            <h2 className="font-sans text-lg lg:text-2xl font-semibold text-gray-900">
              החזרות קרובות
            </h2>
          </div>
          <p className="text-gray-500 text-xs mb-4">7 ימים קרובים</p>
          {returnsLoading ? (
            <div className="text-center py-8">
              <div className="text-gray-500 animate-pulse">◈</div>
            </div>
          ) : upcomingReturns.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              אין החזרות קרובות
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingReturns.slice(0, 5).map((rental: Rental) => (
                <div key={rental.id} className="p-3 bg-gradient-to-l from-gray-50 to-transparent rounded-lg border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{rental.dress_name}</p>
                      <p className="text-xs text-gray-500">{rental.customer_name}</p>
                      <p className="text-xs text-gray-700 mt-1">{formatDate(rental.end_date)}</p>
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

      {/* Add Appointment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title="פגישה חדשה"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="סוג פגישה"
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            options={appointmentTypes}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="תאריך"
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              required
            />
            <Input
              label="שעה"
              type="time"
              value={formData.time}
              onChange={(e) => setFormData({ ...formData, time: e.target.value })}
            />
          </div>

          <Select
            label="לקוח/ה"
            value={isWalkIn ? 'walk-in' : formData.customer_id}
            onChange={(e) => handleCustomerChange(e.target.value)}
            options={customerOptions}
          />

          {isWalkIn && (
            <Input
              label="שם הלקוחה המזדמנת"
              value={walkInName}
              onChange={(e) => setWalkInName(e.target.value)}
              placeholder="שם לזיהוי"
            />
          )}

          {isNewCustomerMode && (
            <div className="p-4 bg-gray-50 rounded-lg space-y-3">
              <p className="text-sm font-medium text-gray-700">יצירת לקוחה חדשה</p>
              <Input
                label="שם"
                value={newCustomerData.name}
                onChange={(e) => setNewCustomerData({ ...newCustomerData, name: e.target.value })}
                placeholder="שם הלקוחה"
                required
              />
              <Input
                label="טלפון"
                value={newCustomerData.phone}
                onChange={(e) => setNewCustomerData({ ...newCustomerData, phone: e.target.value })}
                placeholder="050-0000000"
              />
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleCreateCustomer}
                  disabled={!newCustomerData.name.trim() || createCustomerMutation.isPending}
                >
                  {createCustomerMutation.isPending ? 'יוצר...' : 'צור לקוחה'}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => setIsNewCustomerMode(false)}
                >
                  ביטול
                </Button>
              </div>
            </div>
          )}

          <Select
            label="שמלה"
            value={formData.dress_id}
            onChange={(e) => setFormData({ ...formData, dress_id: e.target.value })}
            options={dressOptions}
          />

          <Textarea
            label="הערות"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={2}
            placeholder="הערות נוספות..."
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button type="button" variant="secondary" size="sm" onClick={closeModal}>
              ביטול
            </Button>
            <Button type="submit" size="sm" disabled={createAppointmentMutation.isPending}>
              הוסף
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
