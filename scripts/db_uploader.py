import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

# Dynamically resolve the absolute path to the .env file at the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '.env')
load_dotenv(dotenv_path=env_path)

def upload_to_postgres(df, table_name):
    """
    Uploads a cleaned DataFrame to PostgreSQL.
    Reads the database password securely from the .env file.
    """
    try:
        password = os.getenv("DB_PASSWORD")
        
        if not password:
            print("❌ ERROR: Password not found. Ensure 'DB_PASSWORD' is set in your .env file.")
            return

        print(f"⏳ Connecting to PostgreSQL to create/update table '{table_name}'...")
        
        # Connection string (adjust 'postgres' if your DBeaver username is different)
        engine = create_engine(f"postgresql://postgres:{password}@localhost:5432/sports_analytics")
        
        # Upload data to SQL. Replaces the table if it already exists.
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        print(f"✅ SUCCESS! {len(df)} rows securely loaded into SQL table '{table_name}'.")
        
    except Exception as e:
        print(f"❌ PostgreSQL Connection ERROR: {e}")