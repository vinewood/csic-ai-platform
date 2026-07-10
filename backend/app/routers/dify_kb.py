"""
Dify API 代理 — 数据集列表通过 docker exec 查询
解决 plugin-daemon 不可用和 Postgres 端口未映射的问题
"""
import json, time, subprocess
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
import httpx
from ..auth import get_current_user

router = APIRouter(prefix="/api/dify", tags=["Dify集成"])

DIFY_CONSOLE = "http://127.0.0.1:5001/console/api"
DIFY_LOGIN = {"email": "admin@csic.cn", "password": "***REMOVED-PASSWORD***"}
_token_cache = {"token": "", "expires": 0}

async def _dify_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{DIFY_CONSOLE}/login", json=DIFY_LOGIN)
        if r.status_code == 200:
            token = r.json().get("data", {}).get("access_token", "")
            if token:
                _token_cache["token"] = token
                _token_cache["expires"] = time.time() + 3000
                return token
    return ""

async def _dify_api(method: str, path: str, json_data=None, files=None, params=None) -> dict:
    token = await _dify_token()
    if not token:
        raise HTTPException(status_code=502, detail="Dify 服务未初始化")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{DIFY_CONSOLE}{path}"
    async with httpx.AsyncClient(timeout=60) as c:
        if method == "GET":
            r = await c.get(url, headers=headers, params=params)
        elif files:
            r = await c.post(url, headers={"Authorization": f"Bearer {token}"}, files=files, data=json_data or {})
        else:
            headers["Content-Type"] = "application/json"
            r = await c.post(url, headers=headers, json=json_data)
        if r.status_code < 400:
            return r.json()
        raise HTTPException(status_code=r.status_code, detail=r.text[:200])

def _dify_db_query(sql: str) -> list:
    """通过 docker exec 直接查询 Dify PostgreSQL"""
    try:
        result = subprocess.run(
            ["docker", "exec", "dify-db", "psql", "-U", "postgres", "-d", "dify",
             "-t", "-A", "-F", "|||", "-c", sql],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0: return []
        lines = [l for l in result.stdout.strip().split("\n") if l.strip() and "|||" in l]
        return lines
    except: return []

# ===================== 数据集列表（DB直查） =====================

@router.get("/datasets")
async def list_datasets(page: int = 1, limit: int = 30, current_user: dict = Depends(get_current_user)):
    """列出 Dify 数据集"""
    # Try API first
    try:
        return await _dify_api("GET", "/datasets", params={"page": page, "limit": limit})
    except HTTPException:
        pass

    # DB fallback
    total = 0
    datasets = []
    try:
        lines = _dify_db_query(
            f"SELECT d.id, d.name, COALESCE(d.description,''), d.permission, "
            f"d.indexing_technique, d.embedding_model, "
            f"d.embedding_model_provider, COUNT(doc.id) as doc_count "
            f"FROM datasets d LEFT JOIN documents doc ON doc.dataset_id = d.id "
            f"GROUP BY d.id ORDER BY d.created_at DESC LIMIT {limit} OFFSET {(page-1)*limit}"
        )
        for line in lines:
            parts = line.split("|||")
            if len(parts) >= 5:
                datasets.append({
                    "id": parts[0], "name": parts[1], "description": parts[2] or "",
                    "permission": parts[3], "document_count": int(parts[7]) if len(parts) > 7 and parts[7].strip().lstrip("-").isdigit() else 0,
                    "word_count": 0,
                    "indexing_technique": parts[4] if len(parts) > 4 else "",
                    "embedding_model": parts[5] if len(parts) > 5 else "",
                    "embedding_model_provider": parts[6] if len(parts) > 6 else "",
                })
        t = _dify_db_query("SELECT COUNT(*) FROM datasets")
        total = int(t[0]) if t and t[0].isdigit() else len(datasets)
    except: pass

    return {"data": datasets, "total": total}


# ===================== 创建数据集 =====================

@router.post("/datasets/create")
async def create_dataset(name: str = Query(...), description: str = Query(""), current_user: dict = Depends(get_current_user)):
    return await _dify_api("POST", "/datasets", json_data={"name": name, "description": description})


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user: dict = Depends(get_current_user)):
    return await _dify_api("DELETE", f"/datasets/{dataset_id}")


# ===================== 文档管理 =====================

@router.get("/datasets/{dataset_id}/documents")
async def list_documents(dataset_id: str, page: int = 1, limit: int = 30, current_user: dict = Depends(get_current_user)):
    """列出数据集文档（DB直查）"""
    docs = []
    try:
        lines = _dify_db_query(
            f"SELECT id, name, indexing_status, file_size, word_count, "
            f"segment_count, display_status "
            f"FROM documents WHERE dataset_id='{dataset_id}' "
            f"ORDER BY created_at DESC LIMIT {limit} OFFSET {(page-1)*limit}"
        )
        for line in lines:
            parts = line.split("|||")
            if len(parts) >= 5:
                docs.append({
                    "id": parts[0], "name": parts[1],
                    "indexing_status": parts[2] if parts[2] != "\\N" else "waiting",
                    "file_size": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                    "word_count": int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                    "segment_count": int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0,
                    "display_status": parts[6] if len(parts) > 6 and parts[6] != "\\N" else "",
                })
    except: pass
    return {"data": docs}


@router.post("/datasets/{dataset_id}/documents/upload")
async def upload_document(dataset_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """上传文档到 Dify 数据集"""
    token = await _dify_token()
    content = await file.read()
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            f"{DIFY_CONSOLE}/datasets/{dataset_id}/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (file.filename or "doc", content, "application/octet-stream")},
            data={"data_source": "upload_file"}
        )
        if r.status_code < 400:
            data = r.json()
            # 标记需要启动 worker 处理
            return {"id": data.get("id", ""), "name": file.filename, "status": "uploaded", "note": "Dify worker 正在处理中"}
        raise HTTPException(status_code=500, detail=f"上传失败: {r.text[:200]}")


@router.delete("/datasets/{dataset_id}/documents/{doc_id}")
async def delete_document(dataset_id: str, doc_id: str, current_user: dict = Depends(get_current_user)):
    return await _dify_api("DELETE", f"/datasets/{dataset_id}/documents/{doc_id}")


# ===================== 简化列表 =====================

@router.get("/datasets/list")
async def datasets_simple(current_user: dict = Depends(get_current_user)):
    items = []
    try:
        lines = _dify_db_query("SELECT d.id, d.name, COUNT(doc.id) FROM datasets d LEFT JOIN documents doc ON doc.dataset_id = d.id GROUP BY d.id ORDER BY d.created_at DESC LIMIT 50")
        for line in lines:
            parts = line.split("|||")
            if len(parts) >= 3:
                items.append({"id": parts[0], "name": parts[1], "count": int(parts[2]) if parts[2].isdigit() else 0})
    except: pass
    return items


@router.get("/health")
async def dify_health():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("http://127.0.0.1:5001/health")
            return {"status": "ok", "API": "ok" if r.status_code < 500 else "error"}
    except:
        return {"status": "error", "API": "offline"}


@router.post("/init")
async def dify_init(current_user: dict = Depends(get_current_user)):
    """重新执行 Dify 初始化"""
    token, account_ok, setup_ok = "", False, False
    
    # 1. Check current state
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{DIFY_CONSOLE}/login", json=DIFY_LOGIN)
            if r.status_code == 200 and r.json().get("data", {}).get("access_token"):
                return {"message": "Dify 已初始化并可正常登录", "status": "ok"}
    except: pass

    # 2. Try API init
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{DIFY_CONSOLE}/init", json={
                "email": "admin@csic.cn", "name": "Admin", "password": "***REMOVED-PASSWORD***"
            })
            init_ok = r.status_code == 200 and r.json().get("result") == "success"
    except: init_ok = False

    return {
        "message": "Dify 初始化已触发" if init_ok else "请手动访问 Dify 控制台完成初始化",
        "status": "init_triggered" if init_ok else "needs_manual",
        "url": "https://csic.thinkalike.com.cn/dify/",
        "credentials": {"email": "admin@csic.cn", "password": "***REMOVED-PASSWORD***"}
    }
