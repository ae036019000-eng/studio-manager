import { Router } from 'express';
import { all, get, run } from '../database/schema.js';

const router = Router();

// Ensure settings table exists
async function ensureSettingsTable() {
  try {
    await run(`
      CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    `);
  } catch (error) {
    // Table might already exist
  }
}

// Default settings
const defaultSettings: Record<string, string> = {
  studio_name: 'Rachel',
  studio_subtitle: 'השכרת שמלות יוקרה',
  whatsapp_return_template: 'שלום {customer_name},\nתזכורת: מחר ({date}) מתוכננת החזרת השמלה "{dress_name}".\nנשמח לראותך!\n\nרחל - השכרת שמלות',
  whatsapp_fitting_template: 'שלום {customer_name},\nתזכורת: מחר ({date}){time} יש לך מדידה בסטודיו.\nמחכים לך!\n\nרחל - השכרת שמלות',
  whatsapp_pickup_template: 'שלום {customer_name},\nתזכורת: מחר ({date}) מתוכנן איסוף השמלה "{dress_name}".\nנשמח לראותך!\n\nרחל - השכרת שמלות',
  whatsapp_thankyou_template: 'שלום {customer_name},\nתודה שבחרת ברחל!\nנשמח לראותך שוב.\n\nרחל - השכרת שמלות',
};

// Get all settings
router.get('/', async (req, res) => {
  try {
    await ensureSettingsTable();
    const settings = await all('SELECT * FROM settings');

    // Merge with defaults
    const result: Record<string, string> = { ...defaultSettings };
    for (const setting of settings) {
      result[setting.key] = setting.value;
    }

    res.json(result);
  } catch (error) {
    console.error('Error fetching settings:', error);
    res.json(defaultSettings);
  }
});

// Get single setting
router.get('/:key', async (req, res) => {
  try {
    await ensureSettingsTable();
    const setting = await get('SELECT * FROM settings WHERE key = ?', [req.params.key]);

    if (setting) {
      res.json({ key: setting.key, value: setting.value });
    } else if (defaultSettings[req.params.key]) {
      res.json({ key: req.params.key, value: defaultSettings[req.params.key] });
    } else {
      res.status(404).json({ error: 'Setting not found' });
    }
  } catch (error) {
    console.error('Error fetching setting:', error);
    res.status(500).json({ error: 'Failed to fetch setting' });
  }
});

// Update setting
router.put('/:key', async (req, res) => {
  try {
    await ensureSettingsTable();
    const { value } = req.body;

    await run(`
      INSERT INTO settings (key, value, updated_at)
      VALUES (?, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
    `, [req.params.key, value, value]);

    res.json({ key: req.params.key, value });
  } catch (error) {
    console.error('Error updating setting:', error);
    res.status(500).json({ error: 'Failed to update setting' });
  }
});

// Update multiple settings
router.post('/bulk', async (req, res) => {
  try {
    await ensureSettingsTable();
    const settings = req.body;

    for (const [key, value] of Object.entries(settings)) {
      await run(`
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
      `, [key, value, value]);
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Error updating settings:', error);
    res.status(500).json({ error: 'Failed to update settings' });
  }
});

export default router;
