import { Router } from 'express';
import { all, get, run } from '../database/schema.js';

const router = Router();

// Get all customers
router.get('/', async (req, res) => {
  try {
    const customers = await all('SELECT * FROM customers ORDER BY created_at DESC');
    res.json(customers);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch customers' });
  }
});

// Get single customer
router.get('/:id', async (req, res) => {
  try {
    const customer = await get('SELECT * FROM customers WHERE id = ?', [req.params.id]);
    if (!customer) {
      return res.status(404).json({ error: 'Customer not found' });
    }
    res.json(customer);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch customer' });
  }
});

// Get customer rental history
router.get('/:id/rentals', async (req, res) => {
  try {
    const rentals = await all(
      `SELECT r.*, d.name as dress_name, d.image_path as dress_image
       FROM rentals r
       JOIN dresses d ON r.dress_id = d.id
       WHERE r.customer_id = ?
       ORDER BY r.start_date DESC`,
      [req.params.id]
    );
    res.json(rentals);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch customer rentals' });
  }
});

// Create customer
router.post('/', async (req, res) => {
  try {
    const { name, phone, email, address, notes } = req.body;
    const result = await run(
      `INSERT INTO customers (name, phone, email, address, notes)
       VALUES (?, ?, ?, ?, ?)`,
      [name, phone, email, address, notes]
    );

    const newCustomer = await get('SELECT * FROM customers WHERE id = ?', [result.lastInsertRowid]);
    res.status(201).json(newCustomer);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create customer' });
  }
});

// Update customer
router.put('/:id', async (req, res) => {
  try {
    const { name, phone, email, address, notes } = req.body;
    await run(
      `UPDATE customers
       SET name = ?, phone = ?, email = ?, address = ?, notes = ?
       WHERE id = ?`,
      [name, phone, email, address, notes, req.params.id]
    );

    const updated = await get('SELECT * FROM customers WHERE id = ?', [req.params.id]);
    res.json(updated);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update customer' });
  }
});

// Delete customer
router.delete('/:id', async (req, res) => {
  try {
    // Check if customer has rentals
    const rentals = await get('SELECT COUNT(*) as count FROM rentals WHERE customer_id = ?', [req.params.id]);
    if (rentals && rentals.count > 0) {
      return res.status(400).json({ error: 'לא ניתן למחוק לקוח עם היסטוריית השכרות' });
    }

    await run('DELETE FROM customers WHERE id = ?', [req.params.id]);
    res.json({ message: 'Customer deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete customer' });
  }
});

export default router;
