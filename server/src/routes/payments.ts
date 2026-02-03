import { Router } from 'express';
import { all, get, run } from '../database/schema.js';

const router = Router();

// Get all payments
router.get('/', async (req, res) => {
  try {
    const payments = await all(`
      SELECT p.*, r.id as rental_id, c.name as customer_name, d.name as dress_name
      FROM payments p
      JOIN rentals r ON p.rental_id = r.id
      JOIN customers c ON r.customer_id = c.id
      JOIN dresses d ON r.dress_id = d.id
      ORDER BY p.payment_date DESC
    `);
    res.json(payments);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch payments' });
  }
});

// Get payments for a rental
router.get('/rental/:rentalId', async (req, res) => {
  try {
    const payments = await all('SELECT * FROM payments WHERE rental_id = ? ORDER BY payment_date DESC', [req.params.rentalId]);
    res.json(payments);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch payments' });
  }
});

// Create payment
router.post('/', async (req, res) => {
  try {
    const { rental_id, amount, payment_date, method, notes } = req.body;
    const result = await run(
      `INSERT INTO payments (rental_id, amount, payment_date, method, notes)
       VALUES (?, ?, ?, ?, ?)`,
      [rental_id, amount, payment_date, method, notes]
    );

    const newPayment = await get('SELECT * FROM payments WHERE id = ?', [result.lastInsertRowid]);
    res.status(201).json(newPayment);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create payment' });
  }
});

// Update payment
router.put('/:id', async (req, res) => {
  try {
    const { amount, payment_date, method, notes } = req.body;
    await run(
      `UPDATE payments
       SET amount = ?, payment_date = ?, method = ?, notes = ?
       WHERE id = ?`,
      [amount, payment_date, method, notes, req.params.id]
    );

    const updated = await get('SELECT * FROM payments WHERE id = ?', [req.params.id]);
    res.json(updated);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update payment' });
  }
});

// Delete payment
router.delete('/:id', async (req, res) => {
  try {
    await run('DELETE FROM payments WHERE id = ?', [req.params.id]);
    res.json({ message: 'Payment deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete payment' });
  }
});

export default router;
