from datetime import datetime
from enum import Enum
import os
from contextlib import contextmanager

from sqlalchemy import (
    VARCHAR,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "dev")

if not DB_HOST:
    DATABASE_URL = "sqlite:///db.sqlite3"
else:
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
print(DATABASE_URL)
# Create engine and session factory
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    global Base
    Base.metadata.create_all(bind=engine)


# Session factory
SessionFactory = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)

# Scoped session
SessionLocal = scoped_session(SessionFactory)


@contextmanager
def local_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        SessionLocal.remove()


class TranscribeStage(Enum):
    KICKOFF = 0
    SEGMENT = 1
    DRAFT = 2
    GEN_TRANSCRIPT = 3
    FINISH = 4


# Models
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(String, nullable=True)
    pitch_id = Column(Integer, nullable=False)
    document_id = Column(Integer, nullable=False)
    process_stage = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def save(self):
        with local_session() as session:
            try:
                if not self.id:
                    # If instance doesn't have an ID, it's a new record.
                    session.add(self)
                else:
                    session.merge(self)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")

    @classmethod
    def get_by_task_id(cls, task_id):
        with local_session() as session:
            try:
                return session.query(cls).filter_by(task_id=task_id).first()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")

    @classmethod
    def get_by_pitch_id(cls, pitch_id):
        with local_session() as session:
            try:
                return session.query(cls).filter_by(pitch_id=pitch_id).first()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")


class Pitch(Base):
    __tablename__ = "pitches"

    id = Column(Integer, primary_key=True)
    drafts = Column(String, nullable=True)
    transcript = Column(String, nullable=True)
    published = Column(Boolean, nullable=False, default=False)

    def save(self):
        with local_session() as session:
            try:
                if not self.id:
                    # If instance doesn't have an ID, it's a new record.
                    session.add(self)
                else:
                    session.merge(self)
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")

    def get(self):
        with local_session() as session:
            try:
                return session.query(Pitch).filter_by(id=self.id).first()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")

    @classmethod
    def get_by_pitch_id(cls, pitch_id):
        with local_session() as session:
            try:
                return session.query(cls).filter_by(id=pitch_id).first()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    pitch_id = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    master_doc = Column(Boolean, nullable=False, default=False)
    progress = Column(VARCHAR(25), nullable=False, default="0:0")
    processed = Column(Integer, nullable=False, default=0)  # 0, 1

    def save(self):
        with local_session() as session:
            try:
                if not self.id:
                    # If instance doesn't have an ID, it's a new record.
                    session.add(self)
                else:
                    session.merge(self)
                session.commit()
            except Exception as e:
                session.rollback()  # This is essential to reset the session state
                print(f"Error occurred: {e}")

    @classmethod
    def get_by_doc_id(cls, doc_id):
        with local_session() as session:
            try:
                return session.query(cls).filter_by(id=doc_id).first()
            except Exception as e:
                session.rollback()
                print(f"Error occurred: {e}")
