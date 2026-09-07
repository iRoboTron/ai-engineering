-- ~/proj/ai-labs/day3-pgvector/rls_demo.sql
\set ON_ERROR_STOP on
DO $check$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = current_user AND (rolsuper OR rolbypassrls)) THEN
        RAISE EXCEPTION 'тест должен выполняться прикладной ролью';
    END IF;
END
$check$;
SET app.tenant_id = '1';
SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id;
DO $check$
BEGIN
    IF NOT EXISTS (SELECT FROM chunks) OR EXISTS (SELECT FROM chunks WHERE tenant_id <> 1) THEN
        RAISE EXCEPTION 'изоляция tenant 1 не работает или данные не загружены';
    END IF;
END
$check$;
SET app.tenant_id = '2';
SELECT tenant_id, count(*) FROM chunks GROUP BY tenant_id;
DO $check$
BEGIN
    IF NOT EXISTS (SELECT FROM chunks) OR EXISTS (SELECT FROM chunks WHERE tenant_id <> 2) THEN
        RAISE EXCEPTION 'изоляция tenant 2 не работает или данные не загружены';
    END IF;
END
$check$;
RESET app.tenant_id;
SELECT count(*) AS visible_without_tenant FROM chunks;
DO $check$
BEGIN
    IF EXISTS (SELECT FROM chunks) THEN
        RAISE EXCEPTION 'RESET оставил доступ к данным';
    END IF;
END
$check$;
BEGIN;
SELECT set_config('app.tenant_id', '1', true);
SELECT count(*) AS leak_attempt FROM chunks WHERE tenant_id = 2;
DO $check$
BEGIN
    IF EXISTS (SELECT FROM chunks WHERE tenant_id = 2) THEN
        RAISE EXCEPTION 'обход фильтра';
    END IF;
END
$check$;
COMMIT;
DO $check$
BEGIN
    IF EXISTS (SELECT FROM chunks) THEN
        RAISE EXCEPTION 'tenant остался после транзакции';
    END IF;
END
$check$;
