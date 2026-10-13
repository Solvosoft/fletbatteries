import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from fletbatteries.contrib.trash import SoftDeleteMixin

from data.manager.db_base import Base


class Note(SoftDeleteMixin, Base):
    """Nota de la demo: historial, papelera, Markdown, color y ubicación."""

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    content = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    category = Column(String(40), nullable=True)
    location = Column(String(40), nullable=True)
    pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
