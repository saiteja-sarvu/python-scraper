-- Password reset tokens issued via /forgot-password (routers/auth_router.py)
-- and consumed via /reset-password. Referenced by model/user_model.py:
-- create_password_reset_token, get_password_reset_token, mark_password_reset_token_used.

CREATE TABLE IF NOT EXISTS `ai_password_reset_tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `token_hash` varchar(64) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_token_hash` (`token_hash`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
