-- Create indexes for frequently accessed columns
CREATE INDEX IF NOT EXISTS idx_hotels_city ON hotels(city);
CREATE INDEX IF NOT EXISTS idx_hotels_price ON hotels(price);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date);
CREATE INDEX IF NOT EXISTS idx_price_history_hotel_id ON price_history(hotel_id);

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_hotels_city_price ON hotels(city, price);
CREATE INDEX IF NOT EXISTS idx_price_history_hotel_date ON price_history(hotel_id, date);

-- Optimize full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_hotels_name_trgm ON hotels USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_hotels_description_trgm ON hotels USING gin(description gin_trgm_ops);

-- Set up table partitioning for price_history
CREATE TABLE IF NOT EXISTS price_history_partitioned (
    id SERIAL,
    hotel_id INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (date);

-- Create partitions for the last 12 months
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months');
    end_date DATE;
BEGIN
    FOR i IN 0..12 LOOP
        end_date := start_date + INTERVAL '1 month';
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS price_history_y%sm%s ' ||
            'PARTITION OF price_history_partitioned ' ||
            'FOR VALUES FROM (%L) TO (%L)',
            date_part('year', start_date),
            date_part('month', start_date),
            start_date,
            end_date
        );
        start_date := end_date;
    END LOOP;
END $$;

-- Optimize query performance
ALTER TABLE hotels SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE price_history SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Create materialized view for common analytics queries
CREATE MATERIALIZED VIEW IF NOT EXISTS hotel_price_stats AS
SELECT 
    h.id,
    h.name,
    h.city,
    AVG(ph.price) as avg_price,
    MIN(ph.price) as min_price,
    MAX(ph.price) as max_price,
    COUNT(ph.id) as price_points,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ph.price) as median_price
FROM 
    hotels h
    LEFT JOIN price_history ph ON h.id = ph.hotel_id
WHERE 
    ph.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 
    h.id, h.name, h.city
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_hotel_price_stats_id ON hotel_price_stats(id);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_hotel_price_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hotel_price_stats;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to refresh stats daily
CREATE OR REPLACE FUNCTION create_price_history_partition()
RETURNS trigger AS $$
BEGIN
    CREATE TABLE IF NOT EXISTS price_history_y_EXTRACT(year FROM NEW.date)_m_EXTRACT(month FROM NEW.date)
    PARTITION OF price_history_partitioned
    FOR VALUES FROM (DATE_TRUNC('month', NEW.date))
    TO (DATE_TRUNC('month', NEW.date) + INTERVAL '1 month');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
