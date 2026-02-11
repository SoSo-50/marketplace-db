import os
from datetime import timedelta

class Config:
    raw_db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://marketplace_user:marketplace_user@localhost:5433/marketplace_db')
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False