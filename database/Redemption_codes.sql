USE unisplit;

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
