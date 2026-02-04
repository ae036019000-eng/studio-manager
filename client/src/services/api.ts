const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'An error occurred' }));
    throw new Error(error.error || 'An error occurred');
  }

  return response.json();
}

// Dresses API
export const dressesApi = {
  getAll: () => fetchApi<any[]>('/dresses'),
  getById: (id: number) => fetchApi<any>(`/dresses/${id}`),
  create: (data: any) => fetchApi<any>('/dresses', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: any) => fetchApi<any>(`/dresses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => fetchApi<void>(`/dresses/${id}`, { method: 'DELETE' }),
  checkAvailability: (id: number, startDate: string, endDate: string) =>
    fetchApi<{ available: boolean; conflicts: any[] }>(`/dresses/${id}/availability?start_date=${startDate}&end_date=${endDate}`),
};

// Customers API
export const customersApi = {
  getAll: () => fetchApi<any[]>('/customers'),
  getById: (id: number) => fetchApi<any>(`/customers/${id}`),
  getRentals: (id: number) => fetchApi<any[]>(`/customers/${id}/rentals`),
  create: (data: any) => fetchApi<any>('/customers', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: any) => fetchApi<any>(`/customers/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => fetchApi<void>(`/customers/${id}`, { method: 'DELETE' }),
};

// Rentals API
export const rentalsApi = {
  getAll: () => fetchApi<any[]>('/rentals'),
  getById: (id: number) => fetchApi<any>(`/rentals/${id}`),
  getActive: () => fetchApi<any[]>('/rentals/status/active'),
  getUpcomingReturns: () => fetchApi<any[]>('/rentals/alerts/upcoming-returns'),
  create: (data: any) => fetchApi<any>('/rentals', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: any) => fetchApi<any>(`/rentals/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => fetchApi<void>(`/rentals/${id}`, { method: 'DELETE' }),
};

// Payments API
export const paymentsApi = {
  getAll: () => fetchApi<any[]>('/payments'),
  getByRental: (rentalId: number) => fetchApi<any[]>(`/payments/rental/${rentalId}`),
  create: (data: any) => fetchApi<any>('/payments', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: any) => fetchApi<any>(`/payments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => fetchApi<void>(`/payments/${id}`, { method: 'DELETE' }),
};

// Reports API
export const reportsApi = {
  getDashboard: () => fetchApi<any>('/reports/dashboard'),
  getRevenue: (startDate?: string, endDate?: string) => {
    let url = '/reports/revenue';
    if (startDate && endDate) {
      url += `?start_date=${startDate}&end_date=${endDate}`;
    }
    return fetchApi<any[]>(url);
  },
  getPopularDresses: () => fetchApi<any[]>('/reports/popular-dresses'),
  getReturningCustomers: () => fetchApi<any[]>('/reports/returning-customers'),
  getCalendarEvents: () => fetchApi<any[]>('/reports/calendar'),
  exportData: (type: 'rentals' | 'customers' | 'dresses' | 'payments') => {
    window.open(`${API_BASE}/reports/export/${type}`, '_blank');
  },
};

// Appointments API
export const appointmentsApi = {
  getAll: () => fetchApi<any[]>('/appointments'),
  getUpcoming: () => fetchApi<any[]>('/appointments/upcoming'),
  getToday: () => fetchApi<any[]>('/appointments/today'),
  getReminders: () => fetchApi<any[]>('/appointments/reminders'),
  getById: (id: number) => fetchApi<any>(`/appointments/${id}`),
  create: (data: any) => fetchApi<any>('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: any) => fetchApi<any>(`/appointments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  markReminderSent: (id: number) => fetchApi<void>(`/appointments/${id}/reminder-sent`, { method: 'POST' }),
  delete: (id: number) => fetchApi<void>(`/appointments/${id}`, { method: 'DELETE' }),
};

// WhatsApp Helper
export const whatsappHelper = {
  // Generate WhatsApp link with message
  getLink: (phone: string, message: string): string => {
    // Clean phone number - remove spaces, dashes, etc.
    let cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    // If starts with 0, replace with Israel code
    if (cleanPhone.startsWith('0')) {
      cleanPhone = '972' + cleanPhone.substring(1);
    }
    // If doesn't start with +, add it
    if (!cleanPhone.startsWith('+')) {
      cleanPhone = '+' + cleanPhone;
    }
    const encodedMessage = encodeURIComponent(message);
    return `https://wa.me/${cleanPhone.replace('+', '')}?text=${encodedMessage}`;
  },

  // Pre-made message templates
  messages: {
    returnReminder: (customerName: string, dressName: string, date: string) =>
      `שלום ${customerName},\nתזכורת: מחר (${date}) מתוכננת החזרת השמלה "${dressName}".\nנשמח לראותך!\n\nרחל - השכרת שמלות`,

    fittingReminder: (customerName: string, date: string, time?: string) =>
      `שלום ${customerName},\nתזכורת: מחר (${date})${time ? ` בשעה ${time}` : ''} יש לך מדידה בסטודיו.\nמחכים לך!\n\nרחל - השכרת שמלות`,

    pickupReminder: (customerName: string, dressName: string, date: string) =>
      `שלום ${customerName},\nתזכורת: מחר (${date}) מתוכנן איסוף השמלה "${dressName}".\nנשמח לראותך!\n\nרחל - השכרת שמלות`,

    thankYou: (customerName: string) =>
      `שלום ${customerName},\nתודה שבחרת ברחל!\nנשמח לראותך שוב.\n\nרחל - השכרת שמלות`,
  }
};

// Settings API
export const settingsApi = {
  getAll: () => fetchApi<Record<string, string>>('/settings'),
  get: (key: string) => fetchApi<{ key: string; value: string }>(`/settings/${key}`),
  update: (key: string, value: string) =>
    fetchApi<{ key: string; value: string }>(`/settings/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    }),
  updateBulk: (settings: Record<string, string>) =>
    fetchApi<{ success: boolean }>('/settings/bulk', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
};

// Upload API
export const uploadApi = {
  uploadImage: async (file: File): Promise<{ path: string; filename: string }> => {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'שגיאה בהעלאת התמונה' }));
      throw new Error(error.error || 'שגיאה בהעלאת התמונה');
    }

    return response.json();
  },
  deleteImage: (filename: string) =>
    fetchApi<void>(`/upload/${filename}`, { method: 'DELETE' }),
};
