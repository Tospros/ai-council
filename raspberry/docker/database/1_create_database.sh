#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE ai_council;

  CREATE USER council_user WITH ENCRYPTED PASSWORD 'pass123';

  GRANT CONNECT ON DATABASE ai_council TO council_user;
EOSQL