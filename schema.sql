-- Σχήμα βάσης δεδομένων για το Αγρόκτημα
-- SQLite

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('farmer', 'customer')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fields (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    location    TEXT,
    area_stremma REAL,
    crop        TEXT,
    tree_count  INTEGER DEFAULT 0,
    latitude    REAL,
    longitude   REAL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id    INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    task_type   TEXT NOT NULL,
    task_date   TEXT NOT NULL,
    cost        REAL DEFAULT 0,
    notes       TEXT,
    photo_filename TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trees (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    field_id         INTEGER REFERENCES fields(id) ON DELETE SET NULL,
    code             TEXT NOT NULL,
    est_oil_kg_min   REAL,
    est_oil_kg_max   REAL,
    price_per_year   REAL NOT NULL,
    status           TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'adopted')),
    photo_notes      TEXT,
    latitude         REAL,
    longitude        REAL,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS adoptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tree_id       INTEGER NOT NULL REFERENCES trees(id) ON DELETE CASCADE,
    customer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    season_year   INTEGER NOT NULL,
    amount        REAL NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'cancelled')),
    stripe_session_id TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    paid_at       TEXT
);

CREATE TABLE IF NOT EXISTS production_updates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tree_id     INTEGER NOT NULL REFERENCES trees(id) ON DELETE CASCADE,
    update_date TEXT NOT NULL,
    message     TEXT NOT NULL,
    photo_filename TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS harvests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id      INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    harvest_date  TEXT NOT NULL,
    product       TEXT NOT NULL,
    quantity_kg   REAL NOT NULL,
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_harvests_field ON harvests(field_id);

CREATE TABLE IF NOT EXISTS planned_tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id      INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    task_type     TEXT NOT NULL,
    planned_date  TEXT NOT NULL,
    notes         TEXT,
    status        TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_planned_tasks_field ON planned_tasks(field_id);

CREATE TABLE IF NOT EXISTS reminder_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sent_date   TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(farmer_id, sent_date)
);

CREATE TABLE IF NOT EXISTS advisor_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL,
    is_ai       INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_advisor_farmer ON advisor_messages(farmer_id);
CREATE INDEX IF NOT EXISTS idx_fields_farmer ON fields(farmer_id);
CREATE INDEX IF NOT EXISTS idx_tasks_field ON tasks(field_id);
CREATE INDEX IF NOT EXISTS idx_trees_farmer ON trees(farmer_id);
CREATE INDEX IF NOT EXISTS idx_adoptions_tree ON adoptions(tree_id);
CREATE INDEX IF NOT EXISTS idx_adoptions_customer ON adoptions(customer_id);
