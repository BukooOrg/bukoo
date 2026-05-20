# Frontend Feature Set Development Lifecycle

This document outlines the step-by-step process for developing any frontend feature set.
Follow this lifecycle for each new set of features.

## Phase 0: Brainstorming

1. **Load the brainstorming skill** — explore user intent, requirements, and design tradeoffs
2. **Clarify scope** — confirm with the user what "done" looks like for this feature set
3. **Identify edge cases** — discuss error states, empty states, loading states, permission boundaries

## Phase 1: Discovery & Context

1. **Read project context**
   - Read `CLAUDE.md` (root), `frontend/CLAUDE.md`
   - Read `.claude/context/project-context.md` for feature status
   - Read `.claude/context/architecture.md` for patterns
   - Read `.claude/context/api-endpoint-catalog.md` for available endpoints
   - Read `.claude/context/domain-model.md` for entity relationships

2. **Identify related GitHub issues**
   - List open issues matching the feature set
   - Note issue numbers for later (closing in PR)
   - Read issue descriptions for requirements

3. **Audit existing code**
   - Check if any pages, components, or tests already exist
   - Verify SDK methods are generated (`sdk/javascript-client/src/apis/`)
   - Confirm `apiClient.js` has the needed API instances

4. **Check backend readiness**
   - Verify the corresponding backend endpoints exist and are implemented
   - Check backend route handlers, use cases, and schemas
   - Confirm API response shapes match what the frontend expects
   - If backend is not ready, inform the user and pause

5. **Present proposal to user**
   - Summarize what will be built (pages, components, routes, tests)
   - List which issues will be addressed
   - Note any gaps, tradeoffs, or questions
   - **Do NOT create any files yet — wait for user approval**

## Phase 2: Design Review

1. **Load the ui-ux-pro-max skill** — apply UI/UX best practices
2. **Review component design** — check against design system guidelines
3. **Validate accessibility** — ensure keyboard nav, ARIA labels, contrast
4. **Check responsive behavior** — mobile, tablet, desktop breakpoints

## Phase 3: Implementation

After user approves the proposal:

1. **Load the frontend-design skill** — build production-grade components
2. **Load the vercel-react-best-practices skill** — apply modern React patterns
3. **Create pages** — route-level components in `src/pages/<feature>/`
4. **Create components** — reusable UI in appropriate `src/components/` subdirectories
5. **Register routes** — add `<Route>` entries in `src/App.jsx`
6. **Wire navigation** — update layout nav menus (AdminLayout, StorefrontLayout, etc.)
7. **Connect to API** — use `@bukoo/api-client` via `src/lib/apiClient.js` instances

**Rules:**
- Use the generated SDK client — never raw `fetch()` for new API calls
- Follow existing patterns (cva variants, cn() class merging, sonner toasts)
- Use React Hook Form + Zod for forms
- Keep components under 300 lines where possible

## Phase 4: Testing

1. **Write component/integration tests**
   - Place test files alongside pages: `PageName.test.jsx`
   - Mock `@/lib/apiClient` and `react-router-dom` hooks
   - Test rendering, user interactions, API calls, error states, edge cases
   - Aim for comprehensive coverage of all user flows

2. **Run all tests**
   - `pnpm vitest run src/pages/<feature>/` — verify new tests pass
   - `make fe-check` — ESLint + Prettier must be clean
   - Fix any failures before proceeding

## Phase 5: User Review & Iteration

1. **Let the user test** — the frontend dev server should be running
2. **Expect feedback** — the user will find bugs, request UI changes, report missing features
3. **Iterate quickly** — make changes, re-run tests, let the user re-test
4. **This phase may have multiple cycles** — do not skip it

**Important:** Do not proceed to Phase 6 until the user confirms the feature is ready.

## Phase 6: Finalize & Ship

1. **Run full test suite**
   - `make test-unit` — backend unit tests
   - `make be-check` — backend lint + typecheck
   - `pnpm vitest run` — all frontend tests
   - `make fe-check` — frontend lint + format

2. **Commit changes**
   - Use conventional commit format: `type(scope): subject`
   - Include comprehensive commit message describing what was built
   - Reference feature set number and issue numbers

3. **Push and create PR**
   - Push branch to `origin`
   - Create PR targeting `main` with `gh pr create`
   - Include summary, test counts, and issue references in PR body

4. **Close related issues**
   - Close each related issue with `gh issue close <num> --comment "Completed in PR #<num>"`
   - Link issues to PR if not auto-closed by keywords

## Questions to Ask the User

At each phase, ask the user:
- **Phase 0:** "What does success look like for this feature? Any specific requirements or constraints?"
- **Phase 1:** "Does this proposal look right? Any changes before I start building?"
- **Phase 4:** "Tests are passing. Ready for you to review the feature?"
- **Phase 5:** "Does everything look good? Any changes needed before I finalize?"
- **Phase 6:** "Ready to commit, push, and create the PR?"

**Never assume. Always confirm with the user before proceeding to the next phase.**
