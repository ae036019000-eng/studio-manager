import { useQuery } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import { reportsApi } from '../services/api';
import Card from '../components/Card';

export default function Calendar() {
  const { data: events = [], isLoading } = useQuery({
    queryKey: ['calendar-events'],
    queryFn: reportsApi.getCalendarEvents,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gold-400 text-4xl animate-pulse">◈</div>
      </div>
    );
  }

  // Style events with elegant colors
  const styledEvents = events.map((event: any) => ({
    ...event,
    backgroundColor: event.extendedProps?.status === 'active' ? '#D4AF37' : '#10b981',
    borderColor: 'transparent',
  }));

  return (
    <div className="animate-slide-up pb-20 lg:pb-0">
      {/* Header */}
      <div className="mb-6 lg:mb-10">
        <h1 className="font-serif text-2xl lg:text-4xl font-semibold text-champagne-800 mb-1 lg:mb-2">
          לוח שנה
        </h1>
        <p className="text-champagne-700 text-sm lg:text-base">תצוגת השכרות בלוח שנה</p>
        <div className="gold-accent mt-3 lg:mt-4 w-12 lg:w-16"></div>
      </div>

      {/* Calendar */}
      <Card className="p-3 lg:p-8" hover={false}>
        <FullCalendar
          plugins={[dayGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          events={styledEvents}
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
          eventClick={(info) => {
            const props = info.event.extendedProps;
            alert(`שמלה: ${props.dressName}\nלקוח/ה: ${props.customerName}\nסטטוס: ${props.status === 'active' ? 'פעיל' : 'הושלם'}`);
          }}
          height="auto"
          dayMaxEvents={2}
          eventDisplay="block"
        />
      </Card>

      {/* Legend */}
      <div className="mt-4 lg:mt-6 flex gap-4 lg:gap-8">
        <div className="flex items-center gap-2 lg:gap-3">
          <div className="w-3 h-3 lg:w-4 lg:h-4 rounded-full bg-gold-500"></div>
          <span className="text-champagne-600 text-sm lg:text-base">השכרה פעילה</span>
        </div>
        <div className="flex items-center gap-2 lg:gap-3">
          <div className="w-3 h-3 lg:w-4 lg:h-4 rounded-full bg-emerald-500"></div>
          <span className="text-champagne-600 text-sm lg:text-base">הושלם</span>
        </div>
      </div>
    </div>
  );
}
