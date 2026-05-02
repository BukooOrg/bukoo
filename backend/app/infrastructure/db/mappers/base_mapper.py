"""
Base mapper abstract class for all ORM ↔ domain entity mappers.

Directional Rules
-----------------
Every concrete mapper must strictly follow these two rules. They apply
across the entire project without exception.

READ PATH — to_entity()
    Direction : SQLAlchemy ORM model  →  Domain entity
    Used by   : Repository read methods (get, list, find, etc.)
    Contract  :
        - Maps ALL columns and ALL eagerly loaded (selectin) relationships
          from the ORM model into the entity and its nested child entities.
        - The returned entity is fully hydrated — callers can traverse any
          nested entity (e.g. book.publisher, book.authors[0].author) without
          hitting the database again.
        - This is the ONLY direction that produces resolved relationship
          objects (PublisherEntity, AuthorEntity, etc.).

WRITE PATH — to_model()
    Direction : Domain entity  →  SQLAlchemy ORM model
    Used by   : Repository write methods (save, update, delete, etc.)
    Contract  :
        - Maps ONLY scalar column values and raw FK ID columns.
        - NEVER sets relationship attributes (model.publisher,
          model.category, model.cart_items, etc.).
        - NEVER calls child mappers to produce nested ORM models.
        - SQLAlchemy's session and identity map are solely responsible for
          resolving and persisting relationships. Setting relationship
          attributes on a manually constructed model risks producing
          detached duplicates that conflict with the session's identity map,
          causing DetachedInstanceError or unintended double-inserts.
        - Callers pass the returned model directly to session.add() /
          session.merge() — the session resolves all FKs from there.

Why two separate directions?
    The read path needs a rich object graph for the service and API layers
    to render responses without extra queries. The write path only needs
    the column values the database requires — the ORM handles everything
    else. Conflating the two directions produces either over-fetching on
    writes or under-hydration on reads. Keeping them separate makes each
    path simple, predictable, and safe.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

Model = TypeVar("Model")
Entity = TypeVar("Entity")


class BaseMapper[Model, Entity](ABC):
    @staticmethod
    @abstractmethod
    def to_entity(model: Model) -> Entity:
        """
        READ PATH: Convert a fully loaded SQLAlchemy ORM model into a
        hydrated domain entity. All selectin-loaded relationships must be
        mapped into their corresponding nested entities.
        """
        ...

    @staticmethod
    @abstractmethod
    def to_model(entity: Entity) -> Model:
        """
        WRITE PATH: Convert a domain entity into a SQLAlchemy ORM model
        containing only scalar column values and raw FK ID columns.
        Relationship attributes must NOT be set — the session manages them.
        """
        ...
