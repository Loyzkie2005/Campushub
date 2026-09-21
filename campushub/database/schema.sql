-- =====================================================================
-- CampusHub - Login / Signup Schema
-- Run this script inside the "CampusHub" database in pgAdmin
-- =====================================================================

-- Required for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================
-- ROLE
-- =====================================================================
CREATE TABLE IF NOT EXISTS role (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name   VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =====================================================================
-- CAMPUSHUB_LOGIN  (login + signup data)
-- =====================================================================
CREATE TABLE IF NOT EXISTS campushub_login (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    role_id       UUID REFERENCES role(id) ON DELETE SET NULL,
    is_active     BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campushub_login_username ON campushub_login(username);
CREATE INDEX IF NOT EXISTS idx_campushub_login_email    ON campushub_login(email);

-- =====================================================================
-- updated_at auto-update trigger
-- =====================================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_campushub_login_updated_at ON campushub_login;
CREATE TRIGGER trg_campushub_login_updated_at
BEFORE UPDATE ON campushub_login
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =====================================================================
-- Seed default roles
-- =====================================================================
INSERT INTO role (role_name, description) VALUES
    ('Super Admin',    'Full system access and configuration'),
    ('Facility Admin', 'Manages facility schedules, reservations, and payment verification'),
    ('Seller',         'Manages marketplace products and orders'),
    ('Faculty',        'Reserves facilities for academic purposes'),
    ('Student',        'Student access to facilities and marketplace')
ON CONFLICT (role_name) DO NOTHING;
