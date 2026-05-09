from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.dtos.author_dto import CreateAuthorCommand, CreateAuthorResult
from app.application.use_cases.author.create_author import CreateAuthorUseCase
from app.domain.entities import AuthorEntity
from app.domain.repositories.author_repository import IAuthorRepository


class FakeAuthorRepository(IAuthorRepository):
    def __init__(self) -> None:
        self._saved: AuthorEntity | None = None

    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        return None

    async def save(self, author: AuthorEntity) -> None:
        self._saved = author


@pytest.mark.unit
class TestCreateAuthorUseCase:
    async def test_creates_author_successfully(self) -> None:
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository()
        use_case = CreateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        cmd = CreateAuthorCommand(name="Fyodor Dostoevsky")

        result = await use_case.execute(cmd)

        assert isinstance(result, CreateAuthorResult)
        assert result.name == "Fyodor Dostoevsky"
        assert isinstance(result.id, str) and len(result.id) > 0
        db_session.commit.assert_called_once()

    async def test_result_id_is_non_empty_string(self) -> None:
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository()
        use_case = CreateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        cmd = CreateAuthorCommand(name="Leo Tolstoy")

        result = await use_case.execute(cmd)

        assert len(result.id) > 0

    async def test_accepts_name_at_max_length(self) -> None:
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository()
        use_case = CreateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        long_name = "A" * 255
        cmd = CreateAuthorCommand(name=long_name)

        result = await use_case.execute(cmd)

        assert result.name == long_name
        assert author_repo._saved is not None

    async def test_preserves_whitespace_in_name(self) -> None:
        db_session = AsyncMock()
        author_repo = FakeAuthorRepository()
        use_case = CreateAuthorUseCase(db_session=db_session, author_repo=author_repo)
        cmd = CreateAuthorCommand(name="  Gabriel García Márquez  ")

        result = await use_case.execute(cmd)

        assert result.name == "  Gabriel García Márquez  "
