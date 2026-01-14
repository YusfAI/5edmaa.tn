-- ========================================
-- 5EDMA.TN UML TABLES - COMPLETE
-- ========================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('worker', 'client', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. WORKER_PROFILES TABLE
CREATE TABLE IF NOT EXISTS worker_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    bio TEXT,
    categories TEXT[],
    hourly_rate DECIMAL(10,2),
    location VARCHAR(100),
    availability JSONB,
    portfolio_urls TEXT[],
    verified BOOLEAN DEFAULT FALSE,
    premium_until TIMESTAMP WITH TIME ZONE,
    rating DECIMAL(3,2)
);

-- 3. CLIENT_PROFILES TABLE
CREATE TABLE IF NOT EXISTS client_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    company_name VARCHAR(255),
    location VARCHAR(100)
);

-- Optional indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
