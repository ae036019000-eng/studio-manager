import { Router } from 'express';
import { all, get, run } from '../database/schema.js';

const router = Router();

// Get all rentals
router.get('/', async (req, res) => {
  try {
    const rentals = await all(`
      SELECT r.*,
             d.name as dress_name, d.image_path as dress_image, d.color as dress_color,
             c.name as customer_name, c.phone as customer_phone
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      ORDER BY r.start_date DESC
    `);
    res.json(rentals);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch rentals' });
  }
});

// Get single rental
router.get('/:id', async (req, res) => {
  try {
    const rental = await get(`
      SELECT r.*,
             d.name as dress_name, d.image_path as dress_image, d.price_per_day,
             c.name as customer_name, c.phone as customer_phone, c.email as customer_email
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      WHERE r.id = ?
    `, [req.params.id]);

    if (!rental) {
      return res.status(404).json({ error: 'Rental not found' });
    }

    // Get payments for this rental
    const payments = await all('SELECT * FROM payments WHERE rental_id = ? ORDER BY payment_date DESC', [req.params.id]);

    res.json({ ...rental, payments });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch rental' });
  }
});

// Get active rentals (for dashboard)
router.get('/status/active', async (req, res) => {
  try {
    const rentals = await all(`
      SELECT r.*,
             d.name as dress_name, d.image_path as dress_image,
             c.name as customer_name, c.phone as customer_phone
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      WHERE r.status = 'active'
      ORDER BY r.end_date ASC
    `);
    res.json(rentals);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch active rentals' });
  }
});

// Get upcoming returns (next 7 days)
router.get('/alerts/upcoming-returns', async (req, res) => {
  try {
    const today = new Date().toISOString().split('T')[0];
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const rentals = await all(`
      SELECT r.*,
             d.name as dress_name, d.image_path as dress_image,
             c.name as customer_name, c.phone as customer_phone
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      WHERE r.status = 'active'
      AND r.end_date BETWEEN ? AND ?
      ORDER BY r.end_date ASC
    `, [today, nextWeek]);
    res.json(rentals);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch upcoming returns' });
  }
});

// Create rental
router.post('/', async (req, res) => {
  try {
    const { dress_id, customer_id, start_date, end_date, total_price, deposit, notes } = req.body;

    // Check dress availability
    const conflicts = await all(`
      SELECT * FROM rentals
      WHERE dress_id = ?
      AND status != 'cancelled'
      AND (
        (start_date <= ? AND end_date >= ?)
        OR (start_date <= ? AND end_date >= ?)
        OR (start_date >= ? AND end_date <= ?)
      )
    `, [dress_id, end_date, start_date, start_date, start_date, start_date, end_date]);

    if (conflicts.length > 0) {
      return res.status(400).json({ error: 'השמלה לא פנויה בתאריכים שנבחרו' });
    }

    const result = await run(`
      INSERT INTO rentals (dress_id, customer_id, start_date, end_date, total_price, deposit, status, notes)
      VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
    `, [dress_id, customer_id, start_date, end_date, total_price, deposit || 0, notes]);

    // Update dress status
    await run('UPDATE dresses SET status = ? WHERE id = ?', ['rented', dress_id]);

    const newRental = await get(`
      SELECT r.*, d.name as dress_name, c.name as customer_name
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      WHERE r.id = ?
    `, [result.lastInsertRowid]);

    res.status(201).json(newRental);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create rental' });
  }
});

// Update rental
router.put('/:id', async (req, res) => {
  try {
    const { start_date, end_date, total_price, deposit, status, notes } = req.body;

    const currentRental = await get('SELECT * FROM rentals WHERE id = ?', [req.params.id]);
    if (!currentRental) {
      return res.status(404).json({ error: 'Rental not found' });
    }

    await run(`
      UPDATE rentals
      SET start_date = ?, end_date = ?, total_price = ?, deposit = ?, status = ?, notes = ?
      WHERE id = ?
    `, [start_date, end_date, total_price, deposit, status, notes, req.params.id]);

    // Update dress status based on rental status
    if (status === 'completed' || status === 'cancelled') {
      await run('UPDATE dresses SET status = ? WHERE id = ?', ['available', currentRental.dress_id]);
    }

    const updated = await get(`
      SELECT r.*, d.name as dress_name, c.name as customer_name
      FROM rentals r
      JOIN dresses d ON r.dress_id = d.id
      JOIN customers c ON r.customer_id = c.id
      WHERE r.id = ?
    `, [req.params.id]);

    res.json(updated);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update rental' });
  }
});

// Delete rental
router.delete('/:id', async (req, res) => {
  try {
    const rental = await get('SELECT * FROM rentals WHERE id = ?', [req.params.id]);
    if (rental) {
      // Restore dress availability
      await run('UPDATE dresses SET status = ? WHERE id = ?', ['available', rental.dress_id]);
      // Delete associated payments
      await run('DELETE FROM payments WHERE rental_id = ?', [req.params.id]);
    }

    await run('DELETE FROM rentals WHERE id = ?', [req.params.id]);
    res.json({ message: 'Rental deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete rental' });
  }
});

export default router;
