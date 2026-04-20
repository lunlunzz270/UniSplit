USE unisplit;

CREATE TABLE IF NOT EXISTS reminders (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
    group_id     INT UNSIGNED NOT NULL, 
    sender_id    INT UNSIGNED NOT NULL, 
    recipient_id INT UNSIGNED NOT NULL, 
    expense_id   INT UNSIGNED DEFAULT NULL,
    message      TEXT NOT NULL, 
    is_read      TINYINT(1) DEFAULT 0, 
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP, 
    
    FOREIGN KEY (group_id)     REFERENCES `groups`(id) ON DELETE CASCADE, 
    FOREIGN KEY (sender_id)    REFERENCES users(id)    ON DELETE CASCADE, 
    FOREIGN KEY (recipient_id) REFERENCES users(id)    ON DELETE CASCADE,
    FOREIGN KEY (expense_id)   REFERENCES expenses(id) ON DELETE SET NULL,
    INDEX idx_recipient (recipient_id),
    INDEX idx_group (group_id)
) ENGINE=InnoDB;
