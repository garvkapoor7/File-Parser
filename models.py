from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLAEnum
from datetime import datetime
from .database import Base  # import your Base from database.py within the app package

class FileStatus(str, Enum):
    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"

class File(Base):
    __tablename__ = "files"

    file_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(SQLAEnum(FileStatus), default=FileStatus.uploading)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    parsed_content = Column(JSON, nullable=True)
