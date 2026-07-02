-- =============================================================================
-- Tuki Database — Row Level Security Policies
-- =============================================================================
-- Apply these to your Supabase instance for RLS.
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE barangays ENABLE ROW LEVEL SECURITY;
ALTER TABLE landmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE jeep_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE jeep_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE jeep_route_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE transfer_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE tricycle_terminals ENABLE ROW LEVEL SECURITY;
ALTER TABLE fare_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE walking_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE walking_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- PUBLIC READ ACCESS (for transport data)
-- =============================================================================
-- Anyone can read transport-related data (no auth required)

CREATE POLICY "Public read access for barangays"
    ON barangays FOR SELECT USING (true);

CREATE POLICY "Public read access for landmarks"
    ON landmarks FOR SELECT USING (true);

CREATE POLICY "Public read access for jeep_routes"
    ON jeep_routes FOR SELECT USING (true);

CREATE POLICY "Public read access for jeep_stops"
    ON jeep_stops FOR SELECT USING (true);

CREATE POLICY "Public read access for jeep_route_stops"
    ON jeep_route_stops FOR SELECT USING (true);

CREATE POLICY "Public read access for transfer_points"
    ON transfer_points FOR SELECT USING (true);

CREATE POLICY "Public read access for tricycle_terminals"
    ON tricycle_terminals FOR SELECT USING (true);

CREATE POLICY "Public read access for fare_matrix"
    ON fare_matrix FOR SELECT USING (true);

CREATE POLICY "Public read access for walking_nodes"
    ON walking_nodes FOR SELECT USING (true);

CREATE POLICY "Public read access for walking_edges"
    ON walking_edges FOR SELECT USING (true);

-- =============================================================================
-- USER PROFILES (private per user)
-- =============================================================================

CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- =============================================================================
-- SERVICE ROLE ACCESS (for backend operations)
-- =============================================================================
-- The service role key bypasses RLS, so no explicit policies needed.
-- This is used by seed scripts and admin operations.
