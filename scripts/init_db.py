#!/usr/bin/env python3
"""
Initialize or migrate the PostgreSQL database for Market Agent.
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from pathlib import Path

# ---------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in environment or .env file")

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
MIGRATIONS_DIR = SQL_DIR / "migrations"

# ---------------------------------------------------------------------
# Apply SQL files in order
# ---------------------------------------------------------------------
def run_sql_file(conn, file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        sql_text = f.read()
    with conn.cursor() as cur:
        cur.execute(sql.SQL(sql_text))
    print(f"✅ Applied: {file_path.name}")

def main():
    print("Connecting to database...")
    with psycopg2.connect(DATABASE_URL) as conn:
        conn.autocommit = False

        try:
            # 1. Base schema
            schema_file = SQL_DIR / "schema.sql"
            if schema_file.exists():
                run_sql_file(conn, schema_file)

            # 2. Migrations (ordered lexicographically)
            if MIGRATIONS_DIR.exists():
                for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                    run_sql_file(conn, path)

            # 3. Optional seed data
            seeds = SQL_DIR / "seeds.sql"
            if seeds.exists():
                run_sql_file(conn, seeds)

            conn.commit()
            print("🎉 Database initialized successfully.")
        except Exception as e:
            conn.rollback()
            print("❌ Error during initialization:", e)
            raise

if __name__ == "__main__":
    main()
