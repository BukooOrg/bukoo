from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.author_dto import (
    ViewAuthorDetailCommand,
    ViewAuthorDetailResult,
)
from app.application.use_cases.author.view_author_detail import ViewAuthorDetailUseCase
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
        self._author = author

    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        if self._author and self._author.id == author_id:
            return self._author
        return None

    async def save(self, author: AuthorEntity) -> None:
        pass


@pytest.mark.unit
class TestViewAuthorDetailUseCase:
    async def test_returns_result_with_correct_fields(self) -> None:
        author = _make_author("author-001")
        repo = FakeAuthorRepository(author=author)
        use_case = ViewAuthorDetailUseCase(db_session=AsyncMock(), author_repo=repo)

        result = await use_case.execute(ViewAuthorDetailCommand(author_id="author-001"))

        assert isinstance(result, ViewAuthorDetailResult)
        assert result.id == "author-001"
        assert result.name == "George Orwell"
        assert isinstance(result.created_at, datetime)

    async def test_raises_not_found_when_repo_returns_none(self) -> None:
        repo = FakeAuthorRepository(author=None)
        use_case = ViewAuthorDetailUseCase(db_session=AsyncMock(), author_repo=repo)

        with pytest.raises(AuthorNotFoundError):
            await use_case.execute(ViewAuthorDetailCommand(author_id="nonexistent-id"))

    async def test_raises_not_found_when_id_does_not_match(self) -> None:
        author = _make_author("author-001")
        repo = FakeAuthorRepository(author=author)
        use_case = ViewAuthorDetailUseCase(db_session=AsyncMock(), author_repo=repo)

        with pytest.raises(AuthorNotFoundError):
            await use_case.execute(ViewAuthorDetailCommand(author_id="author-999"))
