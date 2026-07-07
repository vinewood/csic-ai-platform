"""Pydantic 请求/响应模型"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


# ---- 认证 ----
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: str = ""
    password: str = "dh24681357"

# ---- 对话 ----
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = ""
    model: Optional[str] = "qwen"
    skill_id: Optional[str] = ""
    kb_id: Optional[str] = ""
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 2048
    files: Optional[list] = None

class ConversationOut(BaseModel):
    id: int
    title: str
    model: str
    messages: list
    created_at: Optional[datetime] = None

# ---- RSS ----
class RssSourceCreate(BaseModel):
    name: str
    url: str
    category: str = "其他"
    ai_enabled: bool = True

class RssSourceOut(BaseModel):
    id: int
    name: str
    url: str
    category: str
    ai_enabled: bool
    active: bool

# ---- 邮箱 ----
class EmailConfigOut(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    from_addr: str
    to_addr: str
    send_time: str
    auto_send: bool

class EmailConfigUpdate(BaseModel):
    smtp_host: Optional[str] = ""
    smtp_port: Optional[int] = 465
    smtp_user: Optional[str] = ""
    smtp_pass: Optional[str] = ""
    from_addr: Optional[str] = ""
    to_addr: Optional[str] = ""
    send_time: Optional[str] = "08:00"
    auto_send: Optional[bool] = False

# ---- API 配置 ----
class ApiConfigUpdate(BaseModel):
    config_json: dict

# ---- 通用 ----
class MessageResponse(BaseModel):
    message: str
    data: Optional[Any] = None
