-- Migration: Add index to research_reports
CREATE INDEX CONCURRENTLY idx_research_reports_symbol_created_at 
ON research_reports(symbol, created_at);