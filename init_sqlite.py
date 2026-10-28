import os
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_FILE = os.path.join(BASE_DIR, 'database', 'airport.sql')
DB_FILE = os.path.join(BASE_DIR, 'database', 'airport.db')

def build_sqlite_db():
    if not os.path.exists(SQL_FILE):
        raise FileNotFoundError(f"SQL file not found at {SQL_FILE}")

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Remove single-line comments
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith('--'):
            continue
        lines.append(line)
    full_sql = '\n'.join(lines)

    # Split into statements by semicolons outside quotes
    statements = []
    current = []
    in_quote = False
    quote_char = ''

    for char in full_sql:
        if char in ("'", '"') and not in_quote:
            in_quote = True
            quote_char = char
            current.append(char)
        elif in_quote and char == quote_char:
            in_quote = False
            current.append(char)
        elif char == ';' and not in_quote:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)

    # If DB already exists, delete it first
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")

    for raw_stmt in statements:
        stmt = raw_stmt.strip()
        if not stmt:
            continue
        # Skip CREATE DATABASE and USE statements
        if re.match(r'^(CREATE DATABASE|USE\s+)', stmt, re.IGNORECASE):
            continue
        
        # Strip ENGINE=InnoDB and character sets
        stmt = re.sub(r'ENGINE\s*=\s*InnoDB', '', stmt, flags=re.IGNORECASE)
        stmt = re.sub(r'CHARACTER\s+SET\s+\w+', '', stmt, flags=re.IGNORECASE)
        stmt = re.sub(r'COLLATE\s+\w+', '', stmt, flags=re.IGNORECASE)
        # Convert AUTO_INCREMENT
        stmt = re.sub(r'\bINT\s+PRIMARY\s+KEY\s+AUTO_INCREMENT\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', stmt, flags=re.IGNORECASE)
        stmt = re.sub(r'\bAUTO_INCREMENT\b', 'AUTOINCREMENT', stmt, flags=re.IGNORECASE)
        # Remove multiline ON DUPLICATE KEY UPDATE clause
        stmt = re.sub(r'\s+ON\s+DUPLICATE\s+KEY\s+UPDATE.*$', '', stmt, flags=re.IGNORECASE | re.DOTALL)
        
        cursor.execute(stmt)

    conn.commit()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
    print(f"SQLite database successfully created at: {DB_FILE}")
    print(f"Total tables: {len(tables)} -> {', '.join(tables)}")

    cursor.execute("SELECT COUNT(*) FROM Employee;")
    print(f"Employee seed records count: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM Flight;")
    print(f"Flight seed records count: {cursor.fetchone()[0]}")

    conn.close()

if __name__ == '__main__':
    build_sqlite_db()
