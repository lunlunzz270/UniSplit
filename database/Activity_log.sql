USE unisplit;

CREATE TABLE IF NOT EXISTS activity_log (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id    INT UNSIGNED    NOT NULL,
    user_id     INT UNSIGNED    NOT NULL,
    action_type ENUM(
                    'expense_added',
                    'expense_deleted',
                    'settlement_recorded',
                    'member_added',
                    'member_removed',
                    'group_created',
                    'expense_accepted',
                    'expense_appealed',
                    'group_joined',
                    'group_left'
                ) NOT NULL,
    description VARCHAR(255)    NOT NULL,
    ref_id      INT UNSIGNED    DEFAULT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES users(id)    ON DELETE CASCADE,
    INDEX idx_group_id   (group_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;
