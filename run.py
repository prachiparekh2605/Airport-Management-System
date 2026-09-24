import sys
from app import app
from db import test_connection
from config import Config

def main():
    print("=" * 60)
    print("  SkyOps Hub - Airport Staff Management System")
    print(f"  Target Database: {Config.MYSQL_DB}")
    print(f"  Target Host:     {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
    print("=" * 60)

    ok, msg = test_connection()
    if ok:
        print("[OK] MySQL Database Connection verified successfully.")
    else:
        print(f"[!] Database Connection Notice: {msg}")
        print("    If your database is protected with a password, ensure it is set in .env")

    print("\nStarting SkyOps Web Server at http://127.0.0.1:5000 and http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
