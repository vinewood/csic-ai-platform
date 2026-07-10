"""AMiner 学术搜索集成服务 — 真实 API 调用"""

import jwt
import time
import json
import urllib.request
import urllib.parse
import sqlite3
from pathlib import Path

AMINER_BASE = "https://datacenter.aminer.cn/gateway/open_platform/api"


def _get_aminer_credentials():
    """从数据库读取 AMiner API Key"""
    try:
        db_path = Path(__file__).resolve().parent.parent.parent / "data" / "csic.db"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT config_json FROM api_configs WHERE provider='aminer' LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            cfg = json.loads(row[0])
            return cfg.get("key", ""), cfg.get("baseUrl", AMINER_BASE)
    except Exception:
        pass
    return "", AMINER_BASE


def generate_token():
    """生成 AMiner JWT Token"""
    api_key, _ = _get_aminer_credentials()
    if not api_key:
        return None, None

    # 从 api_key 提取 user_id (JWT payload)
    try:
        decoded = jwt.decode(api_key, options={"verify_signature": False})
        user_id = decoded.get("user_id", "")
    except Exception:
        user_id = ""

    if not user_id:
        # Fallback: use hardcoded user ID from account
        user_id = "6a50f0d66368530ed6f3aef7"

    exp_time = int(time.time()) + 3600
    now_time = int(time.time())
    payload = {"user_id": user_id, "exp": exp_time, "timestamp": now_time}
    headers_jwt = {"alg": "HS256", "sign_type": "SIGN"}

    try:
        token = jwt.encode(payload, api_key, algorithm="HS256", headers=headers_jwt)
        return token, user_id
    except Exception:
        return None, None


def _api_get(endpoint, params=None):
    """调用 AMiner GET API"""
    token, _ = generate_token()
    if not token:
        return {"error": "AMiner API Key 未配置", "success": False}

    url = f"{AMINER_BASE}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)
    req.add_header("Authorization", token)
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "success": False}


def _api_post(endpoint, body):
    """调用 AMiner POST API"""
    token, _ = generate_token()
    if not token:
        return {"error": "AMiner API Key 未配置", "success": False}

    url = f"{AMINER_BASE}/{endpoint}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json;charset=utf-8")
    req.add_header("Authorization", token)

    try:
        resp = urllib.request.urlopen(req, data=data, timeout=20)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "success": False}


# ====== 论文搜索 ======
def search_papers(keyword="", title="", author="", org="", page=0, size=10, order=""):
    """多条件论文搜索"""
    params = {"page": page, "size": size}
    if keyword:
        params["keyword"] = keyword
    if title:
        params["title"] = title
    if author:
        params["author"] = author
    if org:
        params["org"] = org
    if order:
        params["order"] = order
    return _api_get("paper/search/pro", params)


def paper_qa_search(query, size=5):
    """AI 学术问答搜索"""
    return _api_post("paper/qa/search", {"query": query, "size": size})


# ====== 学者搜索 ======
def search_scholars(name, size=10):
    """搜索学者"""
    return _api_post("person/search", {"name": name, "size": size})


def get_scholar_detail(scholar_id):
    """获取学者详情"""
    return _api_get(f"person/detail", {"id": scholar_id})


def get_scholar_papers(scholar_id, size=10):
    """获取学者的论文列表"""
    return _api_get("person/paper_relation", {"id": scholar_id, "size": size})


# ====== 机构搜索 ======
def search_org(name, size=10):
    """搜索机构"""
    return _api_post("org/search", {"name": name, "size": size})


def get_org_detail(org_id):
    """机构详情"""
    return _api_post("org/detail", {"id": org_id})


# ====== 期刊 ======
def search_venue(name, size=10):
    """搜索期刊"""
    return _api_post("venue/search", {"name": name, "size": size})


# ====== 专利 ======
def search_patents(keyword, size=10):
    """搜索专利"""
    return _api_post("patent/search", {"keyword": keyword, "size": size})


# ====== 综合检索（用于 CSIC 文献检索 Tab）=====
def comprehensive_search(query, search_type="all", size=10):
    """
    综合检索：论文 + 学者 + 机构
    search_type: all / paper / scholar / org / patent
    """
    results = {}

    if search_type == "all" or search_type == "paper":
        results["papers"] = search_papers(keyword=query, size=size)

    if search_type == "all" or search_type == "scholar":
        results["scholars"] = search_scholars(query, size=size)

    if search_type == "all" or search_type == "org":
        results["orgs"] = search_org(query, size=size)

    if search_type == "patent":
        results["patents"] = search_patents(query, size=size)

    return results
