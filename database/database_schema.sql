
CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE time_dimensions (
    time_id SERIAL PRIMARY KEY,
    pickup_datetime TIMESTAMP NOT NULL UNIQUE,
    pickup_hour INTEGER NOT NULL CHECK (pickup_hour >= 0 AND pickup_hour < 24),
    pickup_day INTEGER NOT NULL CHECK (pickup_day >= 1 AND pickup_day <= 31),
    pickup_month INTEGER NOT NULL CHECK (pickup_month >= 1 AND pickup_month <= 12),
    pickup_weekday INTEGER NOT NULL CHECK (pickup_weekday >= 0 AND pickup_weekday <= 6),
    pickup_year INTEGER NOT NULL,
    time_of_day VARCHAR(20) CHECK (time_of_day IN ('morning', 'afternoon', 'evening', 'night')),
    is_weekend BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    location_type VARCHAR(20) CHECK (location_type IN ('pickup', 'dropoff', 'both')),
    zone_name VARCHAR(100),
    borough VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(latitude, longitude)
);


CREATE TABLE trip_facts (
    trip_id VARCHAR(50) PRIMARY KEY,
    vendor_id INTEGER NOT NULL,
    pickup_location_id INTEGER NOT NULL,
    dropoff_location_id INTEGER NOT NULL,
    time_id INTEGER NOT NULL,
    pickup_datetime TIMESTAMP NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,
    trip_duration INTEGER NOT NULL CHECK (trip_duration > 0),
    trip_distance_km DECIMAL(10, 3) NOT NULL CHECK (trip_distance_km >= 0),
    trip_speed_kmh DECIMAL(10, 3) CHECK (trip_speed_kmh >= 0 AND trip_speed_kmh <= 120),
    trip_efficiency DECIMAL(10, 3) CHECK (trip_efficiency >= 0),
    passenger_count INTEGER CHECK (passenger_count >= 1 AND passenger_count <= 6),
    store_and_fwd_flag VARCHAR(1) CHECK (store_and_fwd_flag IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_vendor FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    CONSTRAINT fk_pickup_location FOREIGN KEY (pickup_location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_dropoff_location FOREIGN KEY (dropoff_location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_time FOREIGN KEY (time_id) REFERENCES time_dimensions(time_id),
    
    CONSTRAINT valid_trip_timing CHECK (dropoff_datetime > pickup_datetime)
);

-- =============================================================================
-- DATA QUALITY LOGGING TABLE
-- =============================================================================

CREATE TABLE data_quality_log (
    log_id SERIAL PRIMARY KEY,
    load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_records_processed INTEGER,
    records_inserted INTEGER,
    records_rejected INTEGER,
    rejection_reason TEXT,
    load_status VARCHAR(20) CHECK (load_status IN ('SUCCESS', 'PARTIAL', 'FAILED'))
);

-- INDEXES for Query Performance


CREATE INDEX idx_trip_pickup_datetime ON trip_facts(pickup_datetime);
CREATE INDEX idx_trip_dropoff_datetime ON trip_facts(dropoff_datetime);
CREATE INDEX idx_trip_vendor ON trip_facts(vendor_id);
CREATE INDEX idx_trip_pickup_location ON trip_facts(pickup_location_id);
CREATE INDEX idx_trip_dropoff_location ON trip_facts(dropoff_location_id);
CREATE INDEX idx_trip_time_id ON trip_facts(time_id);
CREATE INDEX idx_trip_distance ON trip_facts(trip_distance_km);
CREATE INDEX idx_trip_duration ON trip_facts(trip_duration);
CREATE INDEX idx_trip_speed ON trip_facts(trip_speed_kmh);
CREATE INDEX idx_trip_datetime_vendor ON trip_facts(pickup_datetime, vendor_id);
CREATE INDEX idx_trip_location_datetime ON trip_facts(pickup_location_id, pickup_datetime);
CREATE INDEX idx_time_hour ON time_dimensions(pickup_hour);
CREATE INDEX idx_time_weekday ON time_dimensions(pickup_weekday);
CREATE INDEX idx_time_month ON time_dimensions(pickup_month);
CREATE INDEX idx_time_weekend ON time_dimensions(is_weekend);
CREATE INDEX idx_time_of_day ON time_dimensions(time_of_day);
CREATE INDEX idx_location_coords ON locations(latitude, longitude);
CREATE INDEX idx_location_zone ON locations(zone_name);




-- VIEWS for Analytics Queries

-- Hourly trip statistics view
CREATE OR REPLACE VIEW hourly_trip_stats AS
SELECT 
    td.pickup_hour,
    td.time_of_day,
    td.is_weekend,
    COUNT(*) as trip_count,
    AVG(tf.trip_distance_km) as avg_distance,
    AVG(tf.trip_duration) as avg_duration,
    AVG(tf.trip_speed_kmh) as avg_speed,
    SUM(tf.trip_distance_km) as total_distance
FROM trip_facts tf
JOIN time_dimensions td ON tf.time_id = td.time_id
GROUP BY td.pickup_hour, td.time_of_day, td.is_weekend;

-- Daily trip statistics view
CREATE OR REPLACE VIEW daily_trip_stats AS
SELECT 
    DATE(td.pickup_datetime) as trip_date,
    td.is_weekend,
    COUNT(*) as trip_count,
    AVG(tf.trip_distance_km) as avg_distance,
    AVG(tf.trip_duration) as avg_duration,
    AVG(tf.trip_speed_kmh) as avg_speed
FROM trip_facts tf
JOIN time_dimensions td ON tf.time_id = td.time_id
GROUP BY DATE(td.pickup_datetime), td.is_weekend;

-- Location-based trip statistics
CREATE OR REPLACE VIEW location_trip_stats AS
SELECT 
    l.location_id,
    l.latitude,
    l.longitude,
    l.zone_name,
    COUNT(*) as pickup_count
FROM trip_facts tf
JOIN locations l ON tf.pickup_location_id = l.location_id
GROUP BY l.location_id, l.latitude, l.longitude, l.zone_name;




-- Insert vendor data
INSERT INTO vendors (vendor_id, vendor_name, description) VALUES
(1, 'Creative Mobile Technologies', 'Primary NYC taxi technology provider'),
(2, 'VeriFone Inc', 'Secondary NYC taxi technology provider');

COMMENT ON TABLE vendors IS 'Dimension table storing taxi service vendors';
COMMENT ON TABLE time_dimensions IS 'Dimension table for temporal analysis';
COMMENT ON TABLE locations IS 'Dimension table for geographic locations';
COMMENT ON TABLE trip_facts IS 'Fact table containing all taxi trip records';
COMMENT ON TABLE data_quality_log IS 'Audit log for data loading operations';