import os
import decimal
import datetime
import sqlite3
import pymysql
import pymysql.cursors
from config import Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database', 'airport.db')

def serialize_val(val):
    if val is None:
        return None
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
        return val.isoformat()
    return val

def sync():
    print("Connecting to local MySQL...")
    mconn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )
    
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

    sconn = sqlite3.connect(DB_FILE)
    scur = sconn.cursor()
    scur.execute("PRAGMA foreign_keys = OFF;")

    with mconn.cursor() as mcur:
        mcur.execute("SHOW TABLES;")
        tables = [list(row.values())[0] for row in mcur.fetchall()]
        print(f"Found MySQL tables: {tables}")

        for table in tables:
            mcur.execute(f"SHOW COLUMNS FROM `{table}`;")
            columns = mcur.fetchall()
            
            col_defs = []
            col_names = []
            for col in columns:
                field = col['Field']
                col_names.append(field)
                col_type = col['Type'].upper()
                extra = col.get('Extra', '').upper()
                
                if 'INT' in col_type:
                    if 'AUTO_INCREMENT' in extra:
                        sq_type = 'INTEGER PRIMARY KEY AUTOINCREMENT'
                    else:
                        sq_type = 'INTEGER'
                elif any(t in col_type for t in ['DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE']):
                    sq_type = 'REAL'
                else:
                    sq_type = 'TEXT'

                col_defs.append(f"`{field}` {sq_type}")

            create_sql = f"CREATE TABLE IF NOT EXISTS `{table}` ({', '.join(col_defs)});"
            scur.execute(create_sql)

            mcur.execute(f"SELECT * FROM `{table}`;")
            rows = mcur.fetchall()
            print(f"Table '{table}': copying {len(rows)} rows...")

            if rows:
                placeholders = ', '.join(['?'] * len(col_names))
                quoted_cols = ', '.join([f"`{c}`" for c in col_names])
                insert_sql = f"INSERT INTO `{table}` ({quoted_cols}) VALUES ({placeholders});"
                
                row_values = []
                for row in rows:
                    vals = [serialize_val(row[c]) for c in col_names]
                    row_values.append(vals)
                
                scur.executemany(insert_sql, row_values)

    sconn.commit()
    sconn.close()
    mconn.close()
    print("All tables and data successfully transferred from MySQL to SQLite database!")

if __name__ == '__main__':
    sync()
