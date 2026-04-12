USE unisplit;

CREATE TABLE IF NOT EXISTS sessions (
    id          VARCHAR(255) PRIMARY KEY,
    user_id     INT UNSIGNED    NOT NULL,
    token       VARCHAR(512)    NOT NULL UNIQUE,
    expires_at  DATETIME        NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token     (token),
    INDEX idx_user_id   (user_id),
    INDEX idx_expires   (expires_at)
) ENGINE=InnoDB;
