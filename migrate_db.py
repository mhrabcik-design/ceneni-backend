from sqlalchemy import create_engine, text
import os

db_url = os.getenv('DATABASE_URL', 'sqlite:///Input/04_Databaze/prices_v2.db')
engine = create_engine(db_url)

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE sources ADD COLUMN source_type VARCHAR DEFAULT 'SUPPLIER'"))
        conn.commit()
        print("Migration successful: Added source_type to sources.")
    except Exception as e:
        print(f"Migration skipped or failed: {e}")
