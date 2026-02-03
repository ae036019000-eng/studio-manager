import { Router } from 'express';
import { all, get } from '../database/schema.js';

const router = Router();

// Dashboard summary
router.get('/dashboard', async (req, res) => {
  try {
    const totalDresses = await get('SELECT COUNT(*) as count FROM dresses');
    const availableDresses = await get("SELECT COUNT(*) as count FROM dresses WHERE status = 'available'");
    const totalCustomers = await get('SELECT COUNT(*) as count FROM customers');
    const activeRentals = await get("SELECT COUNT(*) as count FROM rentals WHERE status = 'active'");

    const monthStart = new Date();
    monthStart.setDate(1);
    const monthStartStr = monthStart.toISOString().split('T')[0];

    const monthlyRevenue = await get(`
      SELECT COALESCE(SUM(amount), 0) as total
      FROM payments
      WHERE payment_date >= ?
    `, [monthStartStr]);

    res.json({
      totalDresses: totalDresses?.count || 0,
      availableDresses: availableDresses?.count || 0,
      totalCustomers: totalCustomers?.count || 0,
      activeRentals: activeRentals?.count || 0,
      monthlyRevenue: monthlyRevenue?.total || 0
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch dashboard data' });
  }
});

// Revenue report
router.get('/revenue', async (req, res) => {
  try {
    const { start_date, end_date } = req.query;

    let query = `
      SELECT
        strftime('%Y-%m', payment_date) as month,
        SUM(amount) as total,
        COUNT(*) as payment_count
      FROM payments
    `;

    const params: string[] = [];
    if (start_date && end_date) {
      query += ' WHERE payment_date BETWEEN ? AND ?';
      params.push(start_date as string, end_date as string);
    }

    query += ' GROUP BY strftime("%Y-%m", payment_date) ORDER BY month DESC';

    const revenue = await all(query, params);
    res.json(revenue);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch revenue report' });
  }
});

// Popular dresses
router.get('/popular-dresses', async (req, res) => {
  try {
    const popularDresses = await all(`
      SELECT d.*, COUNT(r.id) as rental_count, COALESCE(SUM(r.total_price), 0) as total_revenue
      FROM dresses d
      LEFT JOIN rentals r ON d.id = r.dress_id
      GROUP BY d.id
      ORDER BY rental_count DESC
      LIMIT 10
    `);
    res.json(popularDresses);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch popular dresses' });
  }
});

// Returning customers
router.get('/returning-customers', async (req, res) => {
  try {
    const returningCustomers = await all(`
      SELECT c.*, COUNT(r.id) as rental_count, COALESCE(SUM(r.total_price), 0) as total_spent
      FROM customers c
      JOIN rentals r ON c.id = r.customer_id
      GROUP BY c.id
      HAVING rental_count > 1
      ORDER BY rental_count DESC
    `);
    res.json(returningCustomers);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch returning customers' });
  }
});

// Calendar events (for FullCalendar)
router.get('/calendar', async (req, res) => {
  try {
    const rentals = await all(`
      SELECT r.id, r.start_date, r.end_date, r.status,
             d.name as dress_name, d.color as dress_color,
             c.name as customer_name
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      WHERE r.status != 'cancelled'
    `);

    const events = rentals.map((r: any) => ({
      id: r.id,
      title: `${r.dress_name} - ${r.customer_name}`,
      start: r.start_date,
      end: r.end_date,
      backgroundColor: r.status === 'active' ? '#3b82f6' : '#10b981',
      extendedProps: {
        dressName: r.dress_name,
        customerName: r.customer_name,
        status: r.status
      }
    }));

    res.json(events);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch calendar events' });
  }
});

// Export data to CSV format
router.get('/export/:type', async (req, res) => {
  try {
    const { type } = req.params;
    let data: any[];
    let filename: string;

    switch (type) {
      case 'rentals':
        data = await all(`
          SELECT r.id, d.name as dress_name, c.name as customer_name,
                 r.start_date, r.end_date, r.total_price, r.deposit, r.status
          FROM rentals r
          JOIN dresses d ON r.dress_id = d.id
          JOIN customers c ON r.customer_id = c.id
          ORDER BY r.start_date DESC
        `);
        filename = 'rentals.csv';
        break;
      case 'customers':
        data = await all('SELECT id, name, phone, email, address FROM customers');
        filename = 'customers.csv';
        break;
      case 'dresses':
        data = await all('SELECT id, name, size, color, price_per_day, status FROM dresses');
        filename = 'dresses.csv';
        break;
      case 'payments':
        data = await all(`
          SELECT p.id, p.amount, p.payment_date, p.method,
                 c.name as customer_name, d.name as dress_name
          FROM payments p
          JOIN rentals r ON p.rental_id = r.id
          JOIN customers c ON r.customer_id = c.id
          JOIN dresses d ON r.dress_id = d.id
          ORDER BY p.payment_date DESC
        `);
        filename = 'payments.csv';
        break;
      default:
        return res.status(400).json({ error: 'Invalid export type' });
    }

    if (data.length === 0) {
      return res.status(404).json({ error: 'No data to export' });
    }

    // Convert to CSV
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row =>
      Object.values(row).map(v => `"${v ?? ''}"`).join(',')
    ).join('\n');
    const csv = `${headers}\n${rows}`;

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename=${filename}`);
    res.send(csv);
  } catch (error) {
    res.status(500).json({ error: 'Failed to export data' });
  }
});

export default router;
