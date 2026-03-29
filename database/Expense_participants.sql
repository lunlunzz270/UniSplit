USE unisplit;

CREATE TABLE IF NOT EXISTS expense_participants (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    expense_id  INT UNSIGNED    NOT NULL,
    user_id     INT UNSIGNED    NOT NULL,
    share       DECIMAL(10, 2)  NOT NULL,
    is_settled  TINYINT(1)      NOT NULL DEFAULT 0,

    UNIQUE KEY uq_expense_user (expense_id, user_id),
    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
    INDEX idx_expense_id (expense_id),
    INDEX idx_user_id    (user_id)
) ENGINE=InnoDB;
