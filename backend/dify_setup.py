"""Dify setup script — create datasets and store access token in DB"""
import requests, json, sqlite3

BASE = "http://127.0.0.1:5001"
ADMIN = {"email": "admin@csic.cn", "password": "***REMOVED-PASSWORD***"}

# 1. Login
r = requests.post(f"{BASE}/console/api/login", json=ADMIN)
token = r.json()["data"]["access_token"]
print(f"Login OK: token={token[:20]}...")

# 2. Create datasets
datasets_created = []
for name, desc in [
    ("党建知识库", "党的建设理论、政策文件、案例分析"),
    ("船舶工程资料", "船舶设计制造、海洋工程、军工技术"),
    ("教学资源库", "培训课件、教材、教案、考试题库"),
]:
    r = requests.post(f"{BASE}/console/api/datasets",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name, "description": desc})
    data = r.json()
    print(f"Created: {name} → id={data.get('id', '?')}")
    datasets_created.append(data)

# 3. List datasets
r = requests.get(f"{BASE}/console/api/datasets?page=1&limit=20",
    headers={"Authorization": f"Bearer {token}"})
ds = r.json()
print(f"\nDatasets: {len(ds.get('data', []))} total={ds.get('total', 0)}")
for d in ds.get("data", []):
    print(f"  {d['name']} ({d.get('document_count', 0)} docs) - {d.get('id', '')}")

# 4. Save Dify config to CSIC DB
conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
cfg = json.dumps({"key": token, "email": "admin@csic.cn"})
conn.execute("INSERT OR REPLACE INTO api_configs (provider, config_json) VALUES (?, ?)", ("dify", cfg))
conn.commit()
conn.close()
print("\nDify config saved to CSIC DB")
