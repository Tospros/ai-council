#!/bin/bash
set -e

# Create schema - tables will be managed by Alembic migrations
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "ai_council" <<-EOSQL
  CREATE SCHEMA IF NOT EXISTS main;
<<<<<<< HEAD
  
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
=======

  -- Table to store prompt sessions/calls
  CREATE TABLE main.sessions (
    id              UUID PRIMARY KEY,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Table to store prompts
  CREATE TABLE main.prompts (
    id              SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES main.sessions(id) ON DELETE CASCADE,
    prompt_text     TEXT NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Table to store model responses
  CREATE TABLE main.responses (
    id              SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES main.sessions(id) ON DELETE CASCADE,
    model_name      TEXT NOT NULL,
    response_text   TEXT NOT NULL,
    response_time_ms INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Table to store user ratings
  CREATE TABLE main.ratings (
    id              SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL REFERENCES main.sessions(id) ON DELETE CASCADE,
    model_name      TEXT NOT NULL,
    rating          INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, model_name)
  );

  -- Create indexes for common queries
  CREATE INDEX idx_prompts_session ON main.prompts(session_id);
  CREATE INDEX idx_responses_session ON main.responses(session_id);
  CREATE INDEX idx_ratings_session ON main.ratings(session_id);
  CREATE INDEX idx_sessions_created ON main.sessions(created_at DESC);

  -- Grant permissions to council_user
  GRANT USAGE ON SCHEMA main TO council_user;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA main TO council_user;
  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA main TO council_user;
>>>>>>> 800dc0b0b3fe9fa5541a2373747f092f9042a68a
EOSQL