import asyncio
from app.scanners.engine import run_scan

async def main():
    print("Scanning Lenskart...")
    report1 = await run_scan("https://www.lenskart.com")
    print("Lenskart Score:", report1.get("overall_score"))
    print("Lenskart Pillar Scores:", report1.get("pillar_scores"))
    print("Errors:", report1.get("error"))
    
    print("\nScanning Amazon...")
    report2 = await run_scan("https://www.amazon.in")
    print("Amazon Score:", report2.get("overall_score"))
    print("Amazon Pillar Scores:", report2.get("pillar_scores"))
    print("Errors:", report2.get("error"))

if __name__ == "__main__":
    asyncio.run(main())
