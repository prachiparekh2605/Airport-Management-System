import os
import shutil
import sqlite3
import pymysql
import pymysql.cursors
from config import Config

import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_SOURCE_DB = os.path.join(BASE_DIR, 'database', 'airport.db')

def get_sqlite_path():
    """
    Return path to SQLite database.
    On Vercel, the filesystem is read-only except the temporary directory (/tmp).
    We copy the seed database to temp on cold starts so writes work without errors.
    """
    if os.environ.get('VERCEL'):
        tmp_dir = tempfile.gettempdir()
        tmp_db = os.path.join(tmp_dir, 'airport.db')
        if not os.path.exists(tmp_db) and os.path.exists(SQLITE_SOURCE_DB):
            try:
                shutil.copyfile(SQLITE_SOURCE_DB, tmp_db)
            except Exception as e:
                print(f"[SQLite] Warning copying DB to temp: {e}")
        return tmp_db if os.path.exists(tmp_db) else SQLITE_SOURCE_DB
    return SQLITE_SOURCE_DB

def is_sqlite_mode():
    """
    Determine if SQLite should be used:
    1. If explicitly set via USE_SQLITE=true
    2. If running on Vercel and MYSQL_HOST is still default 'localhost'
    """
    if os.getenv('USE_SQLITE', 'false').lower() in ('true', '1', 'yes'):
        return True
    if os.environ.get('VERCEL') and Config.MYSQL_HOST in ('localhost', '127.0.0.1'):
        return True
    return False

def get_db_connection():
    """
    Establish and return a connection.
    Attempts MySQL first (unless in SQLite mode).
    If MySQL connection fails with connection refused (e.g. 2003), falls back to SQLite.
    """
    if is_sqlite_mode():
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row
        return conn

    conn_params = {
        'host': Config.MYSQL_HOST,
        'port': Config.MYSQL_PORT,
        'user': Config.MYSQL_USER,
        'password': Config.MYSQL_PASSWORD,
        'database': Config.MYSQL_DB,
        'cursorclass': pymysql.cursors.DictCursor,
        'connect_timeout': Config.MYSQL_CONNECT_TIMEOUT,
        'autocommit': False,
        'charset': 'utf8mb4'
    }
    if getattr(Config, 'MYSQL_SSL', False):
        conn_params['ssl'] = {'ssl_mode': 'REQUIRED'}

    try:
        return pymysql.connect(**conn_params)
    except Exception as e:
        # Check if error is connection error (e.g. 2003 or connection refused)
        if hasattr(e, 'args') and len(e.args) >= 1 and (e.args[0] == 2003 or 'Connection refused' in str(e) or 'timed out' in str(e)):
            print(f"[Notice] MySQL at {Config.MYSQL_HOST} unreachable. Falling back to embedded SQLite database.")
            conn = sqlite3.connect(get_sqlite_path())
            conn.row_factory = sqlite3.Row
            return conn
        raise e

def test_connection():
    """
    Test database connection and return (success, message).
    """
    try:
        conn = get_db_connection()
        if isinstance(conn, sqlite3.Connection):
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            conn.close()
            return True, "Connected to embedded SQLite database (airport.db)"
        else:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS test;")
                cursor.fetchone()
            conn.close()
            return True, f"Connected to MySQL successfully ({Config.MYSQL_HOST}:{Config.MYSQL_PORT})"
    except Exception as e:
        return False, str(e)

def query_db(query, args=(), one=False):
    """
    Run a parameterized SELECT query and return rows as dictionaries.
    Compatible with both MySQL (%s) and SQLite (?).
    """
    conn = get_db_connection()
    try:
        if isinstance(conn, sqlite3.Connection):
            sqlite_query = query.replace('%s', '?')
            cursor = conn.cursor()
            cursor.execute(sqlite_query, args)
            rows = cursor.fetchall()
            dict_rows = [dict(row) for row in rows]
            return (dict_rows[0] if dict_rows else None) if one else dict_rows
        else:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                rv = cursor.fetchall()
                return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), return_id=False):
    """
    Run a parameterized INSERT, UPDATE, or DELETE statement with commit.
    Returns last_insert_id if return_id=True, otherwise rowcount.
    Compatible with both MySQL (%s) and SQLite (?).
    """
    conn = get_db_connection()
    try:
        if isinstance(conn, sqlite3.Connection):
            sqlite_query = query.replace('%s', '?')
            cursor = conn.cursor()
            cursor.execute(sqlite_query, args)
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            return last_id if return_id else affected
        else:
            with conn.cursor() as cursor:
                affected = cursor.execute(query, args)
                last_id = cursor.lastrowid
            conn.commit()
            return last_id if return_id else affected
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def format_db_error(e):
    """
    Translate database exceptions into user-friendly error messages.
    """
    err_str = str(e)
    if hasattr(e, 'args') and len(e.args) >= 2:
        code, msg = e.args[0], e.args[1]
        if code == 1062:
            return "Duplicate entry error: A record with this unique value already exists."
        elif code == 1451:
            return "Cannot delete or update: This record is referenced by other active records in the system."
        elif code == 1452:
            return "Cannot add or update: Referenced foreign key does not exist."
        elif code == 1045:
            return "MySQL Access Denied: Please check your MySQL username and password."
        elif code == 1049:
            return f"MySQL Database Unknown: The database '{Config.MYSQL_DB}' does not exist yet."
        elif code == 2003:
            return f"Cannot connect to MySQL server at '{Config.MYSQL_HOST}:{Config.MYSQL_PORT}'."
        return f"Database error ({code}): {msg}"
    return f"Database error: {err_str}"
