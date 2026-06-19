-- Initialize Loan Approval System Database

-- Create applicants table
CREATE TABLE IF NOT EXISTS applicants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id VARCHAR(50) UNIQUE NOT NULL,
    age INT,
    income DECIMAL(12,2),
    employment_type VARCHAR(50),
    credit_score INT,
    loan_amount DECIMAL(12,2),
    loan_tenure INT,
    existing_liabilities DECIMAL(12,2),
    location VARCHAR(100),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_created_at (created_at)
);

-- Create decisions table
CREATE TABLE IF NOT EXISTS decisions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id VARCHAR(50) NOT NULL,
    classification VARCHAR(50),
    risk_score INT,
    confidence_level INT,
    decision_factors JSON,
    explanation TEXT,
    case_id VARCHAR(100),
    notification_sent BOOLEAN DEFAULT FALSE,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id),
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_case_id (case_id),
    INDEX idx_created_at (created_at),
    UNIQUE KEY unique_case_id (case_id)
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id VARCHAR(50),
    action VARCHAR(100),
    agent_name VARCHAR(100),
    details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_agent_name (agent_name),
    INDEX idx_created_at (created_at)
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id VARCHAR(50) NOT NULL,
    notification_type VARCHAR(50),
    channel VARCHAR(50),
    message TEXT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'sent',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (applicant_id) REFERENCES applicants(applicant_id),
    INDEX idx_applicant_id (applicant_id),
    INDEX idx_sent_at (sent_at),
    INDEX idx_status (status)
);

-- Insert sample data if not exists
INSERT IGNORE INTO applicants (applicant_id, age, income, employment_type, credit_score, loan_amount, loan_tenure, existing_liabilities, location)
VALUES
    ('APP001', 32, 85000, 'Salaried', 720, 500000, 60, 15000, 'Mumbai'),
    ('APP002', 28, 45000, 'Self-Employed', 580, 300000, 36, 25000, 'Ahmedabad'),
    ('APP003', 45, 150000, 'Salaried', 810, 750000, 84, 5000, 'Bangalore');
