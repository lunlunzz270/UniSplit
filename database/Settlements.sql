USE unisplit;

CREATE TABLE IF NOT EXISTS settlements (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    group_id    INT UNSIGNED    NOT NULL,
    payer_id    INT UNSIGNED    NOT NULL,
    payee_id    INT UNSIGNED    NOT NULL,
    amount      DECIMAL(10, 2)  NOT NULL,
    note        VARCHAR(255)    DEFAULT NULL,
    settled_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (payer_id) REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (payee_id) REFERENCES users(id)    ON DELETE CASCADE,
    INDEX idx_group_id   (group_id),
    INDEX idx_payer_id   (payer_id),
    INDEX idx_payee_id   (payee_id),
    INDEX idx_settled_at (settled_at)
) ENGINE=InnoDB;
