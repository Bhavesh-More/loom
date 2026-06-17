CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS pipeline_execution_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text NOT NULL UNIQUE,
  task text NOT NULL,
  plan_json jsonb NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pipeline_agent_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text NOT NULL REFERENCES pipeline_execution_plans(run_id),
  agent_id text NOT NULL,
  status text NOT NULL,
  output_json jsonb,
  score float,
  attempt_count int DEFAULT 1,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_manifests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id text NOT NULL UNIQUE,
  manifest_json jsonb NOT NULL,
  registered_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_check_adoption (
  check_name text NOT NULL,
  agent_id text NOT NULL,
  registered_at timestamptz DEFAULT now(),
  PRIMARY KEY (check_name, agent_id)
);

CREATE INDEX IF NOT EXISTS pipeline_agent_results_run_agent_idx
  ON pipeline_agent_results(run_id, agent_id, created_at DESC);
