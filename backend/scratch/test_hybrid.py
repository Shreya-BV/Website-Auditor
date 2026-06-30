import asyncio
import sys
import json
import os
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.scanners.engine import run_scan

async def main():
    urls = [
        "https://www.python.org", # Should be HTTPX
    ]
    
    for url in urls:
        print(f"\n--- Scanning {url} ---")
        try:
            result = await run_scan(url)
            print(f"Overall Score: {result['overall_score']}")
            print(f"Grade: {result['grade']}")
            print(f"Rendering Mode: {result['debug']['rendering_mode']}")
            print(f"Response Time: {result['debug']['response_time']:.2f}s")
            
        except Exception as e:
            print(f"Error scanning {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
