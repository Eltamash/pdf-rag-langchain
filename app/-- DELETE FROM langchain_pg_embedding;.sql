-- DELETE FROM langchain_pg_embedding;

SELECT COUNT(*) FROM langchain_pg_embedding;


SELECT
    AVG(LENGTH(document)) AS avg_chars,
    MIN(LENGTH(document)) AS min_chars,
    MAX(LENGTH(document)) AS max_chars
FROM langchain_pg_embedding;

DeprecationWarning: `langchain-community` is being sunset and is no longer actively maintained. 
See https://github.com/langchain-ai/langchain-community/issues/674 for details and migration guidance 
toward standalone integration packages.
from langchain_community.document_loaders import PyPDFLoader