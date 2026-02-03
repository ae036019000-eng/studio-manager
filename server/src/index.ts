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
const PORT = Number(process.env.PORT) || 3001;
const isProduction = process.env.NODE_ENV === 'production';

console.log('Starting server...');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('PORT:', PORT);

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, '..', '..', 'uploads')));

// Health check - before other routes so it always works
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Routes
app.use('/api/dresses', dressesRouter);
app.use('/api/customers', customersRouter);
app.use('/api/rentals', rentalsRouter);
app.use('/api/payments', paymentsRouter);
app.use('/api/reports', reportsRouter);
app.use('/api/upload', uploadRouter);

// Serve client in production
if (isProduction) {
  const clientPath = path.join(__dirname, '..', '..', 'client', 'dist');
  console.log('Serving client from:', clientPath);
  app.use(express.static(clientPath));
  app.get('*', (req, res) => {
    res.sendFile(path.join(clientPath, 'index.html'));
  });
}

// Initialize database and start server
async function start() {
  try {
    await initializeDatabase();
    console.log('Database initialized');
  } catch (error) {
    console.error('Database initialization error:', error);
    // Continue anyway - tables might already exist
  }

  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
}

start();
