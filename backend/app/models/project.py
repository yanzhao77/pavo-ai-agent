import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Enum as SAEnum
import enum
from app.db.database import Base


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), default="", index=True)
    title = Column(String(255), default="")
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    input_raw = Column(Text, default="")
    input_extracted = Column(JSON, default=dict)
    characters = Column(JSON, default=list)
    scenes = Column(JSON, default=list)
    props = Column(JSON, default=list)
    storyboard = Column(JSON, default=dict)
    videos = Column(JSON, default=list)
    task_ids = Column(JSON, default=list)  # Async task IDs for video generation
    version = Column(String(20), default="1.0")
    trace_log = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VersionHistory(Base):
    """Track project version history for undo/redo."""
    __tablename__ = "version_history"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), index=True)
    version_number = Column(Integer, default=1)
    snapshot = Column(JSON, default=dict)
    description = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """User feedback on generated content."""
    __tablename__ = "feedback"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), index=True)
    user_id = Column(String(64), default="")
    rating = Column(String(10), default="")  # "up" | "down"
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
