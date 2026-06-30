import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.database.mongodb import db_instance, connect_db, close_db

async def check():
    connect_db()
    db = db_instance.db
    users = await db["users"].find().to_list(length=10)
    for u in users:
        print(f"Email: {u.get('email')}, hashed_password: {bool(u.get('hashed_password'))}, password: {bool(u.get('password'))}")
        if u.get('hashed_password'):
            print(f"  hashed_password starts with: {str(u['hashed_password'])[:10]}")
        if u.get('password'):
            print(f"  password starts with: {str(u['password'])[:10]}")
    close_db()

asyncio.run(check())
