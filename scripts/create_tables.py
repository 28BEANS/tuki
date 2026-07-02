import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def main():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env!")
        return

    # asyncpg requires postgresql:// scheme
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    sql_path = "database/sql/001_create_tables.sql"
    if not os.path.exists(sql_path):
        print(f"SQL file not found at {sql_path}!")
        return

    print("Reading SQL Schema...")
    with open(sql_path, "r") as f:
        sql_content = f.read()

    print("Connecting to database...")
    conn = await asyncpg.connect(db_url)
    try:
        print("Executing SQL Schema (001_create_tables.sql)...")
        await conn.execute(sql_content)
        print("SQL Schema executed successfully!")

        rls_path = "database/sql/002_rls_policies.sql"
        if os.path.exists(rls_path):
            print("Reading RLS Policies...")
            with open(rls_path, "r") as f:
                rls_content = f.read()
            print("Executing RLS Policies (002_rls_policies.sql)...")
            await conn.execute(rls_content)
            print("RLS Policies executed successfully!")
            
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
