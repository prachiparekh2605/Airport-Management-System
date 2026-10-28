import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'airport_secret_dev_key_2026')
    
    # MySQL Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'airport_managment_system')
    
    # Connection timeout settings & SSL for Cloud MySQL (Aiven, TiDB, PlanetScale, Railway, AWS RDS)
    MYSQL_CONNECT_TIMEOUT = int(os.getenv('MYSQL_CONNECT_TIMEOUT', 5))
    MYSQL_SSL = os.getenv('MYSQL_SSL', 'false').lower() in ('true', '1', 'yes', 'required')
