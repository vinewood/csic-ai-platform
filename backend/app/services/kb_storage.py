"""Dify知识库文档管理 — 完整上传/存储/进度追踪"""
import os, uuid, time, json, sqlite3
from datetime import datetime
from pathlib import Path

UPLOAD_BASE = Path("/www/wwwroot/csic.thinkalike.com.cn/uploads/kb_docs")
UPLOAD_BASE.mkdir(parents=True, exist_ok=True)

def save_uploaded_doc(dataset_id: str, filename: str, content: bytes, user_id: str = "") -> dict:
    """保存上传的文档，返回文档信息"""
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{filename}"
    filepath = UPLOAD_BASE / safe_name

    with open(filepath, "wb") as f:
        f.write(content)

    file_size = len(content)
    ext = os.path.splitext(filename)[1].lower()
    word_count = estimate_word_count(content, ext)

    # 存入本地数据库追踪
    conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kb_documents (
            id TEXT PRIMARY KEY, dataset_id TEXT, name TEXT, filepath TEXT,
            file_size INTEGER, file_type TEXT, word_count INTEGER,
            status TEXT DEFAULT 'pending', progress INTEGER DEFAULT 0,
            error TEXT, dify_doc_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Try to insert into Dify DB as well (for worker processing)
    dify_doc_id = insert_to_dify_db(dataset_id, filename, content, word_count)

    conn.execute("""
        INSERT INTO kb_documents (id, dataset_id, name, filepath, file_size, file_type, word_count, status, dify_doc_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ready', ?)
    """, (doc_id, dataset_id, filename, str(filepath), file_size, ext, word_count, "local"))
    conn.commit()
    conn.close()

    return {
        "id": doc_id, "name": filename, "file_size": file_size,
        "word_count": word_count, "status": "indexing" if dify_doc_id else "stored",
        "dify_doc_id": dify_doc_id
    }


def insert_to_dify_db(dataset_id: str, filename: str, content: bytes, word_count: int) -> str:
    """将文档记录插入 Dify PostgreSQL，让 worker 自动处理"""
    import subprocess
    doc_id = str(uuid.uuid4())

    # Get tenant and user IDs
    tenant_id = _pg_query("SELECT id FROM tenants LIMIT 1")
    user_id = _pg_query("SELECT id FROM accounts LIMIT 1")
    if not tenant_id or not user_id:
        return ""

    sql = f"""
    INSERT INTO documents (id, tenant_id, dataset_id, position, data_source_type, data_source_info,
        batch, name, created_from, created_by, word_count, tokens, file_id)
    VALUES ('{doc_id}', '{tenant_id}', '{dataset_id}', 1, 'upload_file',
        '{{"upload_file_id":""}}', 'default', '{filename}', 'web-app', '{user_id}', {word_count}, 0, '{doc_id}')
    """
    try:
        result = subprocess.run(
            ["docker", "exec", "dify-db", "psql", "-U", "postgres", "-d", "dify", "-c", sql],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return doc_id
    except: pass
    return ""


def _pg_query(sql: str) -> str:
    """执行 PostgreSQL 查询返回单个值"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "exec", "dify-db", "psql", "-U", "postgres", "-d", "dify",
             "-t", "-A", "-c", sql],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except: pass
    return ""


def estimate_word_count(content: bytes, ext: str) -> int:
    """估算文档字数"""
    try:
        if ext in ('.txt', '.md'):
            text = content.decode('utf-8', errors='ignore')
            # Count Chinese characters + English words
            import re
            chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
            english = len(re.findall(r'[a-zA-Z]+', text))
            return chinese + english
        return 0
    except: return 0


def get_kb_stats() -> dict:
    """获取知识库统计信息"""
    conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
    try:
        pending = conn.execute("SELECT COUNT(*) FROM kb_documents WHERE status='pending'").fetchone()[0]
        indexing = conn.execute("SELECT COUNT(*) FROM kb_documents WHERE status='indexing'").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM kb_documents WHERE status='completed'").fetchone()[0]
        errored = conn.execute("SELECT COUNT(*) FROM kb_documents WHERE status='error'").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM kb_documents").fetchone()[0]
    except:
        pending = indexing = completed = errored = total = 0
    conn.close()
    return {"total": total, "pending": pending, "indexing": indexing, "completed": completed, "error": errored}


def update_doc_progress():
    """从 Dify DB 同步文档处理进度"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "exec", "dify-db", "psql", "-U", "postgres", "-d", "dify",
             "-t", "-A", "-F", "|||", "-c",
             "SELECT id, indexing_status, completed_at, error FROM documents ORDER BY created_at DESC LIMIT 100"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0: return

        conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
        for line in result.stdout.strip().split("\n"):
            parts = line.split("|||")
            if len(parts) < 2: continue
            doc_id, status, completed_at, error = parts[0], parts[1], parts[2] if len(parts)>2 else "", parts[3] if len(parts)>3 else ""

            csic_status = "completed" if status == "completed" else ("error" if status == "error" else "ready")
            progress = 100 if status == "completed" else (50 if status in ("splitting", "cleaning") else 100)
            conn.execute("""
                UPDATE kb_documents SET status=?, progress=?, error=?, updated_at=CURRENT_TIMESTAMP
                WHERE dify_doc_id=?
            """, (csic_status, progress, error or "", doc_id))
        conn.commit()
        conn.close()
    except: pass


def retrieve_from_kb(query: str, dataset_id: str = "", top_k: int = 5) -> list:
    """从知识库检索相关文档（支持中文关键词匹配）"""
    import sqlite3, os, re
    results = []
    conn = sqlite3.connect("/www/wwwroot/csic.thinkalike.com.cn/data/csic.db")
    
    where = "WHERE status='ready'"
    params = []
    if dataset_id:
        where += " AND dataset_id=?"
        params.append(dataset_id)
    
    docs = conn.execute(
        f"SELECT id, name, filepath FROM kb_documents {where} ORDER BY created_at DESC LIMIT 20", params
    ).fetchall()
    conn.close()

    # Extract Chinese keywords (bigrams) + English keywords
    keywords = set()
    # Chinese: extract 2-char sliding windows
    for i in range(len(query) - 1):
        if '\u4e00' <= query[i] <= '\u9fff' and '\u4e00' <= query[i+1] <= '\u9fff':
            keywords.add(query[i:i+2])
    # English words
    keywords.update(w.lower() for w in re.findall(r'[a-zA-Z]+', query))
    
    if not keywords: keywords.add(query)

    for doc_id, name, filepath in docs:
        if not os.path.exists(filepath): continue
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Count keyword matches
            score = sum(content.lower().count(kw) for kw in keywords if kw in content.lower())
            if score > 0:
                # Find best matching paragraph
                lines = content.replace('\r\n','\n').split('\n')
                best_line, best_score = "", 0
                for line in lines:
                    s = sum(line.lower().count(kw) for kw in keywords)
                    if s > best_score: best_score, best_line = s, line
                
                results.append({
                    "doc_id": doc_id, "name": name, "score": min(score, 100),
                    "snippet": (best_line or content)[:300].strip(),
                    "content": content[:3000]
                })
        except: pass

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
