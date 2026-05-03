# /continue — Resume Incomplete API Endpoint Work

Picks up where work left off on a Bukoo API endpoint — either continuing a proposal still in draft/discussion, or resuming a partial code implementation. Works regardless of whether Claude or the developer started the work.

## Input Format

```
/continue <endpoint_ref>
```

Accepted formats for `<endpoint_ref>`:
- Catalog notation: `1.6`, `4.3`, `11.1`
- Zero-padded: `01_06`, `04_03`
- Description: `auth logout`, `create book`, `place order`

---

## Steps

### 1. Locate the Proposal

Search `.claude/context/api-proposals/` for a file matching the endpoint reference.

- File naming pattern: `[api_set_idx]_[uc_idx]_[use_case_name]_proposal.md`
- If not found → stop and say: "No proposal file found for '[input]'. Run `/propose <endpoint_ref>` to create one first."
- If multiple matches → list them and ask which to continue.

### 2. Read the Proposal

Read the full proposal file. Note the **Status** field and the state of the **Implementation Checklist** (which boxes are ticked).

### 3. Determine Continuation Mode

#### Mode A — Proposal Continuation
**Trigger:** Status = `Draft`

1. Summarize the current state of the proposal: which sections are complete, which are thin or missing.
2. Identify the weakest sections (typically: Procedures, Test Cases, Domain Impact).
3. Ask the user: "The proposal is still in Draft. Here's what's been defined so far: [summary]. What would you like to revise or complete?"
4. Incorporate feedback and iterate exactly as `/propose` does.
5. On user approval, update status to `Approved` and save.

#### Mode B — Implementation Continuation
**Trigger:** Status = `Approved` or `Implemented` (but checklist has unchecked items)

1. Read all context files in parallel:
   - `.claude/context/architecture.md`
   - `.claude/context/domain-model.md`
   - `backend/CLAUDE.md`

2. Audit the codebase against the checklist. For each unchecked step, verify whether the artifact actually exists:

   | Checklist Step | Where to look |
   |----------------|---------------|
   | 1. Domain entity | `app/domain/entities/` |
   | 2. Domain exceptions | `app/domain/exceptions/` |
   | 3. Repository interface | `app/domain/repositories/` |
   | 4. DTOs | `app/application/dtos/` |
   | 5. Use case | `app/application/use_cases/` |
   | 6. ORM model | `app/infrastructure/db/models/` |
   | 7. Mapper | `app/infrastructure/db/mappers/` |
   | 8. Repository implementation | `app/infrastructure/db/repositories/` |
   | 9. Exception mapping | `app/presentation/http/exception_mapper.py` |
   | 10. Error codes | `app/application/errors/error_codes.py` |
   | 11. Pydantic schemas | `app/presentation/schemas/` |
   | 12. Route handler | `app/presentation/api/app_api/v1/` |
   | 13. deps.py wiring | `app/presentation/dependencies/deps.py` |
   | 14. Migration | `backend/migrations/versions/` |
   | 15. Bruno test | `bruno/` |
   | 16. Pytest unit tests | `backend/tests/unit/` |

3. Report the audit result clearly:

   ```
   Implementation audit for: [Use Case Name] ([api_set]_[uc_idx])

   Done  (✓):  Steps 1, 2, 3, 4, 5
   Missing (✗): Steps 6, 7, 8, 9, 10, 11, 12, 13, 15, 16
   Skipped (—): Step 14 (no schema change)

   Next step: Step 6 — ORM model
   ```

4. Ask the user: "Continue from step [N]?" (or proceed automatically if the answer is obvious).

5. Continue implementation from the first incomplete step, following the same layer-order rules as `/implement`:
   - Read any existing file before modifying it
   - Implement the artifact
   - Tick the checklist box in the proposal file

6. After completing all remaining steps, run `make be-check` and fix any errors.

7. Update proposal status to `Implemented` if all 16 steps are now complete.

---

## Special Cases

### Partially Written File (Code Exists But Is Incomplete)

If a file exists but clearly doesn't implement the full requirement (e.g., a stub use case with `pass`, or a route missing the handler body):

1. Read the existing file
2. Identify exactly what's missing relative to the proposal's Procedures
3. Explain what was found vs what's expected
4. Ask: "The file exists but appears incomplete. Should I complete it?"
5. Edit the file in place — don't rewrite from scratch

### Checklist Mismatch (Box Ticked But Code Missing)

If a checklist item is marked `[x]` but the corresponding file is absent or empty:

1. Flag the discrepancy: "Step N is marked complete but I can't find [file/symbol]."
2. Re-implement the step
3. Leave the checkbox ticked (it was likely completed and accidentally lost)

### No Unchecked Items But Status Is Not `Implemented`

All 16 boxes are ticked. Run `make be-check` to confirm no issues, then update status to `Implemented` and report.

---

## Error Handling

- **No proposal file**: Instruct the user to run `/propose <endpoint_ref>` first.
- **Ambiguous match**: List matching proposals and ask the user to confirm.
- **`make be-check` fails on resume**: Fix all errors before reporting done. Document any deliberate suppressions with a comment.
- **Developer-written code that deviates from the proposal**: Point out the difference, ask whether to update the proposal to match the code, or update the code to match the proposal.
