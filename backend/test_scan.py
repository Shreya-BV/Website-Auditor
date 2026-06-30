import asyncio
from app.scanners.engine import run_scan

async def main():
    websites = ["lenskart.com", "www.titaneyeplus.com", "www.fastrack.in"]
    for url in websites:
        print(f"\n--- Scanning {url} ---")
        try:
            report = await run_scan(url)
            print("Score:", report["audit_score"])
            print("Rendering mode:", report["performance_metrics"]["rendering_method"])
            for pillar, scores in report["category_scores"].items():
                print(f"Pillar {pillar}: {scores}")
                # print(f"Explanations: {report['pillar_details'][pillar]['technical_explanation']}")
        except Exception as e:
            print(f"Failed to scan {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
