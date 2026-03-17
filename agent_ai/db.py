"""
db.py
SQLAlchemy ORM model for tracking video pipeline jobs.
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Session

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "pipeline.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


class Base(DeclarativeBase):
    pass


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    topic       = Column(String, nullable=False)
    status      = Column(String, default="pending")   # pending | done | failed

    # content
    title       = Column(Text, default="")
    description = Column(Text, default="")
    story       = Column(Text, default="")
    prompts     = Column(Text, default="[]")          # JSON list of strings

    # file paths
    voice_path  = Column(String, default="")
    segments    = Column(Text, default="[]")          # JSON list of paths
    final_path  = Column(String, default="")

    # which steps are done
    steps_done  = Column(Text, default="[]")          # JSON list

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── helpers ──────────────────────────────────────────────────────────────

    def get_steps(self) -> list:
        return json.loads(self.steps_done or "[]")

    def add_step(self, step: str):
        steps = self.get_steps()
        if step not in steps:
            steps.append(step)
        self.steps_done = json.dumps(steps)
        self.updated_at = datetime.utcnow()

    def has_step(self, step: str) -> bool:
        return step in self.get_steps()

    def get_prompts(self) -> list:
        return json.loads(self.prompts or "[]")

    def set_prompts(self, prompts: list):
        self.prompts = json.dumps(prompts)

    def get_segments(self) -> list:
        return json.loads(self.segments or "[]")

    def set_segments(self, paths: list):
        self.segments = json.dumps(paths)

    def pending_steps(self) -> list:
        all_steps = ["content", "voice", "segments", "combine", "merge"]
        done = self.get_steps()
        return [s for s in all_steps if s not in done]

    def __repr__(self):
        return f"<VideoJob id={self.id} topic={self.topic!r} status={self.status} steps={self.get_steps()}>"


# ── DB init & helpers ─────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def get_pending_job() -> VideoJob | None:
    """Return the most recent pending job, if any."""
    with get_session() as s:
        return (
            s.query(VideoJob)
            .filter(VideoJob.status == "pending")
            .order_by(VideoJob.updated_at.desc())
            .first()
        )
