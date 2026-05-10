from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.author_dto import (
    SoftDeleteAuthorCommand,
    SoftDeleteAuthorResult,
)
from app.application.use_cases.author.soft_delete_author import SoftDeleteAuthorUseCase
from app.domain.entities.author_entity import AuthorEntity
from app.domain.exceptions.author import AuthorNotFoundError
from app.domain.repositories.author_repository import IAuthorRepository


def _make_author(author_id: str = "author-001") -> AuthorEntity:
    now = datetime.now(UTC)
    return AuthorEntity(
        _id=author_id,
        _name="George Orwell",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeAuthorRepository(IAuthorRepository):
    def __init__(self, author: AuthorEntity | None = None) -> None:
        self._author: AuthorEntity | None = author
        self._saved: AuthorEntity | None = None

    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        if self._author and self._author.id == author_id:
            return self._author
        return None

    async def save(self, author: AuthorEntity) -> None:
        self._saved = author


@pytest.mark.unit
class TestSoftDeleteAuthorUseCase:
    async def test_returns_success_result(self) -> None:
        db_session = AsyncMock()
        author = _make_author()
        repo = FakeAuthorRepository(author=author)
        use_case = SoftDeleteAuthorUseCase(db_session=db_session, author_repo=repo)
        cmd = SoftDeleteAuthorCommand(author_id=author.id)

        result = await use_case.execute(cmd)

        assert isinstance(result, SoftDeleteAuthorResult)
        assert result.message == "Author deleted successfully."

    async def test_entity_deleted_at_is_set(self) -> None:
        db_session = AsyncMock()
        author = _make_author()
        repo = FakeAuthorRepository(author=author)
        use_case = SoftDeleteAuthorUseCase(db_session=db_session, author_repo=repo)
        cmd = SoftDeleteAuthorCommand(author_id=author.id)

        await use_case.execute(cmd)

        assert repo._saved is not None
        assert repo._saved.deleted_at is not None

    async def test_save_called_with_mutated_entity(self) -> None:
        db_session = AsyncMock()
        author = _make_author()
        repo = FakeAuthorRepository(author=author)
        use_case = SoftDeleteAuthorUseCase(db_session=db_session, author_repo=repo)
        cmd = SoftDeleteAuthorCommand(author_id=author.id)

        await use_case.execute(cmd)

        assert repo._saved is author

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        author = _make_author()
        repo = FakeAuthorRepository(author=author)
        use_case = SoftDeleteAuthorUseCase(db_session=db_session, author_repo=repo)
        cmd = SoftDeleteAuthorCommand(author_id=author.id)

        await use_case.execute(cmd)

        db_session.commit.assert_called_once()

    async def test_raises_author_not_found_when_missing(self) -> None:
        db_session = AsyncMock()
        repo = FakeAuthorRepository(author=None)
        use_case = SoftDeleteAuthorUseCase(db_session=db_session, author_repo=repo)
        cmd = SoftDeleteAuthorCommand(author_id="nonexistent-id")

        with pytest.raises(AuthorNotFoundError):
            await use_case.execute(cmd)
