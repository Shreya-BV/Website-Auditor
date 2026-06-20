import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["website_auditor"]
    
    collections = ["leads", "scans", "visitor_logs"]
    for col in collections:
        result = await db[col].update_many(
            {"created_at": {"$exists": False}, "timestamp": {"$exists": True}},
            [{"$set": {"created_at": "$timestamp", "updated_at": "$timestamp"}}]
        )
        print(f"Migrated {result.modified_count} documents in {col}")
        
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
