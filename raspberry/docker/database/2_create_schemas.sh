#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "ai_council" <<-EOSQL
  CREATE SCHEMA main;
  CREATE TABLE main.prompts_history
    (
      id          TEXT NOT NULL,
      prompt      TEXT NOT NULL,
      rating      INTEGER NOT NULL,
      llm_name    TEXT NOT NULL,
      PRIMARY KEY (id),
      CONSTRAINT rating_range CHECK (rating >= 1 AND rating <= 5)
    );
EOSQL