import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

def get_database():
    return db_instance.db

async def connect_db():
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME", "website_auditor")
    
    logger.info("=== Loaded Environment Variables ===")
    logger.info(f"MongoDB URI Present: {'Yes' if mongodb_uri else 'No'}")
    logger.info(f"Database Name: {database_name}")
    
    if not mongodb_uri:
        error_msg = "Startup Error: MONGODB_URI environment variable is missing. Please set MONGODB_URI in your .env file or Railway variables."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    try:
        db_instance.client = AsyncIOMotorClient(mongodb_uri, tz_aware=True, serverSelectionTimeoutMS=5000)
        # Ping the server
        await db_instance.client.admin.command('ping')
        db_instance.db = db_instance.client[database_name]
        logger.info("Connection Status: MongoDB Connected Successfully")
    except Exception as e:
        error_msg = f"Startup Error: Failed to connect to MongoDB - {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg)

def close_db():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed cleanly")
