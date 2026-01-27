#!/bin/bash
set -e

# Create schema - tables will be managed by Alembic migrations
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "ai_council" <<-EOSQL
  CREATE SCHEMA IF NOT EXISTS main;
  
  -- Grant permissions to council_user
  GRANT ALL ON SCHEMA main TO council_user;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA main TO council_user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA main TO council_user;
  ALTER DEFAULT PRIVILEGES IN SCHEMA main GRANT ALL ON TABLES TO council_user;
  ALTER DEFAULT PRIVILEGES IN SCHEMA main GRANT ALL ON SEQUENCES TO council_user;
  
  -- Create the prompts_history table (initial setup, Alembic will manage future migrations)
  CREATE TABLE IF NOT EXISTS main.prompts_history
    (
      id          TEXT NOT NULL,
      prompt      TEXT NOT NULL,
      response    TEXT,
      rating      INTEGER NOT NULL,
      llm_name    VARCHAR(100) NOT NULL,
      created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
      PRIMARY KEY (id),
      CONSTRAINT rating_range CHECK (rating >= 1 AND rating <= 5)
    );
  
  -- Create indexes for common queries
  CREATE INDEX IF NOT EXISTS ix_prompts_history_llm_name ON main.prompts_history(llm_name);
  CREATE INDEX IF NOT EXISTS ix_prompts_history_created_at ON main.prompts_history(created_at);
EOSQL