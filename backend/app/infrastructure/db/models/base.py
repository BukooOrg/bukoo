"""
SQLAlchemy declarative base and shared mixins.

Base uses both DeclarativeBase and MappedAsDataclass so that all ORM models
get a generated __init__ from the dataclass machinery. Fields that should not
appear as constructor arguments must declare init=False.

Mixin conventions
-----------------
- TimestampMixin  : created_at, updated_at — server-managed, init=False
- SoftDeleteMixin : deleted_at             — nullable, init=False
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from app.infrastructure.db.util import uuid7_str


class Base(DeclarativeBase, MappedAsDataclass):
    """
    All ORM models inherit from this base.
    DeclarativeBase provides the SQLAlchemy table registry.
    MappedAsDataclass generates __init__, __repr__, __eq__ via dataclass machinery.
    """

    pass


class TimestampMixin:
    """
    Adds created_at and updated_at to any model.
    Both columns are managed by the database server.
    init=False keeps them out of the generated __init__ signature.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        init=False,
    )


class SoftDeleteMixin:
    """
    Adds deleted_at to support soft-deletion.
    NULL means the record is live. A datetime means it has been soft-deleted.
    init=False keeps it out of the generated __init__ signature.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        init=False,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class UuidV7Mixin:
    """
    Adds id as the unique identifier of the model.
    It is generated using uuidV7().
    """

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        insert_default=uuid7_str,
        default_factory=uuid7_str,
        init=False,
    )


class DefaultFieldMixin(Base, TimestampMixin, UuidV7Mixin):
    __abstract__ = True
