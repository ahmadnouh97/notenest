import * as SQLite from 'expo-sqlite';
import { CREATE_INDEXES, CREATE_TABLE_EMBEDDINGS, CREATE_TABLE_NOTES } from './schema';

export type DatabaseConnection = SQLite.SQLiteDatabase;

let dbSingleton: DatabaseConnection | null = null;

export async function getDatabase(): Promise<DatabaseConnection> {
  if (dbSingleton) return dbSingleton;
  const db = await SQLite.openDatabaseAsync('notenest.db');
  await db.execAsync('PRAGMA journal_mode = WAL;');
  await db.execAsync(CREATE_TABLE_NOTES);
  await db.execAsync(CREATE_TABLE_EMBEDDINGS);
  await db.execAsync(CREATE_INDEXES);
  dbSingleton = db;
  return dbSingleton;
}


