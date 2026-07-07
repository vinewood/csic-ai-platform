"""SQLAlchemy 数据模型 — 完整版 16 张表"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(32), default="user")
    created_at = Column(DateTime, server_default=func.now())
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    topics = relationship("ResearchTopic", back_populates="user", cascade="all, delete-orphan")
    teaching_topics = relationship("TeachingTopic", back_populates="user", cascade="all, delete-orphan")
    video_tasks = relationship("VideoTask", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    title = Column(String(256), default="新对话")
    user_id = Column(Integer, ForeignKey("users.id"))
    model = Column(String(64), default="qwen")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(16), nullable=False)
    content = Column(Text)
    model = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())
    conversation = relationship("Conversation", back_populates="messages")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    type = Column(String(32), default="教学")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    docs = relationship("KnowledgeDoc", back_populates="kb", cascade="all, delete-orphan")


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"
    id = Column(Integer, primary_key=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    title = Column(String(256))
    filename = Column(String(256))
    filepath = Column(String(512))
    content = Column(Text)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    kb = relationship("KnowledgeBase", back_populates="docs")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    category = Column(String(32))
    prompt = Column(Text)
    icon = Column(String(32), default="MagicStick")
    color = Column(String(16), default="#1677ff")
    rating = Column(Float, default=5.0)
    favorited = Column(Boolean, default=False)
    is_preset = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    status = Column(String(32), default="进行中")
    progress = Column(Integer, default=0)
    members_count = Column(Integer, default=1)
    papers_count = Column(Integer, default=0)
    color = Column(String(16), default="#1677ff")
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    user = relationship("User", back_populates="projects")


class ResearchTopic(Base):
    __tablename__ = "research_topics"
    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    description = Column(Text)
    field = Column(String(64))
    feasibility = Column(Integer, default=0)
    innovation = Column(Integer, default=0)
    academic_value = Column(Integer, default=0)
    practical_value = Column(Integer, default=0)
    advice = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="topics")


class TeachingTopic(Base):
    __tablename__ = "teaching_topics"
    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    description = Column(Text)
    level = Column(String(32), default="标准深度")
    hours = Column(Integer, default=4)
    audience = Column(String(128))
    content_outline = Column(Text)
    lecture_script = Column(Text)
    ppt_outline = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="teaching_topics")
    inspirations = relationship("Inspiration", back_populates="topic", cascade="all, delete-orphan")


class Inspiration(Base):
    __tablename__ = "inspirations"
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("teaching_topics.id"))
    type = Column(String(32))
    title = Column(String(256))
    detail = Column(Text)
    adopted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    topic = relationship("TeachingTopic", back_populates="inspirations")


class VideoTask(Base):
    __tablename__ = "video_tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    filename = Column(String(256))
    filepath = Column(String(512))
    status = Column(String(32), default="pending")
    transcript = Column(Text)
    summary = Column(Text)
    flashcards = Column(Text)
    duration = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    user = relationship("User", back_populates="video_tasks")


class RssSource(Base):
    __tablename__ = "rss_sources"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    url = Column(String(512), nullable=False)
    category = Column(String(32), default="其他")
    ai_enabled = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("rss_sources.id"))
    title = Column(String(512))
    url = Column(String(512))
    summary = Column(Text)
    ai_summary = Column(Text)
    category = Column(String(32))
    published = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class EmailConfig(Base):
    __tablename__ = "email_config"
    id = Column(Integer, primary_key=True)
    smtp_host = Column(String(256), default="")
    smtp_port = Column(Integer, default=465)
    smtp_user = Column(String(256), default="")
    smtp_pass = Column(String(256), default="")
    from_addr = Column(String(256), default="")
    to_addr = Column(String(256), default="")
    send_time = Column(String(16), default="08:00")
    auto_send = Column(Boolean, default=False)


class ApiConfig(Base):
    __tablename__ = "api_configs"
    id = Column(Integer, primary_key=True)
    provider = Column(String(64), unique=True, nullable=False)
    config_json = Column(JSON, default=dict)
    updated_at = Column(DateTime, onupdate=func.now())
