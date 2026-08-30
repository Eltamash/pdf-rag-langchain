SELECT
    document,
    cmetadata
FROM langchain_pg_embedding
WHERE document ILIKE '%B2B%'
   OR document ILIKE '%Merchandi%';

SELECT
    document,
    cmetadata
FROM langchain_pg_embedding
WHERE document ILIKE '%SWC%'
   OR document ILIKE '%Used Products%';   

-- DELETE FROM langchain_pg_embedding;

SELECT COUNT(*) FROM langchain_pg_embedding;


SELECT
    AVG(LENGTH(document)) AS avg_chars,
    MIN(LENGTH(document)) AS min_chars,
    MAX(LENGTH(document)) AS max_chars
FROM langchain_pg_embedding;