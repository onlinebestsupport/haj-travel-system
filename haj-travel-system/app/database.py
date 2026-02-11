import os
import psycopg2

def get_db():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def init_db():
    print("✅ Database connected")
