SELECT
    document,
    cmetadata
FROM langchain_pg_embedding
WHERE document ILIKE '%POLYCOMP%'
   OR document ILIKE '%IMAGERUNNER%';

SELECT DISTINCT cmetadata FROM langchain_pg_embedding where cmetadata like '%Order%';

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