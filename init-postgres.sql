-- Initialize PostgreSQL with required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create database user with appropriate permissions
GRANT ALL PRIVILEGES ON DATABASE nasa_publications TO nasa_user;
GRANT ALL ON SCHEMA public TO nasa_user;