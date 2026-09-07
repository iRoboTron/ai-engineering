-- ~/proj/ai-labs/day3-pgvector/schema.sql
\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS vector;
DO $roles$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rag_app') THEN
        CREATE ROLE rag_app LOGIN NOSUPERUSER NOBYPASSRLS;
    END IF;
END
$roles$;
ALTER ROLE rag_app WITH LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD :'app_password';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO rag_app;
CREATE TABLE IF NOT EXISTS chunks (
    id          text PRIMARY KEY,
    tenant_id   int NOT NULL,
    filename    text NOT NULL,
    chunk_index int NOT NULL,
    text        text NOT NULL,
    embedding   vector(1536) NOT NULL,
    tsv         tsvector GENERATED ALWAYS AS (to_tsvector('russian', text)) STORED
);
CREATE TABLE IF NOT EXISTS lab_snapshot (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    config jsonb NOT NULL
);
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON chunks;
CREATE POLICY tenant_isolation ON chunks
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::int);
REVOKE ALL ON chunks, lab_snapshot FROM PUBLIC;
GRANT SELECT ON chunks, lab_snapshot TO rag_app;
