-- Multi-Agent Framework Database Schema
-- Creates tables for tracking multi-agent research tasks

-- Create multi_agent_tasks table
CREATE TABLE IF NOT EXISTS multi_agent_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  query TEXT NOT NULL,
  intent VARCHAR(50) NOT NULL DEFAULT 'comprehensive_research',
  config JSONB NOT NULL DEFAULT '{}',
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  result JSONB,
  error TEXT,
  tokens_used INTEGER DEFAULT 0,
  duration_ms INTEGER,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'deleted')),
  CONSTRAINT valid_intent CHECK (intent IN ('comprehensive_research', 'market_analysis', 'token_deep_dive', 'news_synthesis', 'portfolio_review'))
);

-- Create multi_agent_runs table for tracking individual agent executions
CREATE TABLE IF NOT EXISTS multi_agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID NOT NULL REFERENCES multi_agent_tasks(id) ON DELETE CASCADE,
  agent_id VARCHAR(50) NOT NULL,
  agent_name VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  input JSONB,
  output JSONB,
  metrics JSONB,
  error TEXT,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  CONSTRAINT valid_run_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_multi_agent_tasks_user ON multi_agent_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_multi_agent_tasks_status ON multi_agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_multi_agent_tasks_created_at ON multi_agent_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_multi_agent_tasks_intent ON multi_agent_tasks(intent);
CREATE INDEX IF NOT EXISTS idx_multi_agent_runs_task ON multi_agent_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_multi_agent_runs_agent ON multi_agent_runs(agent_id);

-- Enable Row Level Security
ALTER TABLE multi_agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE multi_agent_runs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for multi_agent_tasks
CREATE POLICY "Users can view their own tasks"
  ON multi_agent_tasks
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tasks"
  ON multi_agent_tasks
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tasks"
  ON multi_agent_tasks
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tasks"
  ON multi_agent_tasks
  FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for multi_agent_runs
CREATE POLICY "Users can view runs for their tasks"
  ON multi_agent_runs
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM multi_agent_tasks
      WHERE multi_agent_tasks.id = multi_agent_runs.task_id
      AND multi_agent_tasks.user_id = auth.uid()
    )
  );

CREATE POLICY "System can insert runs"
  ON multi_agent_runs
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY "System can update runs"
  ON multi_agent_runs
  FOR UPDATE
  USING (true);

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_multi_agent_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
CREATE TRIGGER update_multi_agent_tasks_updated_at
  BEFORE UPDATE ON multi_agent_tasks
  FOR EACH ROW
  EXECUTE FUNCTION update_multi_agent_tasks_updated_at();
