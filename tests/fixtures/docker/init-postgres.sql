-- Initialize test database schema and sample data for QueryHub integration tests

-- Create sales metrics table
CREATE TABLE IF NOT EXISTS sales_metrics (
    id SERIAL PRIMARY KEY,
    region VARCHAR(50) NOT NULL,
    product VARCHAR(100) NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL,
    units_sold INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create customer feedback table
CREATE TABLE IF NOT EXISTS customer_feedback (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    product VARCHAR(100) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    feedback_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system health metrics table
CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_count INTEGER DEFAULT 0,
    check_timestamp TIMESTAMP NOT NULL
);

-- Insert sample sales data
INSERT INTO sales_metrics (region, product, revenue, units_sold, sale_date) VALUES
    ('North America', 'Widget Pro', 15000.00, 150, '2025-11-01'),
    ('North America', 'Widget Lite', 8500.00, 300, '2025-11-01'),
    ('Europe', 'Widget Pro', 12000.00, 120, '2025-11-01'),
    ('Europe', 'Widget Lite', 6800.00, 250, '2025-11-01'),
    ('Asia Pacific', 'Widget Pro', 18500.00, 185, '2025-11-02'),
    ('Asia Pacific', 'Widget Lite', 9200.00, 320, '2025-11-02'),
    ('North America', 'Widget Pro', 16200.00, 162, '2025-11-03'),
    ('Europe', 'Widget Pro', 11500.00, 115, '2025-11-03'),
    ('Asia Pacific', 'Widget Pro', 19800.00, 198, '2025-11-04'),
    ('North America', 'Widget Lite', 9100.00, 310, '2025-11-04');

-- Insert sample customer feedback
INSERT INTO customer_feedback (customer_name, product, rating, comment, feedback_date) VALUES
    ('Alice Johnson', 'Widget Pro', 5, 'Excellent product! Exceeded expectations.', '2025-11-01'),
    ('Bob Smith', 'Widget Lite', 4, 'Good value for money, works well.', '2025-11-01'),
    ('Carol White', 'Widget Pro', 5, 'Best purchase this year!', '2025-11-02'),
    ('David Brown', 'Widget Lite', 3, 'Decent but could be better.', '2025-11-02'),
    ('Eve Davis', 'Widget Pro', 4, 'Very satisfied with performance.', '2025-11-03'),
    ('Frank Wilson', 'Widget Lite', 5, 'Simple and effective!', '2025-11-03'),
    ('Grace Lee', 'Widget Pro', 5, 'Highly recommend to everyone.', '2025-11-04'),
    ('Henry Martinez', 'Widget Lite', 4, 'Good product overall.', '2025-11-04');

-- Insert system health metrics
INSERT INTO system_health (service_name, status, response_time_ms, error_count, check_timestamp) VALUES
    ('API Gateway', 'healthy', 45, 0, '2025-11-14 10:00:00'),
    ('Database', 'healthy', 12, 0, '2025-11-14 10:00:00'),
    ('Cache Service', 'healthy', 8, 0, '2025-11-14 10:00:00'),
    ('Email Service', 'degraded', 320, 2, '2025-11-14 10:00:00'),
    ('Analytics Service', 'healthy', 156, 0, '2025-11-14 10:00:00');

-- Create indexes for better query performance
CREATE INDEX idx_sales_region ON sales_metrics(region);
CREATE INDEX idx_sales_date ON sales_metrics(sale_date);
CREATE INDEX idx_feedback_product ON customer_feedback(product);
CREATE INDEX idx_feedback_date ON customer_feedback(feedback_date);
CREATE INDEX idx_health_service ON system_health(service_name);
CREATE INDEX idx_health_timestamp ON system_health(check_timestamp);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO testuser;
