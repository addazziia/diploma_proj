CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action_type VARCHAR(50),
    filename VARCHAR(255),
    details TEXT,
    operator VARCHAR(100)
);

SET TIME ZONE 'Asia/Almaty';

SELECT * FROM logs ORDER BY timestamp DESC;
