export interface Dress {
  id: number;
  name: string;
  description: string | null;
  size: string | null;
  color: string | null;
  price_per_day: number;
  image_path: string | null;
  status: 'available' | 'rented' | 'maintenance';
  created_at: string;
}

export interface Customer {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  notes: string | null;
  created_at: string;
}

export interface Rental {
  id: number;
  dress_id: number;
  customer_id: number;
  start_date: string;
  end_date: string;
  total_price: number;
  deposit: number;
  status: 'active' | 'completed' | 'cancelled';
  notes: string | null;
  created_at: string;
  // Joined fields
  dress_name?: string;
  dress_image?: string;
  dress_color?: string;
  customer_name?: string;
  customer_phone?: string;
  customer_email?: string;
  price_per_day?: number;
}

export interface Payment {
  id: number;
  rental_id: number;
  amount: number;
  payment_date: string;
  method: string | null;
  notes: string | null;
  created_at: string;
  // Joined fields
  customer_name?: string;
  dress_name?: string;
}

export interface Appointment {
  id: number;
  customer_id: number | null;
  dress_id: number | null;
  type: 'fitting' | 'pickup' | 'return' | 'other';
  date: string;
  time: string | null;
  notes: string | null;
  status: 'scheduled' | 'completed' | 'cancelled';
  reminder_sent: number;
  created_at: string;
  // Joined fields
  customer_name?: string;
  customer_phone?: string;
  dress_name?: string;
}

export interface DashboardStats {
  totalDresses: number;
  availableDresses: number;
  totalCustomers: number;
  activeRentals: number;
  todayAppointments: number;
  monthlyRevenue: number;
}

export interface CalendarEvent {
  id: number;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  extendedProps: {
    dressName: string;
    customerName: string;
    status: string;
  };
}

export interface RevenueReport {
  month: string;
  total: number;
  payment_count: number;
}

export interface PopularDress extends Dress {
  rental_count: number;
  total_revenue: number;
}

export interface ReturningCustomer extends Customer {
  rental_count: number;
  total_spent: number;
}
