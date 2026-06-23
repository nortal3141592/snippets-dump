from __future__ import annotations
from datetime import datetime, UTC

from database import Base

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Table, Column, UniqueConstraint

# junction table
note_tag = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)

    notes: Mapped[list[Note]] = relationship(back_populates="author", cascade="all, delete-orphan")
    tags: Mapped[list[Tag]] = relationship(back_populates="author", cascade="all, delete-orphan")

    image_file: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)

    @property
    def image_path(self):
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    heading: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False, index=True)

    author: Mapped[User] = relationship(back_populates="notes")

    date_created: Mapped[datetime] = mapped_column(DateTime, default= lambda: datetime.now(UTC))
    
    tags: Mapped[list[Tag]] = relationship(secondary=note_tag, back_populates="notes")

class Tag(Base):
    __tablename__ = "tags"

    __table_args__ = (
        UniqueConstraint("tagname", "user_id", name = "uq_tag_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tagname: Mapped[str] = mapped_column(String(50), nullable=False, unique=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False, index=True)

    author: Mapped[User] = relationship(back_populates="tags")

    notes: Mapped[list[Note]] = relationship(secondary=note_tag, back_populates="tags")

