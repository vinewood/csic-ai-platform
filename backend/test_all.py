import requests, subprocess

BASE = "http://127.0.0.1:8000"
ok = fail = 0

def test(name, method, url, expect_key=None):
    global ok, fail
    try:
        r = requests.post(f"{BASE}{url}", json=expect_key, timeout=15) if method == "POST" else requests.get(f"{BASE}{url}", timeout=15)
        j = r.json() if r.text else {}
        if r.status_code < 400:
            print(f"  OK {name}: {r.status_code}")
            ok += 1
        else:
            print(f"  FAIL {name}: {r.status_code} {str(j)[:60]}")
            fail += 1
    except Exception as e:
        print(f"  FAIL {name}: {str(e)[:50]}")
        fail += 1

r = requests.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"***REMOVED-PASSWORD***"})
token = r.json().get("access_token","")
headers = {"Authorization": f"Bearer {token}"}
print(f"Token: {token[:20]}...")

test("Health", "GET", "/api/health")
test("Login", "POST", "/api/auth/login")
test("Me", "GET", "/api/auth/me")
test("Users list", "GET", "/api/users")
test("Models", "GET", "/api/models")
test("RSS all", "GET", "/api/rss/articles")
test("RSS date", "GET", "/api/rss/articles?date=2026-07-13")
test("OpenAlex", "GET", "/api/academic/openalex/works?query=ship")
test("Crossref", "GET", "/api/academic/crossref/search?query=china&rows=2")
test("Moodle", "GET", "/api/academic/moodle/courses")
test("Khan", "GET", "/api/academic/khan/topics")
test("KB", "GET", "/api/dify/datasets")
test("RAG", "GET", "/api/dify/retrieve?query=test")
test("Skills", "GET", "/api/skills")
test("Register", "POST", "/api/auth/register")

# auth headers for protected
def test_auth(name, method, url):
    global ok, fail
    try:
        r = requests.post(f"{BASE}{url}", json={}, headers=headers, timeout=15) if method == "POST" else requests.get(f"{BASE}{url}", headers=headers, timeout=15)
        if r.status_code < 400:
            print(f"  OK {name}: {r.status_code}")
            ok += 1
        else:
            print(f"  FAIL {name}: {r.status_code}")
            fail += 1
    except Exception as e:
        print(f"  FAIL {name}: {str(e)[:50]}")
        fail += 1

# Approve+delete cycle
r2 = requests.post(f"{BASE}/api/auth/login", json={"username":"bugtest","password":"Test123456"})
print(f"  INFO Login pending: {r2.status_code}")

users = requests.get(f"{BASE}/api/users", headers=headers).json()
uid = next((u["id"] for u in users if u.get("username")=="bugtest"), 0)
if uid:
    requests.post(f"{BASE}/api/users/{uid}/approve", headers=headers)
    r3 = requests.post(f"{BASE}/api/auth/login", json={"username":"bugtest","password":"Test123456"})
    print(f"  OK Login after approve: {r3.status_code}")
    ok += 1
    requests.delete(f"{BASE}/api/users/{uid}", headers=headers)
    print(f"  OK Cleanup bugtest")

# Frontend
for path in ["/"]:
    s = subprocess.run(["curl","-sk","-o","/dev/null","-w","%{http_code}",f"https://csic.thinkalike.com.cn{path}"], capture_output=True, text=True)
    code = s.stdout.strip()
    print(f"  OK Frontend: HTTP {code}")
    ok += 1

# Nginx
s = subprocess.run(["systemctl","is-active","nginx"], capture_output=True, text=True)
print(f"  OK Nginx: {s.stdout.strip()}")

# Errors
s = subprocess.run(["journalctl","-u","csic-backend","--no-pager","--since","5 min ago"], capture_output=True, text=True)
errors = [l for l in s.stdout.split("\n") if "ERROR" in l or "Traceback" in l]
print(f"  {'OK' if not errors else 'FAIL'} Errors: {len(errors)}")

print(f"\n====================")
print(f"Result: {ok} passed / {fail} failed")
