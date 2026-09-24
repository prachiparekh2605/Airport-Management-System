import pymysql
import pymysql.cursors
from config import Config

def get_db_connection():
    """
    Establish and return a connection to the MySQL database.
    Uses DictCursor so columns can be accessed by name.
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=Config.MYSQL_CONNECT_TIMEOUT,
        autocommit=False,
        charset='utf8mb4'
    )

def test_connection():
    """
    Test database connection and return (success, message).
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS test;")
            result = cursor.fetchone()
        conn.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

def query_db(query, args=(), one=False):
    """
    Run a parameterized SELECT query and return rows.
    """
    conn = get_db_connection()
    try:
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
    """
    conn = get_db_connection()
    try:
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
    Translate MySQL database exceptions into user-friendly error messages.
    """
    err_str = str(e)
    # Check for MySQL Integrity Error codes
    if hasattr(e, 'args') and len(e.args) >= 2:
        code, msg = e.args[0], e.args[1]
        if code == 1062:
            return f"Duplicate entry error: A record with this unique value already exists."
        elif code == 1451:
            return f"Cannot delete or update: This record is referenced by other active records in the system."
        elif code == 1452:
            return f"Cannot add or update: Referenced foreign key does not exist."
        elif code == 1045:
            return f"MySQL Access Denied: Please check your MySQL username and password in .env."
        elif code == 1049:
            return f"MySQL Database Unknown: The database '{Config.MYSQL_DB}' does not exist yet. Please create it or import airport.sql."
        return f"Database error ({code}): {msg}"
    return f"Database error: {err_str}"
