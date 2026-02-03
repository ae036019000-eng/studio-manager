import { Router } from 'express';
import { all, get, run } from '../database/schema.js';

const router = Router();

// Get all dresses
router.get('/', async (req, res) => {
  try {
    const dresses = await all('SELECT * FROM dresses ORDER BY created_at DESC');
    res.json(dresses);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch dresses' });
  }
});

// Get single dress
router.get('/:id', async (req, res) => {
  try {
    const dress = await get('SELECT * FROM dresses WHERE id = ?', [req.params.id]);
    if (!dress) {
      return res.status(404).json({ error: 'Dress not found' });
    }
    res.json(dress);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch dress' });
  }
});

// Create dress
router.post('/', async (req, res) => {
  try {
    const { name, description, size, color, price_per_day, image_path, status } = req.body;
    const result = await run(
      `INSERT INTO dresses (name, description, size, color, price_per_day, image_path, status)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [name, description, size, color, price_per_day, image_path, status || 'available']
    );

    const newDress = await get('SELECT * FROM dresses WHERE id = ?', [result.lastInsertRowid]);
    res.status(201).json(newDress);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create dress' });
  }
});

// Update dress
router.put('/:id', async (req, res) => {
  try {
    const { name, description, size, color, price_per_day, image_path, status } = req.body;
    await run(
      `UPDATE dresses
       SET name = ?, description = ?, size = ?, color = ?, price_per_day = ?, image_path = ?, status = ?
       WHERE id = ?`,
      [name, description, size, color, price_per_day, image_path, status, req.params.id]
    );

    const updated = await get('SELECT * FROM dresses WHERE id = ?', [req.params.id]);
    res.json(updated);
  } catch (error) {
    res.status(500).json({ error: 'Failed to update dress' });
  }
});

// Delete dress
router.delete('/:id', async (req, res) => {
  try {
    // Check if dress has active rentals
    const activeRentals = await get(
      "SELECT COUNT(*) as count FROM rentals WHERE dress_id = ? AND status = 'active'",
      [req.params.id]
    );
    if (activeRentals && activeRentals.count > 0) {
      return res.status(400).json({ error: 'לא ניתן למחוק שמלה עם השכרות פעילות' });
    }

    await run('DELETE FROM dresses WHERE id = ?', [req.params.id]);
    res.json({ message: 'Dress deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete dress' });
  }
});

// Check dress availability
router.get('/:id/availability', async (req, res) => {
  try {
    const { start_date, end_date } = req.query;
    const conflicts = await all(
      `SELECT * FROM rentals
       WHERE dress_id = ?
       AND status != 'cancelled'
       AND (
         (start_date <= ? AND end_date >= ?)
         OR (start_date <= ? AND end_date >= ?)
         OR (start_date >= ? AND end_date <= ?)
       )`,
      [req.params.id, end_date, start_date, start_date, start_date, start_date, end_date]
    );

    res.json({ available: conflicts.length === 0, conflicts });
  } catch (error) {
    res.status(500).json({ error: 'Failed to check availability' });
  }
});

export default router;
