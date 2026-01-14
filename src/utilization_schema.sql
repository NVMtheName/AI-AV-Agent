-- ============================================================================
-- Room Utilization Analytics Schema
-- ============================================================================
-- Tables for tracking room utilization, bookings, and occupancy metrics
-- Designed for comprehensive analytics and optimization recommendations
-- ============================================================================

-- ============================================================================
-- Room Meetings Table - Track all scheduled and actual meetings
-- ============================================================================

CREATE TABLE IF NOT EXISTS room_meetings (
    -- Primary key
    meeting_id VARCHAR(200) PRIMARY KEY,

    -- Room identification
    room_id VARCHAR(200) NOT NULL,
    room_name VARCHAR(200) NOT NULL,

    -- Location hierarchy
    site VARCHAR(100),
    building VARCHAR(100),
    floor VARCHAR(50),

    -- Scheduling information
    scheduled_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    scheduled_end TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    scheduled_duration_minutes INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (scheduled_end - scheduled_start)) / 60
    ) STORED,

    -- Actual meeting information
    actual_start TIMESTAMP WITHOUT TIME ZONE,
    actual_end TIMESTAMP WITHOUT TIME ZONE,
    actual_duration_minutes INTEGER,

    -- Attendance tracking
    scheduled_participants INTEGER DEFAULT 0,
    actual_participants INTEGER DEFAULT 0,
    max_participants INTEGER DEFAULT 0,  -- Peak during meeting

    -- Meeting status
    status VARCHAR(50) CHECK (status IN (
        'scheduled', 'in_progress', 'completed', 'no_show', 'cancelled', 'early_departure'
    )),

    -- Utilization flags
    is_ghost_booking BOOLEAN DEFAULT FALSE,  -- Scheduled but zero participants
    is_no_show BOOLEAN DEFAULT FALSE,        -- Scheduled but never started
    is_early_departure BOOLEAN DEFAULT FALSE, -- Ended significantly before scheduled

    -- Meeting metadata
    meeting_topic VARCHAR(500),
    organizer_email VARCHAR(200),
    organizer_name VARCHAR(200),
    meeting_type VARCHAR(50),  -- scheduled, instant, recurring
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_meeting_id VARCHAR(200),

    -- Quality metrics
    audio_quality_score DECIMAL(3,2),  -- 0.00 to 5.00
    video_quality_score DECIMAL(3,2),
    overall_quality_score DECIMAL(3,2),
    had_technical_issues BOOLEAN DEFAULT FALSE,

    -- Data source
    data_source VARCHAR(50) DEFAULT 'zoom_api',
    zoom_meeting_uuid VARCHAR(200),

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),

    -- Metadata
    metadata JSONB,

    -- Indexes
    CONSTRAINT valid_scheduled_times CHECK (scheduled_end > scheduled_start),
    CONSTRAINT valid_actual_times CHECK (actual_end IS NULL OR actual_end >= actual_start)
);

-- Indexes for room_meetings
CREATE INDEX idx_room_meetings_room_id ON room_meetings (room_id);
CREATE INDEX idx_room_meetings_scheduled_start ON room_meetings (scheduled_start DESC);
CREATE INDEX idx_room_meetings_status ON room_meetings (status);
CREATE INDEX idx_room_meetings_room_date ON room_meetings (room_id, scheduled_start DESC);
CREATE INDEX idx_room_meetings_no_show ON room_meetings (is_no_show) WHERE is_no_show = TRUE;
CREATE INDEX idx_room_meetings_ghost ON room_meetings (is_ghost_booking) WHERE is_ghost_booking = TRUE;
CREATE INDEX idx_room_meetings_building ON room_meetings (building, scheduled_start DESC);

-- ============================================================================
-- Room Utilization Daily - Aggregated daily statistics per room
-- ============================================================================

CREATE TABLE IF NOT EXISTS room_utilization_daily (
    -- Composite primary key
    utilization_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id VARCHAR(200) NOT NULL,
    date DATE NOT NULL,

    -- Room information
    room_name VARCHAR(200) NOT NULL,
    building VARCHAR(100),
    floor VARCHAR(50),

    -- Availability
    total_available_hours DECIMAL(5,2) NOT NULL DEFAULT 24.00,  -- Configurable business hours
    business_hours_start TIME DEFAULT '08:00:00',
    business_hours_end TIME DEFAULT '18:00:00',

    -- Scheduled utilization
    total_scheduled_hours DECIMAL(5,2) DEFAULT 0,
    total_scheduled_meetings INTEGER DEFAULT 0,

    -- Actual utilization
    total_actual_hours DECIMAL(5,2) DEFAULT 0,
    total_completed_meetings INTEGER DEFAULT 0,

    -- Utilization rates (percentages)
    scheduled_utilization_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_available_hours > 0
            THEN (total_scheduled_hours / total_available_hours) * 100
            ELSE 0
        END
    ) STORED,

    actual_utilization_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_available_hours > 0
            THEN (total_actual_hours / total_available_hours) * 100
            ELSE 0
        END
    ) STORED,

    -- Efficiency metrics
    booking_efficiency_rate DECIMAL(5,2),  -- actual_hours / scheduled_hours * 100

    -- Problem tracking
    total_no_shows INTEGER DEFAULT 0,
    total_ghost_bookings INTEGER DEFAULT 0,
    total_early_departures INTEGER DEFAULT 0,
    total_cancelled_meetings INTEGER DEFAULT 0,

    no_show_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_scheduled_meetings > 0
            THEN (total_no_shows::DECIMAL / total_scheduled_meetings) * 100
            ELSE 0
        END
    ) STORED,

    -- Participant metrics
    total_participants INTEGER DEFAULT 0,
    avg_participants_per_meeting DECIMAL(5,2),
    max_participants_in_day INTEGER DEFAULT 0,

    -- Average meeting duration
    avg_scheduled_duration_minutes DECIMAL(5,2),
    avg_actual_duration_minutes DECIMAL(5,2),

    -- Peak usage
    peak_hour_start TIME,  -- Hour with most meetings
    peak_hour_meetings INTEGER DEFAULT 0,

    -- Quality metrics
    avg_quality_score DECIMAL(3,2),
    meetings_with_issues INTEGER DEFAULT 0,

    -- Timestamps
    calculated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),

    -- Metadata
    metadata JSONB,

    -- Unique constraint
    CONSTRAINT unique_room_date UNIQUE (room_id, date)
);

-- Indexes for room_utilization_daily
CREATE INDEX idx_utilization_daily_room_id ON room_utilization_daily (room_id);
CREATE INDEX idx_utilization_daily_date ON room_utilization_daily (date DESC);
CREATE INDEX idx_utilization_daily_room_date ON room_utilization_daily (room_id, date DESC);
CREATE INDEX idx_utilization_daily_building_date ON room_utilization_daily (building, date DESC);
CREATE INDEX idx_utilization_daily_actual_rate ON room_utilization_daily (actual_utilization_rate DESC);
CREATE INDEX idx_utilization_daily_low_util ON room_utilization_daily (actual_utilization_rate)
    WHERE actual_utilization_rate < 30;

-- ============================================================================
-- Room Utilization Hourly - Hourly breakdown for heatmaps
-- ============================================================================

CREATE TABLE IF NOT EXISTS room_utilization_hourly (
    -- Composite primary key
    utilization_hourly_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id VARCHAR(200) NOT NULL,
    date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour < 24),

    -- Room information
    room_name VARCHAR(200) NOT NULL,
    building VARCHAR(100),
    floor VARCHAR(50),

    -- Hourly metrics
    is_business_hour BOOLEAN DEFAULT TRUE,
    total_meetings INTEGER DEFAULT 0,
    total_minutes_scheduled INTEGER DEFAULT 0,
    total_minutes_actual INTEGER DEFAULT 0,

    -- Utilization percentage for this hour (0-100)
    hourly_utilization_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_minutes_actual > 60 THEN 100.00
            ELSE (total_minutes_actual::DECIMAL / 60.0) * 100
        END
    ) STORED,

    -- Status during this hour
    status_at_hour VARCHAR(50),  -- Available, In Meeting, Offline

    -- Meeting count
    meetings_started INTEGER DEFAULT 0,
    meetings_ended INTEGER DEFAULT 0,
    meetings_ongoing INTEGER DEFAULT 0,

    -- Participants
    total_participants INTEGER DEFAULT 0,

    -- Timestamps
    calculated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),

    -- Unique constraint
    CONSTRAINT unique_room_date_hour UNIQUE (room_id, date, hour)
);

-- Indexes for room_utilization_hourly
CREATE INDEX idx_utilization_hourly_room_id ON room_utilization_hourly (room_id);
CREATE INDEX idx_utilization_hourly_date ON room_utilization_hourly (date DESC);
CREATE INDEX idx_utilization_hourly_room_date ON room_utilization_hourly (room_id, date DESC);
CREATE INDEX idx_utilization_hourly_hour ON room_utilization_hourly (hour);
CREATE INDEX idx_utilization_hourly_rate ON room_utilization_hourly (hourly_utilization_rate DESC);

-- ============================================================================
-- Room Configuration - Track room capacity and availability settings
-- ============================================================================

CREATE TABLE IF NOT EXISTS room_configuration (
    room_id VARCHAR(200) PRIMARY KEY,
    room_name VARCHAR(200) NOT NULL,

    -- Location
    building VARCHAR(100),
    floor VARCHAR(50),
    site VARCHAR(100),

    -- Capacity
    max_capacity INTEGER,
    recommended_capacity INTEGER,

    -- Availability schedule
    business_hours_start TIME DEFAULT '08:00:00',
    business_hours_end TIME DEFAULT '18:00:00',
    available_monday BOOLEAN DEFAULT TRUE,
    available_tuesday BOOLEAN DEFAULT TRUE,
    available_wednesday BOOLEAN DEFAULT TRUE,
    available_thursday BOOLEAN DEFAULT TRUE,
    available_friday BOOLEAN DEFAULT TRUE,
    available_saturday BOOLEAN DEFAULT FALSE,
    available_sunday BOOLEAN DEFAULT FALSE,

    -- Room characteristics
    room_type VARCHAR(50),  -- conference, huddle, training, etc.
    has_zoom_rooms BOOLEAN DEFAULT TRUE,
    has_calendar_integration BOOLEAN DEFAULT FALSE,

    -- Equipment
    has_display BOOLEAN DEFAULT FALSE,
    has_whiteboard BOOLEAN DEFAULT FALSE,
    has_video_conferencing BOOLEAN DEFAULT FALSE,

    -- Utilization thresholds (for recommendations)
    low_utilization_threshold DECIMAL(5,2) DEFAULT 30.00,
    high_utilization_threshold DECIMAL(5,2) DEFAULT 80.00,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_bookable BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),

    -- Metadata
    metadata JSONB
);

-- Indexes for room_configuration
CREATE INDEX idx_room_config_building ON room_configuration (building);
CREATE INDEX idx_room_config_type ON room_configuration (room_type);
CREATE INDEX idx_room_config_active ON room_configuration (is_active) WHERE is_active = TRUE;

-- ============================================================================
-- Utilization Recommendations - Store optimization recommendations
-- ============================================================================

CREATE TABLE IF NOT EXISTS utilization_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Target room
    room_id VARCHAR(200) NOT NULL,
    room_name VARCHAR(200) NOT NULL,
    building VARCHAR(100),

    -- Recommendation details
    recommendation_type VARCHAR(50) CHECK (recommendation_type IN (
        'underutilized_repurpose',
        'overbooked_expansion',
        'high_no_show_policy',
        'optimal_timing',
        'capacity_mismatch',
        'equipment_upgrade'
    )),

    priority VARCHAR(20) CHECK (priority IN ('low', 'medium', 'high', 'critical')),

    -- Recommendation content
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    recommended_action TEXT,

    -- Supporting metrics
    utilization_rate DECIMAL(5,2),
    no_show_rate DECIMAL(5,2),
    avg_occupancy DECIMAL(5,2),

    -- Time period analyzed
    analysis_start_date DATE NOT NULL,
    analysis_end_date DATE NOT NULL,
    days_analyzed INTEGER,

    -- Impact estimation
    estimated_hours_saved DECIMAL(8,2),
    estimated_cost_impact DECIMAL(12,2),

    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'reviewed', 'approved', 'implemented', 'dismissed'
    )),

    reviewed_by VARCHAR(200),
    reviewed_at TIMESTAMP WITHOUT TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc'),

    -- Metadata
    supporting_data JSONB,
    metadata JSONB
);

-- Indexes for utilization_recommendations
CREATE INDEX idx_recommendations_room_id ON utilization_recommendations (room_id);
CREATE INDEX idx_recommendations_type ON utilization_recommendations (recommendation_type);
CREATE INDEX idx_recommendations_priority ON utilization_recommendations (priority);
CREATE INDEX idx_recommendations_status ON utilization_recommendations (status);
CREATE INDEX idx_recommendations_created ON utilization_recommendations (created_at DESC);

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- Weekly utilization summary by room
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_room_utilization_weekly AS
SELECT
    room_id,
    room_name,
    building,
    DATE_TRUNC('week', date)::DATE as week_start,
    AVG(actual_utilization_rate) as avg_utilization_rate,
    SUM(total_actual_hours) as total_hours_used,
    SUM(total_completed_meetings) as total_meetings,
    AVG(no_show_rate) as avg_no_show_rate,
    AVG(avg_participants_per_meeting) as avg_participants,
    COUNT(*) as days_with_data
FROM room_utilization_daily
GROUP BY room_id, room_name, building, DATE_TRUNC('week', date);

CREATE INDEX idx_mv_weekly_room ON mv_room_utilization_weekly (room_id);
CREATE INDEX idx_mv_weekly_week ON mv_room_utilization_weekly (week_start DESC);

-- Monthly utilization summary by room
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_room_utilization_monthly AS
SELECT
    room_id,
    room_name,
    building,
    DATE_TRUNC('month', date)::DATE as month_start,
    AVG(actual_utilization_rate) as avg_utilization_rate,
    SUM(total_actual_hours) as total_hours_used,
    SUM(total_completed_meetings) as total_meetings,
    AVG(no_show_rate) as avg_no_show_rate,
    AVG(avg_participants_per_meeting) as avg_participants,
    COUNT(*) as days_with_data
FROM room_utilization_daily
GROUP BY room_id, room_name, building, DATE_TRUNC('month', date);

CREATE INDEX idx_mv_monthly_room ON mv_room_utilization_monthly (room_id);
CREATE INDEX idx_mv_monthly_month ON mv_room_utilization_monthly (month_start DESC);

-- Room ranking by utilization (last 30 days)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_room_ranking AS
SELECT
    room_id,
    room_name,
    building,
    AVG(actual_utilization_rate) as avg_utilization_rate,
    SUM(total_completed_meetings) as total_meetings,
    AVG(no_show_rate) as avg_no_show_rate,
    AVG(avg_participants_per_meeting) as avg_participants,
    MAX(date) as last_updated,
    ROW_NUMBER() OVER (ORDER BY AVG(actual_utilization_rate) DESC) as utilization_rank
FROM room_utilization_daily
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY room_id, room_name, building;

CREATE INDEX idx_mv_ranking_rank ON mv_room_ranking (utilization_rank);
CREATE INDEX idx_mv_ranking_rate ON mv_room_ranking (avg_utilization_rate DESC);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to refresh all utilization materialized views
CREATE OR REPLACE FUNCTION refresh_utilization_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_room_utilization_weekly;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_room_utilization_monthly;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_room_ranking;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate meeting efficiency
CREATE OR REPLACE FUNCTION calculate_meeting_efficiency(
    p_actual_duration INTEGER,
    p_scheduled_duration INTEGER
)
RETURNS DECIMAL(5,2) AS $$
BEGIN
    IF p_scheduled_duration IS NULL OR p_scheduled_duration = 0 THEN
        RETURN NULL;
    END IF;

    RETURN ROUND((p_actual_duration::DECIMAL / p_scheduled_duration) * 100, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to determine if meeting is a no-show
CREATE OR REPLACE FUNCTION is_meeting_no_show(
    p_scheduled_start TIMESTAMP,
    p_actual_start TIMESTAMP,
    p_grace_minutes INTEGER DEFAULT 15
)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_actual_start IS NULL THEN
        -- If past scheduled start + grace period and still no actual start
        IF NOW() > p_scheduled_start + (p_grace_minutes || ' minutes')::INTERVAL THEN
            RETURN TRUE;
        END IF;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Update Triggers
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = (NOW() AT TIME ZONE 'utc');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_room_meetings_updated_at
    BEFORE UPDATE ON room_meetings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_room_configuration_updated_at
    BEFORE UPDATE ON room_configuration
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE room_meetings IS 'Tracks all scheduled and actual meeting data for room utilization analysis';
COMMENT ON TABLE room_utilization_daily IS 'Daily aggregated utilization statistics per room';
COMMENT ON TABLE room_utilization_hourly IS 'Hourly utilization data for heatmap visualizations';
COMMENT ON TABLE room_configuration IS 'Room configuration and availability settings';
COMMENT ON TABLE utilization_recommendations IS 'AI-generated optimization recommendations for room usage';

COMMENT ON COLUMN room_meetings.is_ghost_booking IS 'Meeting scheduled but had zero participants';
COMMENT ON COLUMN room_meetings.is_no_show IS 'Meeting scheduled but never started';
COMMENT ON COLUMN room_meetings.is_early_departure IS 'Meeting ended significantly before scheduled end time';

COMMENT ON MATERIALIZED VIEW mv_room_utilization_weekly IS 'Weekly aggregation of room utilization metrics';
COMMENT ON MATERIALIZED VIEW mv_room_utilization_monthly IS 'Monthly aggregation of room utilization metrics';
COMMENT ON MATERIALIZED VIEW mv_room_ranking IS 'Room ranking by utilization rate (last 30 days)';
