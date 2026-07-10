"""Debug Dify create dataset response"""
import requests, json

BASE = "http://127.0.0.1:5001"
r = requests.post(f"{BASE}/console/api/login", json={"email": "admin@csic.cn", "password": "***REMOVED-PASSWORD***"})
token = r.json()["data"]["access_token"]

# Create one dataset and print full response
r = requests.post(f"{BASE}/console/api/datasets",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "测试库", "description": "测试"})
print("CREATE status:", r.status_code)
print("CREATE body:", json.dumps(r.json(), ensure_ascii=False, indent=2)[:500])

# List
r = requests.get(f"{BASE}/console/api/datasets?page=1",
    headers={"Authorization": f"Bearer {token}"})
print("\nLIST status:", r.status_code)
print("LIST body:", json.dumps(r.json(), ensure_ascii=False, indent=2)[:1000])
