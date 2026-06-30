import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient('mongodb+srv://websiteauditor:shni0531@cluster0.4dxqunq.mongodb.net/website_auditor?retryWrites=true&w=majority&appName=Cluster0')
    db = client['website_auditor']
    users = await db.users.find({'email': {'$not': {'$regex': '^test'}}}).to_list(10)
    print(f"Found {len(users)} real users")
    for u in users:
        print(f"email: {u.get('email')}, hp: {bool(u.get('hashed_password'))}, p: {bool(u.get('password'))}")
        if u.get('hashed_password'):
            print(f"  hp val: {str(u['hashed_password'])[:15]}...")
        if u.get('password'):
            print(f"  p val: {str(u['password'])[:15]}...")
asyncio.run(main())
