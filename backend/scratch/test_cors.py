import httpx
import asyncio

async def test_cors():
    url = "http://localhost:8000/api/visitor"
    headers = {
        "Origin": "https://website-auditor-amok17kl4-shreya-bvs-projects.vercel.app",
        "Access-Control-Request-Method": "POST"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.options(url, headers=headers)
        print(f"Status Code: {resp.status_code}")
        print("Headers:")
        for k, v in resp.headers.items():
            print(f"  {k}: {v}")
            
        if "access-control-allow-origin" in resp.headers:
            print("CORS is successfully configured for the preview domain!")
        else:
            print("CORS configuration failed.")

if __name__ == "__main__":
    asyncio.run(test_cors())
