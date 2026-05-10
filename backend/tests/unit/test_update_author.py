from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.author_dto import UpdateAuthorCommand, UpdateAuthorResult
from app.application.use_cases.author.update_author import UpdateAuthorUseCase
from app.domain.entities import AuthorEntity
from app.domain.exceptions import AuthorNotFoundError
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

    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        if self._author and self._author.id == author_id:
            return self._author
        return None

    async def save(self, author: AuthorEntity) -> None:
        self.author = author


@pytest.mark.unit
class TestUpdateAuthorUseCase:
    async def test_update_author_successfully(self) -> None:
        author = _make_author("author-001")
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository(author=author)
        use_case = UpdateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        cmd = UpdateAuthorCommand(author_id="author-001", name="George Orwell")

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateAuthorResult)
        assert result.id == "author-001"
        assert result.name == "George Orwell"
        assert isinstance(result.created_at, datetime)
        db_session.commit.assert_called_once()

    async def test_updated_at_bumped(self) -> None:
        author = _make_author("author-001")
        before_update = author.updated_at
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository(author=author)
        use_case = UpdateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        cmd = UpdateAuthorCommand(author_id="author-001", name="George Orwell")

        await use_case.execute(cmd)

        after_update = author.updated_at
        assert after_update >= before_update

    async def test_raises_when_author_not_found(self) -> None:
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository(author=None)

        use_case = UpdateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        cmd = UpdateAuthorCommand(author_id="author-001", name="George Orwell")

        with pytest.raises(AuthorNotFoundError):
            await use_case.execute(cmd)

    async def test_accepts_name_at_max_length(self) -> None:
        author = _make_author("author-001")
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository(author=author)

        use_case = UpdateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        long_name = "A" * 255
        cmd = UpdateAuthorCommand(author_id="author-001", name=long_name)

        result = await use_case.execute(cmd)

        assert result.name == long_name
        assert author_repo.author is not None
