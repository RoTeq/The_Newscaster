# Sqlite db implementation to have peple stored

###############################
######## Imports ##############
###############################

import sqlite3
import os

###############################
######## Load Env #############
###############################



class oracleDB():
    tables = [
        "global_stats",
        "users"
    ]

    def __init__(self, db:str):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                ghoul_count INTEGER DEFAULT 0
            )
        """)

    # Update / Insert Rows
    #########################

    def upsert_global(self, key:str, value:str):
        self.cursor.execute("""
            INSERT INTO global_stats (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET VALUE = ?
        """, (key, value, value))
        self.conn.commit()

    def upsert_user(self, user_id:int, username:str, ghoul_increment:int = 1):
        self.cursor.execute("""
            INSERT INTO users (user_id, username, ghoul_count)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                ghoul_count = ghoul_count + ?,
                username = ?
        """, (user_id, username, ghoul_increment, ghoul_increment, username))
        self.conn.commit()

    # Get Rows
    ##########################

    def get_top_ghouls(self, limit: int = 5):
        """Returns a list of tuples/rows with the top users and their counts."""

        self.conn.row_factory = sqlite3.Row
        self.cursor.execute(
            """
            SELECT username, ghoul_count 
            FROM users 
            ORDER BY ghoul_count DESC 
            LIMIT ?
        """,(limit,))

        return self.cursor.fetchall()

    def get_global_stat(self, key: str, default=None):
        """Fetches a value from global_stats based on the provided key."""

        self.cursor.execute(
            """
            SELECT value 
            FROM global_stats 
            WHERE key = ?
        """,(key,))

        row = self.cursor.fetchone()
        return row[0] if row else default