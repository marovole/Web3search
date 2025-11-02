-- Migration: Add trigram index to coins
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY idx_coins_name 
ON coins USING gin(name gin_trgm_ops);