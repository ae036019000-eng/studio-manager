import { createClient, Client } from '@libsql/client';
import initSqlJs, { Database as SqlJsDatabase, SqlValue } from 'sql.js';
import fs from 'fs';
import path from 'path';

const dbPath = path.join(__dirname, '..', '..', '..', 'studio.db');

// Use Turso in production, sql.js locally
const useTurso = !!process.env.TURSO_DATABASE_URL;

let tursoClient: Client | null = null;
let sqlJsDb: SqlJsDatabase | null = null;

export async function initializeDatabase(): Promise<void> {
  if (useTurso) {
    // Production: Use Turso
    console.log('Connecting to Turso...');
    console.log('URL:', process.env.TURSO_DATABASE_URL?.substring(0, 30) + '...');
    tursoClient = createClient({
      url: process.env.TURSO_DATABASE_URL!,
      authToken: process.env.TURSO_AUTH_TOKEN,
    });
    console.log('Connected to Turso database');
  } else {
    // Development: Use sql.js
    const SQL = await initSqlJs();
    if (fs.existsSync(dbPath)) {
      const buffer = fs.readFileSync(dbPath);
      sqlJsDb = new SQL.Database(buffer);
    } else {
      sqlJsDb = new SQL.Database();
    }
    console.log('Using local sql.js database');
  }

  // Create tables (skip if they exist)
  try {
    await runMigrations();
    console.log('Migrations completed');
  } catch (error) {
    console.log('Migrations skipped (tables may already exist)');
  }
}

async function runMigrations(): Promise<void> {
  const tables = [
    `CREATE TABLE IF NOT EXISTS dresses (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      description TEXT,
      size TEXT,
      color TEXT,
      rental_price REAL NOT NULL,
      image_path TEXT,
      status TEXT DEFAULT 'available',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`,
    `CREATE TABLE IF NOT EXISTS customers (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      phone TEXT,
      email TEXT,
      address TEXT,
      notes TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`,
    `CREATE TABLE IF NOT EXISTS rentals (
      id INTEGER PRIMARY KEY,
      dress_id INTEGER NOT NULL,
      customer_id INTEGER NOT NULL,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      total_price REAL NOT NULL,
      deposit REAL DEFAULT 0,
      status TEXT DEFAULT 'active',
      notes TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
      id INTEGER PRIMARY KEY,
      rental_id INTEGER NOT NULL,
      amount REAL NOT NULL,
      payment_date TEXT NOT NULL,
      method TEXT,
      notes TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`,
    `CREATE TABLE IF NOT EXISTS appointments (
      id INTEGER PRIMARY KEY,
      customer_id INTEGER,
      dress_id INTEGER,
      type TEXT NOT NULL,
      date TEXT NOT NULL,
      time TEXT,
      notes TEXT,
      status TEXT DEFAULT 'scheduled',
      reminder_sent INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`,
  ];

  for (const sql of tables) {
    try {
      await run(sql);
    } catch (error) {
      console.error('Migration error:', error);
    }
  }
}

function saveLocalDatabase(): void {
  if (sqlJsDb) {
    const data = sqlJsDb.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(dbPath, buffer);
  }
}

// Convert params to SqlValue array for sql.js
function toSqlValues(params: any[]): SqlValue[] {
  return params.map(p => {
    if (p === undefined) return null;
    return p as SqlValue;
  });
}

// Helper functions that work with both databases
export async function all(sql: string, params: any[] = []): Promise<any[]> {
  try {
    if (useTurso && tursoClient) {
      const result = await tursoClient.execute({ sql, args: params });
      return result.rows as any[];
    } else if (sqlJsDb) {
      const results: any[] = [];
      const stmt = sqlJsDb.prepare(sql);
      if (params.length > 0) {
        stmt.bind(toSqlValues(params));
      }
      while (stmt.step()) {
        results.push(stmt.getAsObject());
      }
      stmt.free();
      return results;
    }
    return [];
  } catch (error) {
    console.error('SQL Error (all):', error, 'SQL:', sql, 'Params:', params);
    throw error;
  }
}

export async function get(sql: string, params: any[] = []): Promise<any> {
  const results = await all(sql, params);
  return results[0] || null;
}

export async function run(sql: string, params: any[] = []): Promise<{ lastInsertRowid: number; changes: number }> {
  try {
    if (useTurso && tursoClient) {
      const result = await tursoClient.execute({ sql, args: params });
      return {
        lastInsertRowid: Number(result.lastInsertRowid) || 0,
        changes: result.rowsAffected
      };
    } else if (sqlJsDb) {
      const stmt = sqlJsDb.prepare(sql);
      if (params.length > 0) {
        stmt.bind(toSqlValues(params));
      }
      stmt.step();
      stmt.free();

      const lastIdResult = sqlJsDb.exec("SELECT last_insert_rowid() as id");
      const lastId = lastIdResult[0]?.values[0]?.[0] as number || 0;
      const changes = sqlJsDb.getRowsModified();
      saveLocalDatabase();
      return { lastInsertRowid: lastId, changes };
    }
    return { lastInsertRowid: 0, changes: 0 };
  } catch (error) {
    console.error('SQL Error (run):', error, 'SQL:', sql, 'Params:', params);
    throw error;
  }
}
