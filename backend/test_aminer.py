import json, urllib.request
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjI2NDc2MDMwNjAsInRpbWVzdGFtcCI6MTc4MzY4OTQ2MiwidXNlcl9pZCI6IjZhNTBmMGQ2NjM2ODUzMGVkNmYzYWVmNyJ9.kcNSsc5hUy5sx1gmY8GFoEmc3MJAEDrFe2mjSKHBLWo"

endpoints = [
    "/gateway/open_platform/api/paper/search/pro",
    "/open/api/paper/search",
    "/api/paper/search",
    "/api/v1/paper/search",
]

for ep in endpoints:
    url = "https://datacenter.aminer.cn" + ep + "?page=0&size=2&title=ai"
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + KEY)
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read())
        print("%s -> OK: %s" % (ep, str(data.get("total","?"))[:40]))
        break
    except Exception as e:
        print("%s -> %s" % (ep, str(e)[:50]))

# Also try the main API host
print("\nTrying alternate host...")
url = "https://api.aminer.cn/api/paper/search?page=0&size=2&title=ai"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + KEY)
try:
    resp = urllib.request.urlopen(req, timeout=8)
    data = json.loads(resp.read())
    print("api.aminer.cn -> OK: %s" % str(data)[:100])
except Exception as e:
    print("api.aminer.cn -> %s" % str(e)[:80])

# Try open.aminer.cn
url = "https://open.aminer.cn/api/paper/search?page=0&size=2&title=ai"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + KEY)
try:
    resp = urllib.request.urlopen(req, timeout=8)
    data = json.loads(resp.read())
    print("open.aminer.cn -> OK: %s" % str(data)[:100])
except Exception as e:
    print("open.aminer.cn -> %s" % str(e)[:80])
