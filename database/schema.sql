-- Yalnız giriş / qeydiyyat üçün minimal sxem (PostgreSQL)
-- Tətbiq işə düşəndə də CREATE TABLE edilir; əl ilə: psql "$DATABASE_URL" -f database/schema.sql

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
