from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import FindUserResult, FindUsersCommand
from app.application.use_cases.user.find_users import FindUsersUseCase
from app.core.constants import UserRole, UserStatus
from app.core.query_params import (
    PageParams,
    PaginatedResult,
    QueryParams,
)
from app.domain.entities.user_entity import UserEntity
from app.domain.repositories.user_repository import IUserRepository, UserFilters


def _now() -> datetime:
    return datetime.now(UTC)


def _make_user(
    user_id: str = "user-1",
    email: str = "test@example.com",
    full_name: str = "Test User",
    role: UserRole = UserRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
) -> UserEntity:
    now = _now()
    return UserEntity(
        _id=user_id,
        _email=email,
        _full_name=full_name,
        _date_of_birth=date(1990, 1, 1),
        _role=role,
        _status=status,
        _hashed_password="hashed",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeUserRepository(IUserRepository):
    def __init__(self, users: list[UserEntity] | None = None) -> None:
        self._users = users or []

    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return next((u for u in self._users if u.id == user_id), None)

    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return next((u for u in self._users if u.id == user_id), None)

    async def find_by_email(self, email: str) -> UserEntity | None:
        return next((u for u in self._users if u.email == email), None)

    async def save(self, user: UserEntity) -> None:
        self._users.append(user)

    async def soft_delete(self, user_id: str) -> None:
        pass

    async def exists_by_email(self, email: str) -> bool:
        return any(u.email == email for u in self._users)

    async def count_including_deleted(self) -> int:
        return len(self._users)

    async def find_all(
        self, query: QueryParams, filters: UserFilters
    ) -> PaginatedResult[UserEntity]:
        items = [u for u in self._users if u.deleted_at is None]

        if filters.role is not None:
            items = [u for u in items if u.role == filters.role]
        if filters.status is not None:
            items = [u for u in items if u.status == filters.status]
        if query.search:
            term = query.search.lower()
            items = [
                u
                for u in items
                if term in u.full_name.lower() or term in u.email.lower()
            ]

        total = len(items)
        offset = query.page.offset
        limit = query.page.limit
        page_items = items[offset : offset + limit]

        return PaginatedResult(
            items=page_items,
            total_items=total,
            page=query.page.page,
            page_size=query.page.page_size,
        )


def _default_query(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
) -> QueryParams:
    return QueryParams(
        page=PageParams(page=page, page_size=page_size),
        sorts=[],
        search=search,
    )


@pytest.mark.unit
class TestFindUsersUseCase:
    async def test_returns_all_users_when_no_filters(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[
                _make_user("u1", role=UserRole.USER),
                _make_user("u2", role=UserRole.ADMIN, email="admin@example.com"),
            ]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(), role=None, status=None)
        )

        assert result.total_items == 2
        assert len(result.items) == 2
        assert all(isinstance(u, FindUserResult) for u in result.items)

    async def test_filters_by_role_admin(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[
                _make_user("u1", role=UserRole.USER),
                _make_user("u2", role=UserRole.ADMIN, email="admin@example.com"),
            ]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(), role=UserRole.ADMIN)
        )

        assert result.total_items == 1
        assert result.items[0].role == UserRole.ADMIN

    async def test_filters_by_status_suspended(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[
                _make_user("u1", status=UserStatus.ACTIVE),
                _make_user("u2", status=UserStatus.SUSPENDED, email="s@example.com"),
            ]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(), status=UserStatus.SUSPENDED)
        )

        assert result.total_items == 1
        assert result.items[0].status == UserStatus.SUSPENDED

    async def test_filters_by_role_and_status_combined(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[
                _make_user("u1", role=UserRole.USER, status=UserStatus.ACTIVE),
                _make_user(
                    "u2",
                    role=UserRole.USER,
                    status=UserStatus.SUSPENDED,
                    email="s@example.com",
                ),
                _make_user(
                    "u3",
                    role=UserRole.ADMIN,
                    status=UserStatus.ACTIVE,
                    email="a@example.com",
                ),
            ]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(
                query_params=_default_query(),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
            )
        )

        assert result.total_items == 1
        assert result.items[0].role == UserRole.USER
        assert result.items[0].status == UserStatus.ACTIVE

    async def test_search_by_name(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[
                _make_user("u1", full_name="Jane Doe", email="jane@example.com"),
                _make_user("u2", full_name="John Smith", email="john@example.com"),
            ]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(search="jane"))
        )

        assert result.total_items == 1
        assert result.items[0].full_name == "Jane Doe"

    async def test_search_is_case_insensitive(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[
                _make_user("u1", full_name="Jane Doe", email="jane@example.com"),
            ]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(search="JANE"))
        )

        assert result.total_items == 1

    async def test_returns_empty_when_repository_is_empty(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(users=[])
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(FindUsersCommand(query_params=_default_query()))

        assert result.total_items == 0
        assert result.items == []

    async def test_pagination_page_2_beyond_total(self) -> None:
        db_session = AsyncMock()
        repo = FakeUserRepository(
            users=[_make_user("u1"), _make_user("u2", email="u2@example.com")]
        )
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(page=2, page_size=20))
        )

        assert result.total_items == 2
        assert result.items == []
        assert result.page == 2

    async def test_pagination_metadata(self) -> None:
        db_session = AsyncMock()
        users = [_make_user(f"u{i}", email=f"u{i}@example.com") for i in range(5)]
        repo = FakeUserRepository(users=users)
        use_case = FindUsersUseCase(db_session=db_session, user_repo=repo)

        result = await use_case.execute(
            FindUsersCommand(query_params=_default_query(page=1, page_size=3))
        )

        assert result.total_items == 5
        assert result.page == 1
        assert result.page_size == 3
        assert len(result.items) == 3
