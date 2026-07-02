import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def main():
    load_dotenv()
    db_url = os.getenv("SUPABASE_DATABASE_URL")
    if not db_url:
        print("SUPABASE_DATABASE_URL not found in .env!")
        return

    # asyncpg requires postgresql:// scheme
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to database...")
    conn = await asyncpg.connect(db_url)
    try:
        print("Executing migration SQL...")
        # Check if full_name column exists in user_profiles
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'full_name'
        """)
        
        if columns:
            print("Renaming column full_name to first_name...")
            await conn.execute("ALTER TABLE user_profiles RENAME COLUMN full_name TO first_name;")
        else:
            print("Column 'full_name' already renamed or does not exist.")

        # Check if last_name column exists in user_profiles
        last_name_col = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'last_name'
        """)
        
        if not last_name_col:
            print("Adding column last_name...")
            await conn.execute("ALTER TABLE user_profiles ADD COLUMN last_name VARCHAR(255);")
        else:
            print("Column 'last_name' already exists.")

        print("Migration query executed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
