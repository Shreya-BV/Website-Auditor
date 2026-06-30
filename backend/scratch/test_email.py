import httpx
import asyncio

async def test_email():
    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post("http://127.0.0.1:8000/api/auth/login", data={
            "username": "testaudit@example.com",
            "password": "Password123!"
        })
        print("Login:", response.status_code, response.json())
        token = response.json()["access_token"]
        
        # Get history to find an audit
        headers = {"Authorization": f"Bearer {token}"}
        history = await client.get("http://127.0.0.1:8000/api/audit/history", headers=headers)
        audits = history.json()
        if not audits:
            print("No audits found")
            return
        audit_id = audits[0]["_id"]
        
        # Retry email
        retry = await client.post(f"http://127.0.0.1:8000/api/audit/retry-email/{audit_id}", headers=headers)
        print("Retry email:", retry.status_code, retry.json())

if __name__ == "__main__":
    asyncio.run(test_email())
