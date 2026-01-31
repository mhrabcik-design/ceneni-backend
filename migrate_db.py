import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in environment")
        return

    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("Checking/Adding columns to 'sources' table...")
        
        # Add offer_number if not exists
        try:
            conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS offer_number VARCHAR;"))
            print("Column 'offer_number' checked/added.")
        except Exception as e:
            print(f"Error adding offer_number: {e}")

        # Add file_hash if not exists
        try:
            conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS file_hash VARCHAR UNIQUE;"))
            print("Column 'file_hash' checked/added.")
        except Exception as e:
            print(f"Error adding file_hash: {e}")
            
        conn.commit()
    
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
