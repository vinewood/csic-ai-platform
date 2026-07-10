import sqlite3, json, sys
sys.path.insert(0, "/www/wwwroot/csic.thinkalike.com.cn/backend")
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjI2NDc2MDMwNjAsInRpbWVzdGFtcCI6MTc4MzY4OTQ2MiwidXNlcl9pZCI6IjZhNTBmMGQ2NjM2ODUzMGVkNmYzYWVmNyJ9.kcNSsc5hUy5sx1gmY8GFoEmc3MJAEDrFe2mjSKHBLWo"
DB = "/www/wwwroot/csic.thinkalike.com.cn/data/csic.db"
conn = sqlite3.connect(DB)
conn.execute("INSERT OR REPLACE INTO api_configs (id, provider, config_json) VALUES ((SELECT id FROM api_configs WHERE provider='aminer'), 'aminer', ?)", (json.dumps({"key": KEY}),))
conn.commit()
print("AMiner key saved")
# Test
import urllib.request
req = urllib.request.Request("https://datacenter.aminer.cn/gateway/open_platform/api/paper/search/pro?page=0&size=2&keyword=党建")
req.add_header("Authorization", KEY)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    print(f"API OK: total={data.get('total','?')}")
except Exception as e:
    print(f"API fail: {e}")
