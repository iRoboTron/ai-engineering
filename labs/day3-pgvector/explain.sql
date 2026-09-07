-- ~/proj/ai-labs/day3-pgvector/explain.sql
-- один вектор запроса берём прямо из таблицы, чтобы не тащить его из Python
SET app.tenant_id = '1';
SET enable_indexscan = off;
SET enable_bitmapscan = off;
\set qvec 'SELECT embedding FROM chunks WHERE tenant_id = 1 ORDER BY id LIMIT 1'

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, filename, 1 - (embedding <=> (:qvec)) AS score
FROM chunks ORDER BY embedding <=> (:qvec) LIMIT 5;

RESET enable_indexscan;
RESET enable_bitmapscan;

SET enable_seqscan = off;   -- только для демонстрации на малой таблице
SET hnsw.ef_search = 40;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, filename, 1 - (embedding <=> (:qvec)) AS score
FROM chunks ORDER BY embedding <=> (:qvec) LIMIT 5;

-- ловушка фильтра: селективный фильтр после индекса возвращает меньше LIMIT
SET hnsw.iterative_scan = off;
SELECT count(*) AS rows_without_iterative FROM (
  SELECT id FROM chunks WHERE filename = (SELECT filename FROM chunks WHERE tenant_id = 1 ORDER BY id DESC LIMIT 1)
  ORDER BY embedding <=> (:qvec) LIMIT 5) t;

SET hnsw.iterative_scan = strict_order;
SELECT count(*) AS rows_with_iterative FROM (
  SELECT id FROM chunks WHERE filename = (SELECT filename FROM chunks WHERE tenant_id = 1 ORDER BY id DESC LIMIT 1)
  ORDER BY embedding <=> (:qvec) LIMIT 5) t;
RESET enable_seqscan;
