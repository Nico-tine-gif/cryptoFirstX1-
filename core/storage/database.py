import sqlite3
from pathlib import Path

DATABASE = Path("data/cryptoFirstX1.db")


def connect():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def initialize():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS blocks (
            network TEXT NOT NULL,
            height INTEGER NOT NULL,
            block_hash TEXT,
            previous_hash TEXT,
            timestamp INTEGER,
            transaction_count INTEGER,
            detected_at INTEGER NOT NULL,
            PRIMARY KEY(network, height)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            network TEXT NOT NULL,
            txid TEXT NOT NULL,
            block_height INTEGER,
            block_hash TEXT,
            confirmed INTEGER DEFAULT 0,
            confirmations INTEGER DEFAULT 0,
            fee INTEGER,
            size INTEGER,
            weight INTEGER,
            first_seen INTEGER,
            last_seen INTEGER,
            status TEXT,
            raw_json TEXT,
            PRIMARY KEY(network, txid)
        );

        CREATE TABLE IF NOT EXISTS watched_addresses (
            network TEXT NOT NULL,
            address TEXT NOT NULL,
            label TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL,
            PRIMARY KEY(network, address)
        );

        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            network TEXT NOT NULL,
            address TEXT NOT NULL,
            txid TEXT NOT NULL,
            vout INTEGER,
            amount INTEGER NOT NULL,
            block_height INTEGER,
            confirmations INTEGER DEFAULT 0,
            status TEXT DEFAULT 'DETECTED',
            detected_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            UNIQUE(network, txid, vout, address)
        );

        CREATE TABLE IF NOT EXISTS mempool_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            network TEXT NOT NULL,
            txid TEXT,
            event TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            data TEXT
        );

        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            data TEXT
        );
        """)


if __name__ == "__main__":
    initialize()
    print("DATABASE: READY")
