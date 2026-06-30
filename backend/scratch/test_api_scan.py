import requests
import time

def run_scans():
    base_url = "http://localhost:8000/api"
    # Login to get token
    print("Logging in to get token...")
    # use previous test user or create a new one
    email = "test_scanner@example.com"
    password = "password123"
    requests.post(f"{base_url}/auth/register", json={
        "full_name": "Scanner Tester",
        "email": email,
        "password": password
    })
    res_login = requests.post(f"{base_url}/auth/login", json={
        "email": email,
        "password": password
    })
    token = res_login.json().get("access_token")
    if not token:
        print("Failed to get token!")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    websites = ["lenskart.com", "github.com", "apple.com", "openai.com", "amazon.in"]
    
    for url in websites:
        print(f"\n--- Scanning {url} via API ---")
        start_time = time.time()
        try:
            # Note: the scan endpoint might be /api/audit/scan?url=...
            res = requests.post(f"{base_url}/scan", json={"url": url}, headers=headers)
            print("Scan Status:", res.status_code)
            if res.status_code == 200:
                report = res.json()
                print("Score:", report.get("audit_score"))
                print("ID:", report.get("id") or report.get("_id"))
                print("Pillars:", list(report.get("category_scores", {}).keys()))
            else:
                print("Scan Failed:", res.text)
        except Exception as e:
            print(f"Error scanning {url}: {e}")
        finally:
            print(f"Time taken: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    run_scans()
