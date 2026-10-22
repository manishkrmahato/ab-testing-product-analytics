-- Database Schema for A/B Testing Analytics

DROP TABLE IF EXISTS raw_events;
CREATE TABLE raw_events (
    user_id INTEGER,
    timestamp TEXT NOT NULL,
    group_name TEXT NOT NULL,
    landing_page TEXT NOT NULL,
    converted INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_user_id ON raw_events(user_id);
CREATE INDEX IF NOT EXISTS idx_raw_group ON raw_events(group_name);

DROP TABLE IF EXISTS clean_events;
CREATE TABLE clean_events (
    user_id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    group_name TEXT NOT NULL,
    landing_page TEXT NOT NULL,
    converted INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_clean_group ON clean_events(group_name);
CREATE INDEX IF NOT EXISTS idx_clean_landing_page ON clean_events(landing_page);

DROP TABLE IF EXISTS user_countries;
CREATE TABLE user_countries (
    user_id INTEGER PRIMARY KEY,
    country TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_country ON user_countries(country);
