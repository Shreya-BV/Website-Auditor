import requests
import random
import string

def test_auth():
    base_url = "http://localhost:8000/api/auth"
    email = f"test_{''.join(random.choices(string.ascii_lowercase, k=5))}@example.com"
    password = "password123"
    full_name = "Test User"
    
    # 1. Register
    print(f"Registering {email}...")
    res = requests.post(f"{base_url}/register", json={
        "full_name": full_name,
        "email": email,
        "password": password
    })
    print("Register Status:", res.status_code)
    print("Register Response:", res.text)
    
    if res.status_code != 200:
        return
        
    # 2. Login
    print(f"\nLogging in with {email}...")
    res = requests.post(f"{base_url}/login", json={
        "email": email,
        "password": password
    })
    print("Login Status:", res.status_code)
    print("Login Response:", res.text)

if __name__ == "__main__":
    test_auth()
