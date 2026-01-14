-- ============================================================================
-- AI Ops Copilot - Unified Event Storage Schema
-- ============================================================================
-- Production-ready Postgres schema for normalized operational events
-- Optimized for time-series queries, correlation, and RCA analysis
--
-- Design principles:
-- 1. Store normalized events in structured columns for fast queries
-- 2. Preserve raw payload in JSONB for auditability
-- 3. Index heavily on time, location, asset, and severity
-- 4. Support correlation via incident/ticket/change IDs
-- 5. Enable efficient time-range and pattern queries
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For similarity search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For multi-column indexes

-- ============================================================================
-- Main Events Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS events (
    -- Primary key
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Timestamp (UTC, indexed heavily)
    ts TIMESTAMP WITHOUT TIME ZONE NOT NULL,

    -- Source classification
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN (
        'av', 'network', 'compute', 'app', 'ticket', 'change'
    )),
    source_vendor VARCHAR(50) NOT NULL,
    source_system VARCHAR(200) NOT NULL,

    -- Location hierarchy (normalized for joins)
    site VARCHAR(100),
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),

    -- Asset information (denormalized for query performance)
    asset_id VARCHAR(200),
    asset_type VARCHAR(50),
    asset_make VARCHAR(100),
    asset_model VARCHAR(100),
    asset_serial VARCHAR(200),
    asset_ip INET,  -- PostgreSQL native IP type
    asset_mac MACADDR,  -- PostgreSQL native MAC type
    asset_hostname VARCHAR(200),
    asset_firmware_version VARCHAR(100),

    -- Event classification
    severity VARCHAR(20) NOT NULL CHECK (severity IN (
        'debug', 'info', 'notice', 'warning', 'error', 'critical'
    )),
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'connectivity', 'power', 'audio', 'video', 'control', 'auth',
        'performance', 'config', 'hardware', 'user_action', 'vendor_service'
    )),

    -- Event content
    signal VARCHAR(200) NOT NULL,  -- Stable machine identifier
    message TEXT NOT NULL,  -- Human-readable

    -- Correlation IDs
    incident_id VARCHAR(100),
    ticket_id VARCHAR(100),
    change_id VARCHAR(100),
    correlation_ids JSONB,  -- Flexible key-value pairs

    -- Metadata and tags
    metadata JSONB,
    tags TEXT[],  -- Array for easy searching

    -- Raw data (MANDATORY for auditability)
    raw_line TEXT NOT NULL,
    raw_ts VARCHAR(200),
    source_file VARCHAR(500),
    line_number INTEGER,
    raw_fields JSONB,

    -- Ingestion metadata
    ingested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    parser_version VARCHAR(20) NOT NULL,

    -- Constraints
    CONSTRAINT valid_timestamp CHECK (ts <= NOW() + INTERVAL '1 day'),  -- Sanity check
    CONSTRAINT valid_ingestion CHECK (ingested_at >= ts - INTERVAL '10 years')  -- Reasonable bound
);

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Primary time-series index (most common query pattern)
CREATE INDEX idx_events_ts ON events (ts DESC);

-- Time + severity (for alert queries)
CREATE INDEX idx_events_ts_severity ON events (ts DESC, severity);

-- Time + location (for room/building queries)
CREATE INDEX idx_events_ts_room ON events (ts DESC, room) WHERE room IS NOT NULL;
CREATE INDEX idx_events_ts_building ON events (ts DESC, building) WHERE building IS NOT NULL;

-- Asset queries
CREATE INDEX idx_events_asset_id ON events (asset_id) WHERE asset_id IS NOT NULL;
CREATE INDEX idx_events_asset_ip ON events (asset_ip) WHERE asset_ip IS NOT NULL;
CREATE INDEX idx_events_ts_asset_id ON events (ts DESC, asset_id) WHERE asset_id IS NOT NULL;

-- Correlation queries
CREATE INDEX idx_events_incident_id ON events (incident_id) WHERE incident_id IS NOT NULL;
CREATE INDEX idx_events_ticket_id ON events (ticket_id) WHERE ticket_id IS NOT NULL;
CREATE INDEX idx_events_change_id ON events (change_id) WHERE change_id IS NOT NULL;

-- Source/vendor queries
CREATE INDEX idx_events_source_type ON events (source_type, ts DESC);
CREATE INDEX idx_events_source_vendor ON events (source_vendor, ts DESC);

-- Signal pattern matching (for recurring issues)
CREATE INDEX idx_events_signal ON events (signal, ts DESC);

-- Category analysis
CREATE INDEX idx_events_category ON events (category, ts DESC);

-- Tag searching (GIN index for array containment)
CREATE INDEX idx_events_tags ON events USING GIN (tags);

-- JSONB indexes for metadata searches
CREATE INDEX idx_events_metadata ON events USING GIN (metadata);
CREATE INDEX idx_events_correlation_ids ON events USING GIN (correlation_ids);

-- Full-text search on message field
CREATE INDEX idx_events_message_fts ON events USING GIN (to_tsvector('english', message));

-- Composite index for common RCA queries (time window + room + severity)
CREATE INDEX idx_events_rca_query ON events (ts DESC, room, severity)
    WHERE severity IN ('error', 'critical');

-- ============================================================================
-- Assets Table (for enrichment)
-- ============================================================================

CREATE TABLE IF NOT EXISTS assets (
    asset_id VARCHAR(200) PRIMARY KEY,
    asset_type VARCHAR(50) NOT NULL,

    -- Identification
    make VARCHAR(100),
    model VARCHAR(100),
    serial VARCHAR(200) UNIQUE,
    ip INET,
    mac MACADDR,
    hostname VARCHAR(200),

    -- Location
    site VARCHAR(100),
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),

    -- Status
    status VARCHAR(50),  -- active, maintenance, decommissioned
    last_seen TIMESTAMP WITHOUT TIME ZONE,

    -- Versioning
    firmware_version VARCHAR(100),
    software_version VARCHAR(100),

    -- Metadata
    purchase_date DATE,
    warranty_expiry DATE,
    vendor_support_tier VARCHAR(50),
    notes TEXT,

    -- Flexible metadata
    metadata JSONB,
    tags TEXT[],

    -- Audit
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Asset indexes
CREATE INDEX idx_assets_room ON assets (room) WHERE room IS NOT NULL;
CREATE INDEX idx_assets_building ON assets (building) WHERE building IS NOT NULL;
CREATE INDEX idx_assets_ip ON assets (ip) WHERE ip IS NOT NULL;
CREATE INDEX idx_assets_type ON assets (asset_type);
CREATE INDEX idx_assets_tags ON assets USING GIN (tags);

-- ============================================================================
-- Tickets Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(100) PRIMARY KEY,

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    resolved_at TIMESTAMP WITHOUT TIME ZONE,

    -- Status
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    category VARCHAR(100),

    -- Content
    title TEXT NOT NULL,
    description TEXT,

    -- Location
    site VARCHAR(100),
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),

    -- Assignment
    assigned_to VARCHAR(200),
    assigned_team VARCHAR(100),

    -- Impact
    affected_users INTEGER,
    business_impact TEXT,

    -- Source
    source_system VARCHAR(100) NOT NULL,
    tags TEXT[],
    custom_fields JSONB,

    -- Raw import
    raw_csv_row JSONB,

    -- Audit
    ingested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_tickets_created_at ON tickets (created_at DESC);
CREATE INDEX idx_tickets_status ON tickets (status);
CREATE INDEX idx_tickets_room ON tickets (room) WHERE room IS NOT NULL;
CREATE INDEX idx_tickets_priority ON tickets (priority);

-- ============================================================================
-- Changes Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS changes (
    change_id VARCHAR(100) PRIMARY KEY,
    change_type VARCHAR(100) NOT NULL,

    -- Timestamps
    scheduled_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    executed_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,

    -- Status
    status VARCHAR(50) NOT NULL,

    -- Target
    target_type VARCHAR(100) NOT NULL,
    target_identifier VARCHAR(200) NOT NULL,

    -- Details
    change_description TEXT NOT NULL,
    changed_by VARCHAR(200) NOT NULL,

    -- Versioning
    previous_version VARCHAR(200),
    new_version VARCHAR(200),
    previous_config TEXT,
    new_config TEXT,

    -- Location
    site VARCHAR(100),
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),

    -- Risk assessment
    risk_level VARCHAR(20),
    expected_impact TEXT,
    actual_impact TEXT,

    -- Metadata
    source_system VARCHAR(100) NOT NULL,
    approval_id VARCHAR(100),
    rollback_plan TEXT,

    -- Raw import
    raw_csv_row JSONB,

    -- Audit
    ingested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX idx_changes_scheduled_at ON changes (scheduled_at DESC);
CREATE INDEX idx_changes_executed_at ON changes (executed_at DESC) WHERE executed_at IS NOT NULL;
CREATE INDEX idx_changes_target ON changes (target_type, target_identifier);
CREATE INDEX idx_changes_room ON changes (room) WHERE room IS NOT NULL;
CREATE INDEX idx_changes_type ON changes (change_type);

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- Recent errors by room (refresh every 5 minutes)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_recent_errors_by_room AS
SELECT
    room,
    building,
    COUNT(*) as error_count,
    MAX(ts) as last_error_ts,
    array_agg(DISTINCT signal) as error_signals
FROM events
WHERE
    severity IN ('error', 'critical')
    AND ts > NOW() - INTERVAL '24 hours'
    AND room IS NOT NULL
GROUP BY room, building
ORDER BY error_count DESC;

CREATE UNIQUE INDEX ON mv_recent_errors_by_room (room);

-- Asset health summary
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_asset_health AS
SELECT
    asset_id,
    asset_type,
    room,
    COUNT(*) FILTER (WHERE severity IN ('error', 'critical')) as error_count_24h,
    COUNT(*) FILTER (WHERE severity = 'warning') as warning_count_24h,
    MAX(ts) as last_event_ts,
    MAX(ts) FILTER (WHERE severity IN ('error', 'critical')) as last_error_ts
FROM events
WHERE
    ts > NOW() - INTERVAL '24 hours'
    AND asset_id IS NOT NULL
GROUP BY asset_id, asset_type, room;

CREATE UNIQUE INDEX ON mv_asset_health (asset_id);

-- ============================================================================
-- Partitioning (for large-scale deployments)
-- ============================================================================

-- Uncomment to enable monthly partitioning for events table
-- (Requires manual partition creation or pg_partman extension)

/*
ALTER TABLE events RENAME TO events_template;

CREATE TABLE events (LIKE events_template INCLUDING ALL)
PARTITION BY RANGE (ts);

-- Create partitions (example for 2026)
CREATE TABLE events_2026_01 PARTITION OF events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE events_2026_02 PARTITION OF events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Add more as needed
*/

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_recent_errors_by_room;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_asset_health;
END;
$$ LANGUAGE plpgsql;

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW() AT TIME ZONE 'utc';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Grants (adjust for your security model)
-- ============================================================================

-- Example: Create roles and grant permissions
-- CREATE ROLE aiops_ingest WITH LOGIN PASSWORD 'your_password';
-- CREATE ROLE aiops_readonly WITH LOGIN PASSWORD 'your_password';

-- GRANT INSERT, SELECT ON events, tickets, changes TO aiops_ingest;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO aiops_readonly;

-- ============================================================================
-- Sample Queries (for testing)
-- ============================================================================

-- Find all critical events in a room in the last 24 hours
-- SELECT * FROM events
-- WHERE room = 'CR-101'
--   AND severity = 'critical'
--   AND ts > NOW() - INTERVAL '24 hours'
-- ORDER BY ts DESC;

-- Find events correlated with a change
-- SELECT e.* FROM events e
-- JOIN changes c ON e.ts BETWEEN c.scheduled_at AND c.completed_at + INTERVAL '1 hour'
-- WHERE c.change_id = 'CHG0012345'
-- ORDER BY e.ts;

-- Count events by signal (find recurring issues)
-- SELECT signal, COUNT(*), MAX(ts) as last_occurrence
-- FROM events
-- WHERE ts > NOW() - INTERVAL '7 days'
-- GROUP BY signal
-- ORDER BY COUNT(*) DESC
-- LIMIT 20;
