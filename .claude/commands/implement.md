# /implement — API Endpoint Implementation

Implements an approved API endpoint proposal for the Bukoo backend, following the Clean Architecture 16-step sequence. Writes all code layers, Bruno test, and pytest unit tests. Runs quality checks before reporting done.

## Input Format

```
/implement <proposal_ref>
```

Accepted formats for `<proposal_ref>`:

- File name: `01_06_log_out_proposal.md`
- Catalog notation: `1.6`, `4.3`
- Description: `auth logout`, `create book`

---

## Steps

### 1. Locate the Proposal

Search `.claude/context/api-proposals/` for a file matching the input. If multiple files match, list them and ask the user to confirm which one.

If no file is found, tell the user and suggest running `/propose <endpoint_ref>` first.

### 2. Read Context (in parallel)

- The proposal file
- `.claude/context/architecture.md`
- `.claude/context/domain-model.md`
- `backend/CLAUDE.md`
- Any existing files that will be modified (e.g., `deps.py`, `exception_mapper.py`, the relevant route file)

### 3. Check Proposal Status

- If status = `Draft` → **stop**. Tell the user the proposal is not yet approved. Ask them to review it and use `/propose` to finalize it first.
- If status = `Approved` or `Implemented` → proceed.

### 4. Implement in Layer Order

Work through all 16 checklist items **in sequence**. Never skip steps or reorder them — layer dependencies require inner layers to exist before outer ones import them.

For each step:

1. Read any existing file that will be modified first
2. Write or edit the code
3. Tick the checklist box in the proposal file (`[ ]` → `[x]`)

**Layer sequence:**

#### Steps 1–2: Domain Layer

- **Entity** (`app/domain/entities/<name>_entity.py`): Only add if new. Use `@dataclass`, private `_field` names, `@property` getters, `str(uuid7())` for IDs, `datetime.now(UTC)` for timestamps.
- **Exceptions** (`app/domain/exceptions/<group>.py`): Only add if new. Inherit `DomainException`. No HTTP imports.

#### Step 3: Repository Interface

- Add method signature to `app/domain/repositories/<name>_repository.py`. Method signatures use domain entities, never ORM models.

#### Step 4: DTOs / Service Interfaces

- Add frozen `@dataclass` command and result types to `app/application/dtos/<name>_dto.py`.
- Add service interfaces to `app/application/interfaces/` only if an external service is needed.

#### Step 5: Use Case

- Create `app/application/use_cases/<group>/<action>.py`.
- Inherit `BaseUseCase`. Accept `db_session: AsyncSession` in `__init__`.
- Depend only on repository interfaces, never implementations.
- Call `await self._db_session.commit()` explicitly after mutations.
- Raise domain exceptions only — never `HTTPException`.

#### Steps 6–7: ORM Model + Mapper

- Only add if a new DB table is required.
- Model: inherit `DefaultFieldMixin` (adds `id`, `created_at`, `updated_at`). Add `SoftDeleteMixin` for soft-deletable tables.
- **CRITICAL**: Import the new model in `backend/migrations/env.py` or Alembic won't detect it.
- Mapper: inherit `BaseMapper[ModelType, EntityType]`. Static `to_entity()` and `to_model()` methods.

#### Step 8: Repository Implementation

- Add method to `app/infrastructure/db/repositories/<name>_repository_impl.py`.
- Always filter `Model.deleted_at.is_(None)` unless explicitly fetching deleted records.
- Never call `session.commit()` in repos — commit belongs in the use case.

#### Step 9: Exception Mapping

- Add any new domain exceptions to the `EXCEPTION_MAP` dict in `app/presentation/http/exception_mapper.py`.
- Map to `(HTTP status code, ErrorCode)` tuple.

#### Step 10: Error Codes

- Add new constants to `app/application/errors/error_codes.py`.

#### Step 11: Pydantic Schemas

- Add request and response schemas to `app/presentation/schemas/<group>_schema.py` (or create a new file if this is the first schema for this domain group).
- Response schema must match the `data` field shape shown in the proposal.

#### Step 12: Route Handler

- Add route to `app/presentation/api/app_api/v1/<group>_routes.py`.
- Use typed dependency aliases from `deps.py` (e.g., `CurrentUser`, `AdminUser`, `UserRepo`).
- Instantiate the use case with injected dependencies inside the handler.
- Return the Pydantic response schema — the `ResponseFormatterMiddleware` wraps it in the envelope automatically.

#### Step 13: Wire in `deps.py`

- Add provider function and typed `Annotated` alias to `app/presentation/dependencies/deps.py`.
- This is the **only** place that imports from both `application/` and `infrastructure/` simultaneously.

#### Step 14: Alembic Migration

- Only run if a new ORM model or schema change was made.
- Run `make migrate msg="<descriptive message>"` and review the generated file.
- Do NOT run `make upgrade` automatically — leave that for the developer to run manually.

#### Step 15: Bruno Test File

- Create `bruno/<api_set_folder>/<use_case_name>.bru`.
- Follow the exact `.bru` format: `meta`, HTTP method block, `headers`, `body:json` (if applicable), `script:post-response` (if token extraction needed), `tests` block.
- Implement all test cases listed in the proposal's Bruno Tests section.
- Use `{{baseUrl}}{{apiBase}}` for URLs, `{{token}}` for auth headers.

#### Step 16: Pytest Unit Tests

- Create `backend/tests/unit/test_<use_case_name>.py`.
- Use the `@pytest.mark.unit` marker.
- Fake repos: create in-memory classes that implement the same ABC interface, stored as local test fixtures or conftest.
- Test pattern: instantiate the use case with fake repos, call `execute()`, assert the result or exception.
- Use `async def test_*()` — asyncio_mode is `auto` in `pytest.ini`.
- Cover all test cases listed in the proposal's Pytest section.

### 5. Run Quality Checks

After all 16 steps are complete, run:

```bash
make be-check
```

Fix all ruff lint, format, and mypy errors before reporting done. Do not skip or suppress errors without a documented reason.

### 6. Update Proposal Status

Edit the proposal file: change `Status: Approved` → `Status: Implemented`.

### 7. Report Summary

Output a summary listing:

- Files created (new)
- Files modified (existing)
- Checklist completion (16/16 ✓ or partial)
- Any steps skipped and why (e.g., "Step 6–7 skipped: no new ORM model needed")
- Any remaining manual steps (e.g., "Run `make upgrade` to apply migration")

---

## Bruno File Format Reference

```bru
meta {
  name: [Human Readable Name]
  type: http
  seq: [sequence number within folder]
}

[get|post|patch|put|delete] {
  url: {{baseUrl}}{{apiBase}}/[path]
  body: [none|json|multipart-form]
  auth: [none|bearer]
}

auth:bearer {
  token: {{token}}
}

headers {
  Content-Type: application/json
}

body:json {
  {
    "field": "value"
  }
}

script:post-response {
  if (res.status === 200) {
    bru.setEnvVar("token", res.body.data.access_token);
  }
}

tests {
  test("status 200", function() {
    expect(res.status).to.equal(200);
  });

  test("success flag", function() {
    expect(res.body.success).to.be.true;
  });

  test("data field present", function() {
    expect(res.body.data).to.have.property("field");
  });

  test("meta has requestId", function() {
    expect(res.body.meta.requestId).to.be.a("string");
  });
}
```

---

## Pytest Unit Test Structure Reference

```python
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from app.application.dtos.[name]_dto import [Name]Command, [Name]Result
from app.application.use_cases.[group].[action] import [UseCaseName]
from app.domain.exceptions.[group] import [DomainException]


class Fake[Name]Repository:
    """In-memory implementation of I[Name]Repository for unit tests."""

    def __init__(self) -> None:
        self._store: dict[str, [Entity]] = {}

    async def find_by_id(self, id: str) -> [Entity] | None:
        return self._store.get(id)

    async def save(self, entity: [Entity]) -> [Entity]:
        self._store[entity.id] = entity
        return entity


@pytest.mark.unit
class Test[UseCaseName]:

    async def test_[happy_path_scenario](self) -> None:
        # Arrange
        db_session = AsyncMock()
        repo = Fake[Name]Repository()
        use_case = [UseCaseName](db_session=db_session, [name]_repo=repo)
        command = [Name]Command([fields])

        # Act
        result = await use_case.execute(command)

        # Assert
        assert isinstance(result, [Name]Result)
        assert result.[field] == expected_value
        db_session.commit.assert_called_once()

    async def test_raises_[exception]_when_[condition](self) -> None:
        # Arrange
        db_session = AsyncMock()
        repo = Fake[Name]Repository()  # empty — entity not found
        use_case = [UseCaseName](db_session=db_session, [name]_repo=repo)
        command = [Name]Command([fields])

        # Act / Assert
        with pytest.raises([DomainException]):
            await use_case.execute(command)
```

---

## Error Handling

- **Proposal not found**: Tell the user and suggest `/propose <endpoint_ref>`.
- **Proposal status is Draft**: Stop and instruct the user to approve the proposal first via `/propose`.
- **`make be-check` fails**: Fix all errors in-place. If an error requires a deliberate suppression (e.g., a known ruff rule listed in `.ruff.toml`), document why in a comment.
- **Migration already exists**: Read the existing migration file before generating a new one. Only create a new migration if the change is genuinely new.
