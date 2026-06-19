-- ============================================================
-- Loan Approval System - MySQL Schema & Seed Data
-- ============================================================
-- Run this once:  mysql -u root -p < database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS loan_approval_db;
USE loan_approval_db;

-- TABLE: applicants
CREATE TABLE IF NOT EXISTS applicants (
    applicant_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT,
    income DECIMAL(12,2),
    employment_type VARCHAR(30),
    employer VARCHAR(100) DEFAULT NULL,
    business_type VARCHAR(50) DEFAULT NULL,
    years_employed INT DEFAULT NULL,
    years_in_business INT DEFAULT NULL,
    location VARCHAR(50),
    existing_accounts INT DEFAULT 0,
    previous_loans_cleared INT DEFAULT 0
);

-- TABLE: credit_history
CREATE TABLE IF NOT EXISTS credit_history (
    applicant_id VARCHAR(20) PRIMARY KEY,
    credit_score INT,
    total_credit_lines INT,
    defaults_count INT DEFAULT 0,
    late_payments INT DEFAULT 0,
    oldest_account_years INT,
    credit_utilization DECIMAL(5,2),
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id)
);

-- TABLE: decision_log
CREATE TABLE IF NOT EXISTS decision_log (
    decision_id VARCHAR(50) PRIMARY KEY,
    applicant_id VARCHAR(20),
    classification VARCHAR(20),
    risk_score DECIMAL(5,2),
    confidence DECIMAL(5,2),
    key_factors TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: notification_log
CREATE TABLE IF NOT EXISTS notification_log (
    notification_id VARCHAR(50) PRIMARY KEY,
    applicant_id VARCHAR(20),
    notification_type VARCHAR(30),
    message TEXT,
    channel VARCHAR(10) DEFAULT 'email',
    status VARCHAR(10) DEFAULT 'SENT',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: case_registry
CREATE TABLE IF NOT EXISTS case_registry (
    case_id VARCHAR(50) PRIMARY KEY,
    applicant_id VARCHAR(20),
    classification VARCHAR(20),
    summary TEXT,
    priority VARCHAR(10) DEFAULT 'NORMAL',
    status VARCHAR(10) DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SEED DATA (mirrors mock data exactly)
-- ============================================================

INSERT IGNORE INTO applicants VALUES
('APP001', 'Rahul Sharma', 32, 85000.00, 'Salaried', 'TCS', NULL, 5, NULL, 'Mumbai', 3, 2),
('APP002', 'Priya Patel', 28, 45000.00, 'Self-Employed', NULL, 'Retail', NULL, 3, 'Ahmedabad', 2, 1),
('APP003', 'Vikram Singh', 45, 150000.00, 'Salaried', 'Infosys', NULL, 15, NULL, 'Bangalore', 5, 4);

INSERT IGNORE INTO credit_history VALUES
('APP001', 720, 3, 0, 1, 8, 35.00),
('APP002', 580, 2, 1, 4, 3, 78.00),
('APP003', 810, 5, 0, 0, 18, 15.00);

-- Verify
SELECT 'Applicants seeded:' AS info, COUNT(*) AS count FROM applicants;
SELECT 'Credit history seeded:' AS info, COUNT(*) AS count FROM credit_history;