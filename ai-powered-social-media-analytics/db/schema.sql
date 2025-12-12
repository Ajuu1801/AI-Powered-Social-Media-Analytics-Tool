create DATABASE IF NOT EXISTS social_media_analytics;
USE social_media_analytics;
-- Users table
CREATE TABLE IF NOT EXISTS users (
	id INT AUTO_INCREMENT PRIMARY KEY,
	username VARCHAR(50) NOT NULL UNIQUE,
	email VARCHAR(100) NOT NULL UNIQUE,
	password_hash VARCHAR(255) NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Social Accounts table
CREATE TABLE IF NOT EXISTS social_accounts (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user_id INT NOT NULL,
	platform ENUM('instagram', 'twitter', 'youtube') NOT NULL,
	account_name VARCHAR(100) NOT NULL,
	access_token VARCHAR(255),
	connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user_id INT NOT NULL,
	account_id INT NOT NULL,
	content TEXT NOT NULL,
	post_date DATETIME NOT NULL,
	likes INT DEFAULT 0,
	comments INT DEFAULT 0,
	shares INT DEFAULT 0,
	impressions INT DEFAULT 0,
	followers_gained INT DEFAULT 0,
	followers_lost INT DEFAULT 0,
	sentiment VARCHAR(20),
	ai_score FLOAT,
	keywords VARCHAR(255),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	FOREIGN KEY (account_id) REFERENCES social_accounts(id) ON DELETE CASCADE
);

-- Analytics Cache table
CREATE TABLE IF NOT EXISTS analytics_cache (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user_id INT NOT NULL,
	account_id INT NOT NULL,
	week_start DATE NOT NULL,
	summary TEXT,
	ai_insights TEXT,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	FOREIGN KEY (account_id) REFERENCES social_accounts(id) ON DELETE CASCADE
);
