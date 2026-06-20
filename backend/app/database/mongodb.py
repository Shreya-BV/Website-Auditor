import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "website_auditor")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

def get_database():
    return db_instance.db

def connect_db():
    db_instance.client = AsyncIOMotorClient(MONGODB_URI, tz_aware=True)
    db_instance.db = db_instance.client[DATABASE_NAME]
    print(f"Connected to MongoDB at {MONGODB_URI}, Database: {DATABASE_NAME}")

def close_db():
    if db_instance.client:
        db_instance.client.close()
        print("MongoDB connection closed")
