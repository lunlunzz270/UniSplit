USE unisplit;

CREATE TABLE IF NOT EXISTS expenses (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id    INT UNSIGNED        NOT NULL,
    description VARCHAR(255)        NOT NULL,
    amount      DECIMAL(10, 2)      NOT NULL,
    paid_by     INT UNSIGNED        NOT NULL,
    category    ENUM(
                    'food_dining',
                    'transportation',
                    'entertainment',
                    'groceries',
                    'other'
                ) NOT NULL DEFAULT 'other',
    created_at  DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (paid_by)  REFERENCES users(id)    ON DELETE CASCADE,
    INDEX idx_group_id   (group_id),
    INDEX idx_paid_by    (paid_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;
