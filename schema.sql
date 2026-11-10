-- =======================================================
-- Cloud-Native Log Analyzer & Telemetry Pipeline
-- Database Schema for Supabase PostgreSQL Data Warehouse
-- =======================================================

CREATE TABLE IF NOT EXISTS server_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    service_name VARCHAR(50) NOT NULL,
    log_level VARCHAR(10) NOT NULL,
    status_code INT NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    response_time_ms INT NOT NULL,
    client_ip VARCHAR(45),
    message TEXT
);

-- Performance Indexes for Real-Time Querying & Observability
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON server_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON server_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_service ON server_logs(service_name);
CREATE INDEX IF NOT EXISTS idx_logs_endpoint ON server_logs(endpoint);
