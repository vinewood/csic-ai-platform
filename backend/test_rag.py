import json, urllib.request

t = json.load(open("/tmp/login.json"))["access_token"]
url = "http://127.0.0.1:8000/api/dify/retrieve?query=%E8%88%B9%E8%88%B6%E5%B7%A5%E4%B8%9A%E6%95%B0%E5%AD%97%E5%8C%96"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + t)
r = urllib.request.urlopen(req)
print(r.read().decode())
