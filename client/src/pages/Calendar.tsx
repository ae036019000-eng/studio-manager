import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import { reportsApi, appointmentsApi, customersApi, dressesApi, whatsappHelper } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input, { Select, Textarea } from '../components/Input';
import type { Appointment, Customer, Dress } from '../types';

const appointmentTypes = [
  { value: 'fitting', label: 'מדידה' },
  { value: 'pickup', label: 'איסוף' },
  { value: 'return', label: 'החזרה' },
  { value: 'other', label: 'אחר' },
];

export default function Calendar() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    customer_id: '',
    dress_id: '',
    type: 'fitting',
    date: '',
    time: '',
    notes: '',
  });

  const { data: events = [], isLoading } = useQuery({
    queryKey: ['calendar-events'],
    queryFn: reportsApi.getCalendarEvents,
  });

  const { data: todayAppointments = [] } = useQuery({
    queryKey: ['today-appointments'],
    queryFn: appointmentsApi.getToday,
  });

  const { data: reminders = [] } = useQuery({
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

  const createMutation = useMutation({
    mutationFn: appointmentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      queryClient.invalidateQueries({ queryKey: ['today-appointments'] });
      queryClient.invalidateQueries({ queryKey: ['appointment-reminders'] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: appointmentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
      queryClient.invalidateQueries({ queryKey: ['today-appointments'] });
    },
  });

  const markReminderSentMutation = useMutation({
    mutationFn: appointmentsApi.markReminderSent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointment-reminders'] });
    },
  });

  const openModal = (date?: string) => {
    setFormData({
      customer_id: '',
      dress_id: '',
      type: 'fitting',
      date: date || new Date().toISOString().split('T')[0],
      time: '',
      notes: '',
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      ...formData,
      customer_id: formData.customer_id ? parseInt(formData.customer_id) : null,
      dress_id: formData.dress_id ? parseInt(formData.dress_id) : null,
    });
  };

  const handleDateClick = (info: any) => {
    openModal(info.dateStr);
  };

  const handleEventClick = (info: any) => {
    const props = info.event.extendedProps;
    if (props.type === 'appointment') {
      const id = parseInt(info.event.id.replace('appointment-', ''));
      if (confirm(`${props.appointmentType === 'fitting' ? 'מדידה' : props.appointmentType === 'pickup' ? 'איסוף' : props.appointmentType === 'return' ? 'החזרה' : 'פגישה'}${props.customerName ? ` - ${props.customerName}` : ''}\n${props.time ? `שעה: ${props.time}` : ''}\n\nלמחוק את הפגישה?`)) {
        deleteMutation.mutate(id);
      }
    } else {
      alert(`שמלה: ${props.dressName}\nלקוח/ה: ${props.customerName}\nסטטוס: ${props.status === 'active' ? 'פעיל' : 'הושלם'}`);
    }
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

  const sendWhatsAppReminder = (appointment: Appointment) => {
    if (!appointment.customer_phone) {
      alert('אין מספר טלפון ללקוח/ה');
      return;
    }

    const date = new Date(appointment.date).toLocaleDateString('he-IL');
    let message = '';

    switch (appointment.type) {
      case 'fitting':
        message = whatsappHelper.messages.fittingReminder(
          appointment.customer_name || 'לקוח/ה יקר/ה',
          date,
          appointment.time || undefined
        );
        break;
      case 'pickup':
        message = whatsappHelper.messages.pickupReminder(
          appointment.customer_name || 'לקוח/ה יקר/ה',
          appointment.dress_name || 'השמלה',
          date
        );
        break;
      case 'return':
        message = whatsappHelper.messages.returnReminder(
          appointment.customer_name || 'לקוח/ה יקר/ה',
          appointment.dress_name || 'השמלה',
          date
        );
        break;
      default:
        message = `שלום ${appointment.customer_name || ''},\nתזכורת לפגישה מחר (${date}).\n\nרחל - השכרת שמלות`;
    }

    const link = whatsappHelper.getLink(appointment.customer_phone, message);
    window.open(link, '_blank');
    markReminderSentMutation.mutate(appointment.id);
  };

  const customerOptions = [
    { value: '', label: 'בחר לקוח/ה (אופציונלי)' },
    ...customers.map((c: Customer) => ({ value: c.id, label: `${c.name}${c.phone ? ` - ${c.phone}` : ''}` })),
  ];

  const dressOptions = [
    { value: '', label: 'בחר שמלה (אופציונלי)' },
    ...dresses.map((d: Dress) => ({ value: d.id, label: d.name })),
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500 text-4xl animate-pulse">◈</div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up pb-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-6 lg:mb-10">
        <div>
          <h1 className="font-sans text-2xl lg:text-4xl font-semibold text-gray-900 mb-1 lg:mb-2">
            לוח שנה
          </h1>
          <p className="text-gray-600 text-sm lg:text-base">השכרות ופגישות</p>
          <div className="gold-accent mt-3 lg:mt-4 w-12 lg:w-16"></div>
        </div>
        <Button onClick={() => openModal()} className="w-full sm:w-auto">
          + פגישה חדשה
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-8">
        {/* Today's Appointments */}
        <Card className="p-4 lg:p-6 lg:col-span-1" hover={false}>
          <div className="flex items-center gap-2 mb-4">
            <span className="text-gray-600">◆</span>
            <h2 className="font-sans text-lg font-semibold text-gray-900">פגישות היום</h2>
          </div>
          {todayAppointments.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">אין פגישות היום</p>
          ) : (
            <div className="space-y-3">
              {todayAppointments.map((apt: Appointment) => (
                <div key={apt.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-medium text-gray-700">{getTypeLabel(apt.type)}</span>
                      {apt.time && <span className="text-xs text-gray-500 mr-2">{apt.time}</span>}
                      <p className="text-sm font-medium text-gray-900">{apt.customer_name || 'ללא לקוח'}</p>
                      {apt.dress_name && <p className="text-xs text-gray-500">{apt.dress_name}</p>}
                    </div>
                    {apt.customer_phone && (
                      <a
                        href={whatsappHelper.getLink(apt.customer_phone, `שלום ${apt.customer_name}, `)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-600 hover:text-green-700"
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

          {/* Reminders Section */}
          {reminders.length > 0 && (
            <>
              <div className="flex items-center gap-2 mt-6 mb-4">
                <span className="text-amber-500">◇</span>
                <h2 className="font-sans text-lg font-semibold text-gray-900">תזכורות למחר</h2>
              </div>
              <div className="space-y-3">
                {reminders.map((apt: Appointment) => (
                  <div key={apt.id} className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs font-medium text-amber-600">{getTypeLabel(apt.type)}</span>
                        <p className="text-sm font-medium text-gray-900">{apt.customer_name || 'ללא לקוח'}</p>
                      </div>
                      {apt.customer_phone && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => sendWhatsAppReminder(apt)}
                          className="text-xs"
                        >
                          שלח תזכורת
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>

        {/* Calendar */}
        <Card className="p-3 lg:p-6 lg:col-span-2" hover={false}>
          <FullCalendar
            plugins={[dayGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            events={events}
            locale="he"
            direction="rtl"
            headerToolbar={{
              right: 'prev,next today',
              center: 'title',
              left: 'dayGridMonth,dayGridWeek',
            }}
            buttonText={{
              today: 'היום',
              month: 'חודש',
              week: 'שבוע',
            }}
            dateClick={handleDateClick}
            eventClick={handleEventClick}
            height="auto"
            dayMaxEvents={2}
            eventDisplay="block"
          />
        </Card>
      </div>

      {/* Legend */}
      <div className="mt-4 lg:mt-6 flex flex-wrap gap-3 lg:gap-6">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-600"></div>
          <span className="text-gray-500 text-sm">השכרה פעילה</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
          <span className="text-gray-500 text-sm">הושלם</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-purple-500"></div>
          <span className="text-gray-500 text-sm">מדידה</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <span className="text-gray-500 text-sm">איסוף</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-gray-500 text-sm">החזרה</span>
        </div>
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
            value={formData.customer_id}
            onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
            options={customerOptions}
          />

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

          <div className="flex justify-end gap-4 pt-4 border-t border-gray-100">
            <Button type="button" variant="secondary" onClick={closeModal}>
              ביטול
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              הוסף פגישה
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
