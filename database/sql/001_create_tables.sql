-- =============================================================================
-- Tuki Database — Full Schema
-- =============================================================================
-- Run this against your Supabase PostgreSQL instance.
-- Requires PostGIS extension.
-- =============================================================================

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- BARANGAYS
-- =============================================================================
CREATE TABLE IF NOT EXISTS barangays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    barangay_name VARCHAR(255) NOT NULL UNIQUE,
    psgc_code VARCHAR(20) UNIQUE,
    geometry GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_barangays_name ON barangays (barangay_name);
CREATE INDEX IF NOT EXISTS idx_barangays_geometry ON barangays USING GIST (geometry);

-- =============================================================================
-- LANDMARKS
-- =============================================================================
CREATE TYPE landmark_category AS ENUM (
    'school', 'mall', 'hospital', 'government', 'church',
    'terminal', 'market', 'restaurant', 'hotel', 'park',
    'bank', 'gas_station', 'other'
);

CREATE TABLE IF NOT EXISTS landmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    aliases TEXT[],
    category landmark_category NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(POINT, 4326) NOT NULL,
    barangay_id UUID REFERENCES barangays(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_landmarks_name ON landmarks (name);
CREATE INDEX IF NOT EXISTS idx_landmarks_category ON landmarks (category);
CREATE INDEX IF NOT EXISTS idx_landmarks_barangay ON landmarks (barangay_id);
CREATE INDEX IF NOT EXISTS idx_landmarks_geometry ON landmarks USING GIST (geometry);

-- =============================================================================
-- JEEP ROUTES
-- =============================================================================
CREATE TABLE IF NOT EXISTS jeep_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_name VARCHAR(255) NOT NULL UNIQUE,
    route_color VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    operating_direction VARCHAR(100),
    geometry GEOMETRY(MULTILINESTRING, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jeep_routes_name ON jeep_routes (route_name);
CREATE INDEX IF NOT EXISTS idx_jeep_routes_color ON jeep_routes (route_color);
CREATE INDEX IF NOT EXISTS idx_jeep_routes_geometry ON jeep_routes USING GIST (geometry);

-- =============================================================================
-- JEEP STOPS
-- =============================================================================
CREATE TABLE IF NOT EXISTS jeep_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stop_name VARCHAR(255) NOT NULL UNIQUE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(POINT, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jeep_stops_name ON jeep_stops (stop_name);
CREATE INDEX IF NOT EXISTS idx_jeep_stops_geometry ON jeep_stops USING GIST (geometry);

-- =============================================================================
-- JEEP ROUTE STOPS (association)
-- =============================================================================
CREATE TABLE IF NOT EXISTS jeep_route_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jeep_route_id UUID NOT NULL REFERENCES jeep_routes(id) ON DELETE CASCADE,
    stop_id UUID NOT NULL REFERENCES jeep_stops(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    UNIQUE (jeep_route_id, stop_id)
);

CREATE INDEX IF NOT EXISTS idx_jeep_route_stops_route ON jeep_route_stops (jeep_route_id);
CREATE INDEX IF NOT EXISTS idx_jeep_route_stops_stop ON jeep_route_stops (stop_id);

-- =============================================================================
-- TRANSFER POINTS
-- =============================================================================
CREATE TYPE transfer_type AS ENUM (
    'jeep_jeep', 'jeep_walk', 'walk_tricycle',
    'jeep_tricycle', 'walk_jeep', 'tricycle_walk'
);

CREATE TABLE IF NOT EXISTS transfer_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    geometry GEOMETRY(POINT, 4326) NOT NULL,
    from_route_id UUID REFERENCES jeep_routes(id) ON DELETE SET NULL,
    to_route_id UUID REFERENCES jeep_routes(id) ON DELETE SET NULL,
    transfer_type transfer_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transfer_points_name ON transfer_points (name);
CREATE INDEX IF NOT EXISTS idx_transfer_points_from ON transfer_points (from_route_id);
CREATE INDEX IF NOT EXISTS idx_transfer_points_to ON transfer_points (to_route_id);
CREATE INDEX IF NOT EXISTS idx_transfer_points_type ON transfer_points (transfer_type);
CREATE INDEX IF NOT EXISTS idx_transfer_points_geometry ON transfer_points USING GIST (geometry);

-- =============================================================================
-- TRICYCLE TERMINALS
-- =============================================================================
CREATE TABLE IF NOT EXISTS tricycle_terminals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(POINT, 4326) NOT NULL,
    service_area GEOMETRY(POLYGON, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tricycle_terminals_name ON tricycle_terminals (name);
CREATE INDEX IF NOT EXISTS idx_tricycle_terminals_geometry ON tricycle_terminals USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_tricycle_terminals_service ON tricycle_terminals USING GIST (service_area);

-- =============================================================================
-- FARE MATRIX
-- =============================================================================
CREATE TABLE IF NOT EXISTS fare_matrix (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transport_type VARCHAR(50) NOT NULL,
    distance_km DOUBLE PRECISION NOT NULL,
    regular_fare DOUBLE PRECISION NOT NULL,
    discounted_fare DOUBLE PRECISION NOT NULL,
    student_fare DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fare_matrix_type ON fare_matrix (transport_type);

-- =============================================================================
-- WALKING NETWORK (OSM)
-- =============================================================================
CREATE TABLE IF NOT EXISTS walking_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    osm_id BIGINT NOT NULL UNIQUE,
    geometry GEOMETRY(POINT, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_walking_nodes_osm ON walking_nodes (osm_id);
CREATE INDEX IF NOT EXISTS idx_walking_nodes_geometry ON walking_nodes USING GIST (geometry);

CREATE TABLE IF NOT EXISTS walking_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID NOT NULL REFERENCES walking_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES walking_nodes(id) ON DELETE CASCADE,
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    length_m DOUBLE PRECISION NOT NULL,
    highway_type VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_walking_edges_source ON walking_edges (source_node_id);
CREATE INDEX IF NOT EXISTS idx_walking_edges_target ON walking_edges (target_node_id);
CREATE INDEX IF NOT EXISTS idx_walking_edges_geometry ON walking_edges USING GIST (geometry);

-- =============================================================================
-- USER PROFILES
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,  -- Matches Supabase Auth user UUID
    email VARCHAR(320) NOT NULL UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles (email);
