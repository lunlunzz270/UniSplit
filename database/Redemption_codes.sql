USE unisplit;

-- 1. Create the table structure
CREATE TABLE IF NOT EXISTS redemption_codes (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(50)     NOT NULL UNIQUE,
    category    ENUM('CASH', 'VIP') NOT NULL,
    value       DECIMAL(10, 2)  NOT NULL, -- Amount for CASH, Days for VIP
    is_used     TINYINT(1)      NOT NULL DEFAULT 0,
    used_by_id  INT UNSIGNED    DEFAULT NULL,
    used_at     DATETIME        DEFAULT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (used_by_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_code (code)
) ENGINE=InnoDB;

-- 2. Seed Data: Professional Code Pool
-- Note: Using IGNORE to prevent errors if running multiple times

-- 10 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-10-A7B2', 'CASH', 10.00), ('UNISPLIT-10-K9L4', 'CASH', 10.00), ('UNISPLIT-10-P1Q8', 'CASH', 10.00), ('UNISPLIT-10-X5Y0', 'CASH', 10.00), ('UNISPLIT-10-M3N6', 'CASH', 10.00);

-- 20 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-20-C8D3', 'CASH', 20.00), ('UNISPLIT-20-J2K1', 'CASH', 20.00), ('UNISPLIT-20-R9S4', 'CASH', 20.00), ('UNISPLIT-20-T5U7', 'CASH', 20.00), ('UNISPLIT-20-V1W9', 'CASH', 20.00);

-- 50 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-50-E4F9', 'CASH', 50.00), ('UNISPLIT-50-G1H2', 'CASH', 50.00), ('UNISPLIT-50-L8M3', 'CASH', 50.00), ('UNISPLIT-50-N5P0', 'CASH', 50.00), ('UNISPLIT-50-Z7X2', 'CASH', 50.00);

-- 100 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-100-Q3W1', 'CASH', 100.00), ('UNISPLIT-100-E5R7', 'CASH', 100.00), ('UNISPLIT-100-T9Y2', 'CASH', 100.00), ('UNISPLIT-100-U4I8', 'CASH', 100.00), ('UNISPLIT-100-O0P6', 'CASH', 100.00);

-- 200 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-200-A1S2', 'CASH', 200.00), ('UNISPLIT-200-D3F4', 'CASH', 200.00), ('UNISPLIT-200-G5H6', 'CASH', 200.00), ('UNISPLIT-200-J7K8', 'CASH', 200.00), ('UNISPLIT-200-L9Z0', 'CASH', 200.00);

-- 500 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-500-X1C2', 'CASH', 500.00), ('UNISPLIT-500-V3B4', 'CASH', 500.00), ('UNISPLIT-500-N5M6', 'CASH', 500.00), ('UNISPLIT-500-Q7W8', 'CASH', 500.00), ('UNISPLIT-500-E9R0', 'CASH', 500.00);

-- 1000 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-1000-GOLD1', 'CASH', 1000.00), ('UNISPLIT-1000-GOLD2', 'CASH', 1000.00), ('UNISPLIT-1000-GOLD3', 'CASH', 1000.00), ('UNISPLIT-1000-GOLD4', 'CASH', 1000.00), ('UNISPLIT-1000-GOLD5', 'CASH', 1000.00);

-- 5000 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-5000-PLAT1', 'CASH', 5000.00), ('UNISPLIT-5000-PLAT2', 'CASH', 5000.00), ('UNISPLIT-5000-PLAT3', 'CASH', 5000.00), ('UNISPLIT-5000-PLAT4', 'CASH', 5000.00), ('UNISPLIT-5000-PLAT5', 'CASH', 5000.00);

-- 10000 USD Codes
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('UNISPLIT-10000-DIAM1', 'CASH', 10000.00), ('UNISPLIT-10000-DIAM2', 'CASH', 10000.00), ('UNISPLIT-10000-DIAM3', 'CASH', 10000.00), ('UNISPLIT-10000-DIAM4', 'CASH', 10000.00), ('UNISPLIT-10000-DIAM5', 'CASH', 10000.00);

-- VIP Codes (30 days & 365 days)
INSERT IGNORE INTO redemption_codes (code, category, value) VALUES 
('VIP-MONTH-FREE', 'VIP', 30), ('VIP-MONTH-GIFT', 'VIP', 30),
('VIP-YEAR-PRO', 'VIP', 365), ('VIP-YEAR-BETA', 'VIP', 365);
