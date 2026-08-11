-- 5edma.tn — MySQL schema
-- Matches the SQLAlchemy models in backend/app/*.py exactly.
-- Safe to import directly: `mysql -u <user> -p <database> < schema.sql`
-- (this also doubles as the Alembic baseline in migrations/versions/0001_initial_schema.py)

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- Core identity
-- ============================================================

CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    phone           VARCHAR(20)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            ENUM('worker', 'client', 'admin') NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE worker_profiles (
    user_id          INT PRIMARY KEY,
    bio              TEXT NULL,
    categories       JSON NULL,
    hourly_rate      DECIMAL(10,2) NULL,
    location         VARCHAR(100) NULL,
    availability     JSON NULL,
    portfolio_urls   JSON NULL,
    verified         BOOLEAN NOT NULL DEFAULT FALSE,
    status           ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    rejection_reason TEXT NULL,
    premium_until    DATETIME NULL,
    rating           DECIMAL(3,2) NULL,
    CONSTRAINT fk_worker_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE client_profiles (
    user_id          INT PRIMARY KEY,
    company_name     VARCHAR(255) NULL,
    location         VARCHAR(100) NULL,
    full_name        VARCHAR(255) NULL,
    bio              TEXT NULL,
    verified         BOOLEAN NOT NULL DEFAULT FALSE,
    status           ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    rejection_reason TEXT NULL,
    CONSTRAINT fk_client_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Flow 1: Jobs & Applications (client posts a job, workers apply)
-- ============================================================

CREATE TABLE job_offers (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    client_id    INT NOT NULL,
    title        VARCHAR(255) NOT NULL,
    description  TEXT NOT NULL,
    category     VARCHAR(100) NOT NULL,
    location     VARCHAR(100) NOT NULL,
    budget_min   DECIMAL(10,2) NULL,
    budget_max   DECIMAL(10,2) NULL,
    status       ENUM('open', 'closed') NOT NULL DEFAULT 'open',
    boost_until  DATETIME NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_job_offers_client_id (client_id),
    INDEX ix_job_offers_category (category),
    INDEX ix_job_offers_location (location),
    CONSTRAINT fk_job_offers_client FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE job_applications (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    job_id         INT NOT NULL,
    worker_id      INT NOT NULL,
    cover_message  TEXT NULL,
    status         ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_job_applications_job_id (job_id),
    INDEX ix_job_applications_worker_id (worker_id),
    CONSTRAINT fk_job_applications_job FOREIGN KEY (job_id) REFERENCES job_offers(id) ON DELETE CASCADE,
    CONSTRAINT fk_job_applications_worker FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Flow 2: Services & Bookings (worker lists a fixed service, client books it)
-- ============================================================

CREATE TABLE services (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    provider_id  INT NOT NULL,
    title        VARCHAR(255) NOT NULL,
    description  TEXT NOT NULL,
    category     VARCHAR(100) NOT NULL,
    location     VARCHAR(100) NOT NULL,
    base_price   DECIMAL(10,2) NULL,
    is_premium   BOOLEAN NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_services_provider_id (provider_id),
    INDEX ix_services_category (category),
    INDEX ix_services_location (location),
    CONSTRAINT fk_services_provider FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bookings (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    service_id     INT NOT NULL,
    customer_id    INT NOT NULL,
    provider_id    INT NOT NULL,
    scheduled_for  DATETIME NOT NULL,
    status         ENUM('pending', 'confirmed', 'cancelled', 'completed') NOT NULL DEFAULT 'pending',
    note           VARCHAR(500) NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_bookings_service_id (service_id),
    INDEX ix_bookings_customer_id (customer_id),
    INDEX ix_bookings_provider_id (provider_id),
    CONSTRAINT fk_bookings_service FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    CONSTRAINT fk_bookings_customer FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_bookings_provider FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Reviews (cover both flows above)
-- ============================================================

CREATE TABLE reviews (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    booking_id          INT NULL,
    job_application_id  INT NULL,
    reviewer_id         INT NOT NULL,
    reviewee_id         INT NOT NULL,
    rating              SMALLINT NOT NULL,
    comment             TEXT NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_reviews_booking_id (booking_id),
    INDEX ix_reviews_job_application_id (job_application_id),
    INDEX ix_reviews_reviewer_id (reviewer_id),
    INDEX ix_reviews_reviewee_id (reviewee_id),
    CONSTRAINT fk_reviews_booking FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_application FOREIGN KEY (job_application_id) REFERENCES job_applications(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_reviewee FOREIGN KEY (reviewee_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Wallet & payments
-- ============================================================

CREATE TABLE wallets (
    user_id      INT PRIMARY KEY,
    balance      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency     VARCHAR(3) NOT NULL DEFAULT 'TND',
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_wallets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE transactions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    type         ENUM('topup', 'payment', 'withdrawal', 'refund', 'fee', 'release') NOT NULL,
    amount       DECIMAL(10,2) NOT NULL,
    status       ENUM('pending', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
    reference    VARCHAR(255) NULL,
    description  VARCHAR(255) NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_transactions_user_id (user_id),
    CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Messaging
-- ============================================================

CREATE TABLE messages (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    job_id        INT NOT NULL,
    sender_id     INT NOT NULL,
    receiver_id   INT NOT NULL,
    content       TEXT NOT NULL,
    attachments   JSON NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at       DATETIME NULL,
    INDEX ix_messages_job_id (job_id),
    INDEX ix_messages_sender_id (sender_id),
    INDEX ix_messages_receiver_id (receiver_id),
    CONSTRAINT fk_messages_job FOREIGN KEY (job_id) REFERENCES job_offers(id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_receiver FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Subscriptions & boosts
-- ============================================================

CREATE TABLE subscription_plans (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    description    VARCHAR(255) NULL,
    price          DECIMAL(10,2) NOT NULL,
    duration_days  INT NOT NULL,
    features       JSON NULL,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE user_subscriptions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    plan_id      INT NOT NULL,
    start_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date     DATETIME NOT NULL,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    INDEX ix_user_subscriptions_user_id (user_id),
    INDEX ix_user_subscriptions_plan_id (plan_id),
    CONSTRAINT fk_user_subscriptions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_subscriptions_plan FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE job_boosts (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    job_id       INT NOT NULL,
    boost_type   VARCHAR(50) NOT NULL,
    start_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date     DATETIME NOT NULL,
    price_paid   DECIMAL(10,2) NOT NULL,
    INDEX ix_job_boosts_job_id (job_id),
    CONSTRAINT fk_job_boosts_job FOREIGN KEY (job_id) REFERENCES job_offers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- Subscription plan data is seeded by backend/scripts/seed_plans.py (idempotent,
-- upserts by name) — run it after importing this schema, not maintained here.
