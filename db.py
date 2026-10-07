"""
Σύνδεση και βοηθητικές συναρτήσεις για τη βάση δεδομένων (SQLite).
"""
import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agroktima.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_db():
    """Επιστρέφει μία σύνδεση στη βάση, μία ανά request (Flask app context)."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_column(conn, table, column, coltype):
    """Προσθέτει στήλη σε υπάρχοντα πίνακα αν λείπει (ασφαλές migration)."""
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def init_db():
    """Δημιουργεί τους πίνακες αν δεν υπάρχουν ήδη. Ασφαλές να τρέχει κάθε φορά."""
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    # Μικρά migrations για βάσεις που δημιουργήθηκαν με παλιότερη έκδοση του schema:
    _ensure_column(conn, "tasks", "photo_filename", "TEXT")
    _ensure_column(conn, "production_updates", "photo_filename", "TEXT")
    _ensure_column(conn, "fields", "latitude", "REAL")
    _ensure_column(conn, "fields", "longitude", "REAL")
    _ensure_column(conn, "trees", "latitude", "REAL")
    _ensure_column(conn, "trees", "longitude", "REAL")
    conn.commit()
    conn.close()


def register_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
