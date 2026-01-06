#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "ai_council" <<-EOSQL
  CREATE SCHEMA IF NOT EXISTS main;

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
EOSQL