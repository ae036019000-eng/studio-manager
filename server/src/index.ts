import express from 'express';
import cors from 'cors';
import path from 'path';
import { initializeDatabase } from './database/schema.js';
import dressesRouter from './routes/dresses.js';
import customersRouter from './routes/customers.js';
import rentalsRouter from './routes/rentals.js';
import paymentsRouter from './routes/payments.js';
import reportsRouter from './routes/reports.js';
import uploadRouter from './routes/upload.js';

const app = express();
const PORT = process.env.PORT || 3001;
const isProduction = process.env.NODE_ENV === 'production';

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, '..', '..', 'uploads')));

// Routes
app.use('/api/dresses', dressesRouter);
app.use('/api/customers', customersRouter);
app.use('/api/rentals', rentalsRouter);
app.use('/api/payments', paymentsRouter);
app.use('/api/reports', reportsRouter);
app.use('/api/upload', uploadRouter);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Serve client in production
if (isProduction) {
  const clientPath = path.join(__dirname, '..', '..', 'client', 'dist');
  app.use(express.static(clientPath));
  app.get('*', (req, res) => {
    res.sendFile(path.join(clientPath, 'index.html'));
  });
}

// Initialize database and start server
async function start() {
  try {
    await initializeDatabase();
    app.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();
