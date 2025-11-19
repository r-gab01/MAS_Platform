CREATE EXTENSION IF NOT EXISTS vector;

SELECT * FROM pg_extension WHERE extname = 'vector';

CREATE TABLE items (id SERIAL PRIMARY KEY, embedding vector(1024));