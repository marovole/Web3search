-- Migration: Add trigram index to coins
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY idx_coins_symbol 
ON coins USING gin(symbol gin_trgm_ops);