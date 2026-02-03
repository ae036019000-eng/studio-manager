import { Router } from 'express';
import { all, get, run } from '../database/schema.js';

const router = Router();

// Get all appointments
router.get('/', async (req, res) => {
  try {
    const appointments = await all(`
      SELECT
        a.*,
        c.name as customer_name,
        c.phone as customer_phone,
        d.name as dress_name
      FROM appointments a
      LEFT JOIN customers c ON a.customer_id = c.id
      LEFT JOIN dresses d ON a.dress_id = d.id
      ORDER BY a.date ASC, a.time ASC
    `);
    res.json(appointments);
  } catch (error) {
    console.error('Error fetching appointments:', error);
    res.status(500).json({ error: 'Failed to fetch appointments' });
  }
});

// Get upcoming appointments (next 7 days)
router.get('/upcoming', async (req, res) => {
  try {
    const today = new Date().toISOString().split('T')[0];
    const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const appointments = await all(`
      SELECT
        a.*,
        c.name as customer_name,
        c.phone as customer_phone,
        d.name as dress_name
      FROM appointments a
      LEFT JOIN customers c ON a.customer_id = c.id
      LEFT JOIN dresses d ON a.dress_id = d.id
      WHERE a.date >= ? AND a.date <= ? AND a.status = 'scheduled'
      ORDER BY a.date ASC, a.time ASC
    `, [today, nextWeek]);
    res.json(appointments);
  } catch (error) {
    console.error('Error fetching upcoming appointments:', error);
    res.status(500).json({ error: 'Failed to fetch appointments' });
  }
});

// Get today's appointments
router.get('/today', async (req, res) => {
  try {
    const today = new Date().toISOString().split('T')[0];

    const appointments = await all(`
      SELECT
        a.*,
        c.name as customer_name,
        c.phone as customer_phone,
        d.name as dress_name
      FROM appointments a
      LEFT JOIN customers c ON a.customer_id = c.id
      LEFT JOIN dresses d ON a.dress_id = d.id
      WHERE a.date = ? AND a.status = 'scheduled'
      ORDER BY a.time ASC
    `, [today]);
    res.json(appointments);
  } catch (error) {
    console.error('Error fetching today appointments:', error);
    res.status(500).json({ error: 'Failed to fetch appointments' });
  }
});

// Get appointments needing reminders (tomorrow)
router.get('/reminders', async (req, res) => {
  try {
    const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const appointments = await all(`
      SELECT
        a.*,
        c.name as customer_name,
        c.phone as customer_phone,
        d.name as dress_name
      FROM appointments a
      LEFT JOIN customers c ON a.customer_id = c.id
      LEFT JOIN dresses d ON a.dress_id = d.id
      WHERE a.date = ? AND a.status = 'scheduled' AND a.reminder_sent = 0
      ORDER BY a.time ASC
    `, [tomorrow]);
    res.json(appointments);
  } catch (error) {
    console.error('Error fetching reminders:', error);
    res.status(500).json({ error: 'Failed to fetch reminders' });
  }
});

// Get single appointment
router.get('/:id', async (req, res) => {
  try {
    const appointment = await get(`
      SELECT
        a.*,
        c.name as customer_name,
        c.phone as customer_phone,
        d.name as dress_name
      FROM appointments a
      LEFT JOIN customers c ON a.customer_id = c.id
      LEFT JOIN dresses d ON a.dress_id = d.id
      WHERE a.id = ?
    `, [req.params.id]);

    if (!appointment) {
      return res.status(404).json({ error: 'Appointment not found' });
    }
    res.json(appointment);
  } catch (error) {
    console.error('Error fetching appointment:', error);
    res.status(500).json({ error: 'Failed to fetch appointment' });
  }
});

// Create appointment
router.post('/', async (req, res) => {
  try {
    const { customer_id, dress_id, type, date, time, notes } = req.body;

    const result = await run(`
      INSERT INTO appointments (customer_id, dress_id, type, date, time, notes)
      VALUES (?, ?, ?, ?, ?, ?)
    `, [customer_id || null, dress_id || null, type, date, time || null, notes || null]);

    const appointment = await get('SELECT * FROM appointments WHERE id = ?', [result.lastInsertRowid]);
    res.status(201).json(appointment);
  } catch (error) {
    console.error('Error creating appointment:', error);
    res.status(500).json({ error: 'Failed to create appointment' });
  }
});

// Update appointment
router.put('/:id', async (req, res) => {
  try {
    const { customer_id, dress_id, type, date, time, notes, status, reminder_sent } = req.body;

    await run(`
      UPDATE appointments
      SET customer_id = ?, dress_id = ?, type = ?, date = ?, time = ?,
          notes = ?, status = ?, reminder_sent = ?
      WHERE id = ?
    `, [customer_id || null, dress_id || null, type, date, time || null,
        notes || null, status || 'scheduled', reminder_sent || 0, req.params.id]);

    const appointment = await get('SELECT * FROM appointments WHERE id = ?', [req.params.id]);
    res.json(appointment);
  } catch (error) {
    console.error('Error updating appointment:', error);
    res.status(500).json({ error: 'Failed to update appointment' });
  }
});

// Mark reminder as sent
router.post('/:id/reminder-sent', async (req, res) => {
  try {
    await run('UPDATE appointments SET reminder_sent = 1 WHERE id = ?', [req.params.id]);
    res.json({ success: true });
  } catch (error) {
    console.error('Error marking reminder:', error);
    res.status(500).json({ error: 'Failed to update reminder status' });
  }
});

// Delete appointment
router.delete('/:id', async (req, res) => {
  try {
    await run('DELETE FROM appointments WHERE id = ?', [req.params.id]);
    res.json({ success: true });
  } catch (error) {
    console.error('Error deleting appointment:', error);
    res.status(500).json({ error: 'Failed to delete appointment' });
  }
});

export default router;
