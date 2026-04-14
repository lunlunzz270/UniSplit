USE unisplit;

CREATE TABLE IF NOT EXISTS users (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100)    NOT NULL,
    email       VARCHAR(255)    NOT NULL UNIQUE,
    password    VARCHAR(255)    NOT NULL,
    balance     DECIMAL(10, 2)  NOT NULL DEFAULT 0.00,
    is_admin    TINYINT(1)      NOT NULL DEFAULT 0,
    is_vip      TINYINT(1)      NOT NULL DEFAULT 0,
    vip_expiry  DATETIME        DEFAULT NULL,
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_email (email)
) ENGINE=InnoDB;
