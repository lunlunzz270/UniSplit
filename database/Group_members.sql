USE unisplit;

CREATE TABLE IF NOT EXISTS group_members (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    group_id    INT UNSIGNED            NOT NULL,
    user_id     INT UNSIGNED            NOT NULL,
    role        ENUM('admin','member')  NOT NULL DEFAULT 'member',
    joined_at   DATETIME                NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_group_user (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES users(id)    ON DELETE CASCADE,
    INDEX idx_group_id (group_id),
    INDEX idx_user_id  (user_id)
) ENGINE=InnoDB;
