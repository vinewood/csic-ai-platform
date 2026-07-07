"""
中船党校 AI 平台 - 后端集成测试
运行: python -m pytest backend/tests/test_api.py -v
"""

import pytest
import httpx
from httpx_sse import connect_sse

BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=30)


@pytest.fixture
def token(client):
    """登录获取 token"""
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "dh24681357"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestHealth:
    """健康检查"""
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuth:
    """认证测试"""
    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "dh24681357"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == "admin"

    def test_login_fail(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrong"
        })
        assert resp.status_code == 401

    def test_me(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200

    def test_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestChat:
    """对话测试"""
    def test_models(self, client):
        resp = client.get("/api/chat/models")
        assert resp.status_code == 200
        models = resp.json()["models"]
        assert len(models) == 6
        model_ids = [m["id"] for m in models]
        assert "qwen" in model_ids
        assert "deepseek" in model_ids

    def test_unauthorized(self, client):
        resp = client.post("/api/chat/stream", json={"query": "test"})
        assert resp.status_code == 401


class TestUsers:
    """用户管理测试"""
    def test_list_users(self, client, auth_headers):
        resp = client.get("/api/users", headers=auth_headers)
        assert resp.status_code == 200
        users = resp.json()
        assert isinstance(users, list)

    def test_create_and_delete(self, client, auth_headers):
        # 创建测试用户（使用随机名避免冲突）
        import random
        uid = f"testuser{random.randint(1000,9999)}"
        resp = client.post("/api/users", headers=auth_headers, json={
            "username": uid,
            "email": f"{uid}@csic.cn",
            "password": "dh24681357"
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "用户已创建"

        # 重复创建应失败
        resp = client.post("/api/users", headers=auth_headers, json={
            "username": uid,
            "email": f"{uid}2@csic.cn",
        })
        assert resp.status_code == 400


class TestRSS:
    """RSS 管理测试"""
    def test_list_sources(self, client):
        resp = client.get("/api/rss/sources")
        assert resp.status_code == 200

    def test_create_source(self, client, auth_headers):
        resp = client.post("/api/rss/sources", headers=auth_headers, json={
            "name": "测试源",
            "url": "https://rsshub.app/test",
            "category": "科技",
            "ai_enabled": True
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "新闻源已添加"

    def test_list_articles(self, client):
        resp = client.get("/api/rss/articles")
        assert resp.status_code == 200


class TestEmail:
    """邮箱配置测试"""
    def test_get_config(self, client):
        resp = client.get("/api/email/config")
        assert resp.status_code == 200

    def test_update_config(self, client, auth_headers):
        resp = client.put("/api/email/config", headers=auth_headers, json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 465,
            "smtp_user": "test@example.com",
            "from_addr": "test@example.com",
            "to_addr": "admin@csic.cn",
        })
        assert resp.status_code == 200


class TestFiles:
    """文件上传测试"""
    def test_upload_unauthorized(self, client):
        resp = client.post("/api/files/upload")
        assert resp.status_code == 401

    def test_upload(self, client, auth_headers):
        resp = client.post("/api/files/upload", headers=auth_headers, files={
            "file": ("test.txt", b"hello world", "text/plain")
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "url" in data
        assert data["size"] == 11


class TestConfig:
    """API 配置测试"""
    def test_get_config(self, client):
        resp = client.get("/api/config/aminer")
        assert resp.status_code == 200

    def test_update_config(self, client, auth_headers):
        resp = client.put("/api/config/aminer", headers=auth_headers, json={
            "config_json": {"key": "test-key", "baseUrl": "https://api.aminer.cn"}
        })
        assert resp.status_code == 200
