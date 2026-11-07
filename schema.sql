DROP TABLE IF EXISTS share_links;
DROP TABLE IF EXISTS history;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS login_attempts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files are stored encrypted on disk under `filename` (a random UUID).
-- `wrapped_key` is the per-file AES key, itself encrypted with the master key.
-- `delete_date` is NULL for live files and set when the file is moved to the trash.
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    wrapped_key BLOB NOT NULL,
    upload_date TEXT NOT NULL,
    delete_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX idx_files_user ON files (user_id, delete_date);

CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_id INTEGER,
    -- copied at write time so the log stays readable after a permanent delete
    file_label TEXT,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE share_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    share_token TEXT UNIQUE NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    download_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    ip TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE INDEX idx_login_attempts ON login_attempts (timestamp);
