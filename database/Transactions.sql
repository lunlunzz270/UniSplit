USE unisplit;

CREATE TABLE IF NOT EXISTS transactions (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED    NOT NULL,
    type        VARCHAR(50)     NOT NULL, -- 'recharge' or 'membership'
    amount      DECIMAL(10, 2)  NOT NULL DEFAULT 0.00,
    description VARCHAR(255)    DEFAULT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_transaction_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
