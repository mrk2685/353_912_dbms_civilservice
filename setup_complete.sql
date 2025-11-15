-- ============================================
-- Civil Service Database - Complete Setup
-- ============================================
-- This file contains everything needed to set up the database:
-- 1. Database creation
-- 2. Tables (DDL)
-- 3. Triggers
-- 4. User management tables
-- 5. Stored procedures
-- 6. Views
-- 7. Sample data (optional)
-- ============================================

-- Create and use database
DROP DATABASE IF EXISTS civilService;
CREATE DATABASE civilService;
USE civilService;

-- ============================================
-- PART 1: CORE TABLES
-- ============================================

-- Aadhar table (Main identity table)
CREATE TABLE aadhar (
    UID BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    DOB DATE NOT NULL,
    mobile CHAR(10) NOT NULL CHECK (mobile REGEXP '^[0-9]{10}$'),
    email VARCHAR(100) UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Biometrics table (Auto-populated by trigger)
CREATE TABLE biometrics (
    UID BIGINT NOT NULL,
    photo MEDIUMBLOB,
    photo_type VARCHAR(10),
    has_photo TINYINT(1) DEFAULT 0,
    created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT NOT NULL DEFAULT 1,
    PRIMARY KEY (UID),
    CONSTRAINT fk_biometrics_aadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- PAN card table
CREATE TABLE PAN (
    panNumber CHAR(10) PRIMARY KEY,
    IssueDate DATE NOT NULL,
    Status VARCHAR(20) NOT NULL,
    UID BIGINT NOT NULL UNIQUE,
    CONSTRAINT fk_pan_aadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Voter ID table
CREATE TABLE votedID (
    EPIC CHAR(10) PRIMARY KEY,
    UID BIGINT NOT NULL,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(300),
    registration_type ENUM('City','Village','Rural','Urban','Other') DEFAULT 'Other',
    IssueDate DATE,
    Status VARCHAR(30) DEFAULT 'Active',
    is_primary TINYINT(1) NOT NULL DEFAULT 0,
    created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_votedid_uid (UID),
    INDEX idx_votedid_status (Status),
    CONSTRAINT fk_votedid_aadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- SIM card table
CREATE TABLE simCard (
    simNo BIGINT PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    UID BIGINT NOT NULL,
    CONSTRAINT fk_sim_aadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Criminal record table
CREATE TABLE criminalRecord (
    CaseNo BIGINT AUTO_INCREMENT PRIMARY KEY,
    offenceType VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Criminal record - Aadhar mapping
CREATE TABLE criminalRecord_Aadhar (
    CaseNo BIGINT NOT NULL,
    UID BIGINT NOT NULL,
    PRIMARY KEY (CaseNo, UID),
    CONSTRAINT fk_criminalCase FOREIGN KEY (CaseNo) REFERENCES criminalRecord(CaseNo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_criminalAadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bank account table
CREATE TABLE bankAccount (
    AccNo BIGINT NOT NULL,
    bankName VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL,
    IFSC CHAR(11) NOT NULL,
    UID BIGINT NOT NULL,
    PRIMARY KEY (AccNo, bankName),
    CONSTRAINT fk_bankaccount_aadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- PART 2: USER MANAGEMENT TABLES
-- ============================================

-- Admin table
CREATE TABLE admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Citizens login table
CREATE TABLE citizens (
    citizen_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    UID BIGINT NOT NULL UNIQUE,
    account_status ENUM('Active', 'Suspended', 'Inactive') DEFAULT 'Active',
    created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    failed_login_attempts INT DEFAULT 0,
    CONSTRAINT fk_citizens_aadhar FOREIGN KEY (UID) REFERENCES aadhar(UID)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Pending registrations table
CREATE TABLE pending_registrations (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    UID BIGINT NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    DOB DATE NOT NULL,
    mobile CHAR(10) NOT NULL CHECK (mobile REGEXP '^[0-9]{10}$'),
    email VARCHAR(100),
    request_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    reviewed_by INT,
    review_date DATETIME,
    rejection_reason VARCHAR(255),
    CONSTRAINT fk_pending_reviewed_by FOREIGN KEY (reviewed_by) REFERENCES admin(admin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Audit log table
CREATE TABLE audit_log (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id VARCHAR(50),
    performed_by VARCHAR(50),
    user_type ENUM('Admin', 'Citizen', 'System'),
    operation_details TEXT,
    ip_address VARCHAR(45),
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user (performed_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- PART 3: TRIGGERS
-- ============================================

-- Trigger 1: Auto-insert biometrics when Aadhar is created
DELIMITER $$

CREATE TRIGGER auto_insert_biometrics
AFTER INSERT ON aadhar
FOR EACH ROW
BEGIN
    -- Insert biometric record with NULL photo initially
    INSERT INTO biometrics (
        UID,
        photo,
        photo_type,
        has_photo,
        created_on,
        last_updated_on,
        version
    ) VALUES (
        NEW.UID,
        NULL,
        NULL,
        FALSE,
        NOW(),
        NOW(),
        1
    );
END$$

DELIMITER ;

-- Trigger 2: Validate DOB on Aadhar insert
DELIMITER $$

CREATE TRIGGER trg_check_dob
BEFORE INSERT ON aadhar
FOR EACH ROW
BEGIN
    -- Check if DOB is in the future
    IF NEW.DOB > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: DOB cannot be in the future.';
    END IF;

    -- Check if DOB is older than 120 years
    IF NEW.DOB < DATE_SUB(CURDATE(), INTERVAL 120 YEAR) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: DOB cannot be older than 120 years.';
    END IF;
END$$

DELIMITER ;

-- Trigger 3: Validate DOB on pending registration
DELIMITER $$

CREATE TRIGGER trg_check_dob_registration
BEFORE INSERT ON pending_registrations
FOR EACH ROW
BEGIN
    -- Check if DOB is in the future
    IF NEW.DOB > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Date of Birth cannot be in the future.';
    END IF;

    -- Check if DOB is older than 120 years
    IF NEW.DOB < DATE_SUB(CURDATE(), INTERVAL 120 YEAR) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Date of Birth cannot be older than 120 years.';
    END IF;
END$$

DELIMITER ;

-- Trigger 4: Validate PAN issue date
DELIMITER $$

CREATE TRIGGER trg_check_issue_date_insert
BEFORE INSERT ON PAN
FOR EACH ROW
BEGIN
    IF NEW.IssueDate > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: IssueDate cannot be in the future.';
    END IF;

    IF NEW.IssueDate < '1995-01-01' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: IssueDate cannot be before 1995-01-01.';
    END IF;
END$$

DELIMITER ;

-- ============================================
-- PART 4: STORED PROCEDURES
-- ============================================

-- Procedure 1: Approve registration
DELIMITER $$

CREATE PROCEDURE approve_registration(
    IN p_request_id INT,
    IN p_admin_id INT
)
BEGIN
    DECLARE v_uid BIGINT;
    DECLARE v_username VARCHAR(50);
    DECLARE v_password_hash VARCHAR(255);
    DECLARE v_name VARCHAR(100);
    DECLARE v_gender CHAR(1);
    DECLARE v_dob DATE;
    DECLARE v_mobile CHAR(10);
    DECLARE v_email VARCHAR(100);
    DECLARE v_status VARCHAR(20);
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error approving registration';
    END;
    
    START TRANSACTION;
    
    -- Get pending registration details
    SELECT UID, username, password_hash, name, gender, DOB, mobile, email, status
    INTO v_uid, v_username, v_password_hash, v_name, v_gender, v_dob, v_mobile, v_email, v_status
    FROM pending_registrations
    WHERE request_id = p_request_id;
    
    -- Check if already processed
    IF v_status != 'Pending' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Registration request already processed';
    END IF;
    
    -- Insert into aadhar (trigger will auto-create biometrics)
    INSERT INTO aadhar (UID, name, gender, DOB, mobile, email)
    VALUES (v_uid, v_name, v_gender, v_dob, v_mobile, v_email);
    
    -- Create citizen account
    INSERT INTO citizens (username, password_hash, UID)
    VALUES (v_username, v_password_hash, v_uid);
    
    -- Update pending registration status
    UPDATE pending_registrations
    SET status = 'Approved',
        reviewed_by = p_admin_id,
        review_date = NOW()
    WHERE request_id = p_request_id;
    
    -- Log the approval
    INSERT INTO audit_log (operation_type, table_name, record_id, performed_by, user_type, operation_details)
    VALUES ('APPROVE_REGISTRATION', 'pending_registrations', p_request_id, 
            (SELECT username FROM admin WHERE admin_id = p_admin_id), 
            'Admin', 
            CONCAT('Approved registration for UID: ', v_uid));
    
    COMMIT;
    
    SELECT 'Registration approved successfully' AS message;
END$$

DELIMITER ;

-- Procedure 2: Reject registration
DELIMITER $$

CREATE PROCEDURE reject_registration(
    IN p_request_id INT,
    IN p_admin_id INT,
    IN p_reason VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error rejecting registration';
    END;
    
    START TRANSACTION;
    
    -- Update pending registration status
    UPDATE pending_registrations
    SET status = 'Rejected',
        reviewed_by = p_admin_id,
        review_date = NOW(),
        rejection_reason = p_reason
    WHERE request_id = p_request_id AND status = 'Pending';
    
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Registration request not found or already processed';
    END IF;
    
    -- Log the rejection
    INSERT INTO audit_log (operation_type, table_name, record_id, performed_by, user_type, operation_details)
    VALUES ('REJECT_REGISTRATION', 'pending_registrations', p_request_id,
            (SELECT username FROM admin WHERE admin_id = p_admin_id),
            'Admin',
            CONCAT('Rejected registration. Reason: ', p_reason));
    
    COMMIT;
    
    SELECT 'Registration rejected successfully' AS message;
END$$

DELIMITER ;

-- Procedure 3: Update citizen profile
DELIMITER $$

CREATE PROCEDURE update_citizen_profile(
    IN p_uid BIGINT,
    IN p_mobile CHAR(10),
    IN p_email VARCHAR(100)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error updating profile';
    END;
    
    START TRANSACTION;
    
    -- Update only allowed fields
    UPDATE aadhar
    SET mobile = p_mobile,
        email = p_email
    WHERE UID = p_uid;
    
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Aadhar record not found';
    END IF;
    
    -- Log the update
    INSERT INTO audit_log (operation_type, table_name, record_id, performed_by, user_type, operation_details)
    VALUES ('UPDATE_PROFILE', 'aadhar', p_uid, p_uid, 'Citizen',
            CONCAT('Updated mobile and email for UID: ', p_uid));
    
    COMMIT;
    
    SELECT 'Profile updated successfully' AS message;
END$$

DELIMITER ;

-- Procedure 4: Get citizen dashboard
DELIMITER $$

CREATE PROCEDURE get_citizen_dashboard(
    IN p_uid BIGINT
)
BEGIN
    -- Get basic aadhar info
    SELECT 
        a.UID,
        a.name,
        a.gender,
        a.DOB,
        TIMESTAMPDIFF(YEAR, a.DOB, CURDATE()) AS age,
        a.mobile,
        a.email,
        c.account_status,
        c.created_on AS account_created,
        c.last_login
    FROM aadhar a
    JOIN citizens c ON a.UID = c.UID
    WHERE a.UID = p_uid;
    
    -- Get linked services count
    SELECT 
        (SELECT COUNT(*) FROM PAN WHERE UID = p_uid) AS pan_count,
        (SELECT COUNT(*) FROM votedID WHERE UID = p_uid) AS voter_id_count,
        (SELECT COUNT(*) FROM simCard WHERE UID = p_uid) AS sim_count,
        (SELECT COUNT(*) FROM bankAccount WHERE UID = p_uid) AS bank_account_count,
        (SELECT COUNT(*) FROM criminalRecord_Aadhar WHERE UID = p_uid) AS criminal_cases;
END$$

DELIMITER ;

-- Procedure 5: Log audit entry
DELIMITER $$

CREATE PROCEDURE log_audit(
    IN p_operation_type VARCHAR(50),
    IN p_table_name VARCHAR(50),
    IN p_record_id VARCHAR(50),
    IN p_performed_by VARCHAR(50),
    IN p_user_type ENUM('Admin', 'Citizen', 'System'),
    IN p_operation_details TEXT
)
BEGIN
    INSERT INTO audit_log (operation_type, table_name, record_id, performed_by, user_type, operation_details)
    VALUES (p_operation_type, p_table_name, p_record_id, p_performed_by, p_user_type, p_operation_details);
END$$

DELIMITER ;

-- ============================================
-- PART 5: FUNCTIONS
-- ============================================

-- Function 1: Get SIM card count for a specific UID
DELIMITER $$

CREATE FUNCTION get_sim_count(user_uid BIGINT) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE sim_count INT;
    SELECT COUNT(*) INTO sim_count
    FROM simCard
    WHERE UID = user_uid;
    RETURN sim_count;
END$$

DELIMITER ;

-- Function 2: Get criminal record count for a specific UID
DELIMITER $$

CREATE FUNCTION get_criminal_record_count(user_uid BIGINT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE crime_count INT;
    SELECT COUNT(*) INTO crime_count
    FROM criminalRecord_Aadhar
    WHERE UID = user_uid;
    RETURN crime_count;
END$$

DELIMITER ;

-- Function 3: Get PAN card count for a specific UID
DELIMITER $$

CREATE FUNCTION get_pan_count(user_uid BIGINT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE pan_count INT;
    SELECT COUNT(*) INTO pan_count
    FROM PAN
    WHERE UID = user_uid;
    RETURN pan_count;
END$$

DELIMITER ;

-- Function 4: Get Voter ID count for a specific UID
DELIMITER $$

CREATE FUNCTION get_voterid_count(user_uid BIGINT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE voterid_count INT;
    SELECT COUNT(*) INTO voterid_count
    FROM votedid
    WHERE UID = user_uid;
    RETURN voterid_count;
END$$

DELIMITER ;

-- Function 5: Get bank account count for a specific UID
DELIMITER $$

CREATE FUNCTION get_bankaccount_count(user_uid BIGINT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE bankaccount_count INT;
    SELECT COUNT(*) INTO bankaccount_count
    FROM bankAccount
    WHERE UID = user_uid;
    RETURN bankaccount_count;
END$$

DELIMITER ;

-- ============================================
-- PART 6: VIEWS
-- ============================================

-- View: Pending registrations summary
CREATE OR REPLACE VIEW pending_registrations_summary AS
SELECT 
    request_id,
    username,
    UID,
    name,
    gender,
    DOB,
    mobile,
    email,
    request_date,
    status,
    DATEDIFF(CURDATE(), request_date) AS days_pending
FROM pending_registrations
WHERE status = 'Pending'
ORDER BY request_date ASC;

-- View: Recent audit log
CREATE OR REPLACE VIEW recent_audit_log AS
SELECT 
    log_id,
    operation_type,
    table_name,
    record_id,
    performed_by,
    user_type,
    operation_details,
    timestamp
FROM audit_log
ORDER BY timestamp DESC
LIMIT 100;

-- ============================================
-- PART 7: DEFAULT DATA
-- ============================================

-- Insert default admin accounts
-- Password: admin123 (hashed with SHA-256)
INSERT INTO admin (username, password_hash, full_name) VALUES
('admin', SHA2('admin123', 256), 'System Administrator'),
('superadmin', SHA2('super123', 256), 'Super Administrator');

-- ============================================
-- PART 8: SAMPLE DATA (Optional)
-- ============================================

-- Insert sample Aadhar records (Biometrics will be auto-generated by trigger)
INSERT INTO aadhar (UID, name, gender, DOB, mobile, email) VALUES
(100000000001, 'Pranav Shenvi', 'M', '2000-10-09', '9876543210', 'pranav.shenvi@example.com'),
(100000000002, 'Ananya Iyer', 'F', '1995-03-15', '9123456789', 'ananya.iyer@example.com'),
(100000000003, 'Rohan Mehta', 'M', '1988-07-22', '9988776655', 'rohan.mehta@example.com'),
(100000000004, 'Sanya Kapoor', 'F', '2002-12-01', '9012345678', 'sanya.kapoor@example.com'),
(100000000005, 'Vikram Singh', 'M', '1990-05-18', '9876501234', 'vikram.singh@example.com'),
(100000000006, 'Meera Joshi', 'F', '1998-11-30', '9123098765', 'meera.joshi@example.com'),
(100000000007, 'Aditya Nair', 'M', '1985-08-12', '9900112233', 'aditya.nair@example.com'),
(100000000008, 'Isha Reddy', 'F', '2001-06-05', '9876012345', 'isha.reddy@example.com'),
(100000000009, 'Karan Verma', 'M', '1992-09-25', '9011223344', 'karan.verma@example.com'),
(100000000010, 'Priya Sharma', 'F', '1999-04-17', '9988123456', 'priya.sharma@example.com');

-- Insert sample PAN records
INSERT INTO PAN (panNumber, IssueDate, Status, UID) VALUES
('ABCDE1234F', '2018-05-20', 'Active', 100000000001),
('FGHIJ5678K', '2017-11-15', 'Active', 100000000002),
('KLMNO9012P', '2019-01-10', 'Inactive', 100000000003);

-- Insert sample Voter IDs
INSERT INTO votedID (EPIC, name, address, UID) VALUES
('VOTER001', 'Pranav Shenvi', 'City: Mumbai, Maharashtra', 100000000001),
('VOTER002', 'Pranav Shenvi', 'Village: Panvel, Maharashtra', 100000000001),
('VOTER003', 'Ananya Iyer', 'City: Bangalore, Karnataka', 100000000002),
('VOTER004', 'Rohan Mehta', 'City: Pune, Maharashtra', 100000000003),
('VOTER005', 'Rohan Mehta', 'Village: Baramati, Maharashtra', 100000000003),
('VOTER006', 'Sanya Kapoor', 'City: Delhi', 100000000004);

-- Insert sample SIM cards
INSERT INTO simCard (simNo, provider, status, UID) VALUES
(9876543210, 'Airtel', 'Active', 100000000001),
(9123456789, 'Jio', 'Active', 100000000001),
(9988776655, 'Vodafone', 'Inactive', 100000000002),
(9012345670, 'Airtel', 'Active', 100000000003),
(9012345671, 'Jio', 'Inactive', 100000000003);

-- Insert sample criminal records
INSERT INTO criminalRecord (CaseNo, offenceType) VALUES
(2001, 'Theft'),
(2002, 'Fraud'),
(2003, 'Assault');

INSERT INTO criminalRecord_Aadhar (CaseNo, UID) VALUES
(2001, 100000000001),
(2001, 100000000002),
(2002, 100000000003);

-- Insert sample bank accounts
INSERT INTO bankAccount (AccNo, bankName, type, IFSC, UID) VALUES
(1002003001, 'HDFC', 'Savings', 'HDFC0001234', 100000000001),
(1002003002, 'SBI', 'Current', 'SBIN0005678', 100000000001),
(1002003003, 'ICICI', 'Savings', 'ICIC0002345', 100000000002),
(1002003004, 'HDFC', 'Current', 'HDFC0003456', 100000000003);

-- Create citizen login accounts for sample data
-- Password for all: 'password123'
INSERT INTO citizens (username, password_hash, UID, account_status) VALUES
('pranav.shenvi', SHA2('password123', 256), 100000000001, 'Active'),
('ananya.iyer', SHA2('password123', 256), 100000000002, 'Active'),
('rohan.mehta', SHA2('password123', 256), 100000000003, 'Active'),
('sanya.kapoor', SHA2('password123', 256), 100000000004, 'Active'),
('vikram.singh', SHA2('password123', 256), 100000000005, 'Active'),
('meera.joshi', SHA2('password123', 256), 100000000006, 'Active'),
('aditya.nair', SHA2('password123', 256), 100000000007, 'Active'),
('isha.reddy', SHA2('password123', 256), 100000000008, 'Active'),
('karan.verma', SHA2('password123', 256), 100000000009, 'Active'),
('priya.sharma', SHA2('password123', 256), 100000000010, 'Active');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Show all tables
SHOW TABLES;

-- Show triggers
SHOW TRIGGERS;

-- Show procedures
SHOW PROCEDURE STATUS WHERE Db = 'civilService';

-- Show functions
SHOW FUNCTION STATUS WHERE Db = 'civilService';

-- Show views
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = 'civilService';

-- Verify sample data counts
SELECT 
    'Aadhar Records' AS Table_Name, COUNT(*) AS Count FROM aadhar
UNION ALL
SELECT 'Biometrics Records', COUNT(*) FROM biometrics
UNION ALL
SELECT 'PAN Records', COUNT(*) FROM PAN
UNION ALL
SELECT 'Voter IDs', COUNT(*) FROM votedID
UNION ALL
SELECT 'SIM Cards', COUNT(*) FROM simCard
UNION ALL
SELECT 'Bank Accounts', COUNT(*) FROM bankAccount
UNION ALL
SELECT 'Criminal Records', COUNT(*) FROM criminalRecord
UNION ALL
SELECT 'Citizens', COUNT(*) FROM citizens
UNION ALL
SELECT 'Admins', COUNT(*) FROM admin;

-- Test functions (optional)
SELECT 
    'Functions Test' AS Test_Type,
    get_sim_count(100000000001) AS SIM_Count,
    get_pan_count(100000000001) AS PAN_Count,
    get_voterid_count(100000000001) AS VoterID_Count,
    get_bankaccount_count(100000000001) AS BankAccount_Count,
    get_criminal_record_count(100000000001) AS Criminal_Count;

-- ============================================
-- SETUP COMPLETE!
-- ============================================
-- Database Objects Created:
--   - 12 Tables
--   - 4 Triggers
--   - 5 Stored Procedures
--   - 5 Functions
--   - 2 Views
--   - 10 Sample Citizens with Services
--   - 2 Admin Accounts
--
-- You can now run the GUI application:
--   python civil_service_gui_enhanced.py
--
-- Default Credentials:
--   Admin Login: admin / admin123
--   Citizen Login: pranav.shenvi / password123
-- ============================================
