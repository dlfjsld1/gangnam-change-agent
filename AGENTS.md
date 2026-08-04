# AGENTS.md

This file contains only the routing, ownership, safety, and completion rules needed on every task.
Product details, decisions, contracts, implementation status, and detailed collaboration procedures live under `docs/`.

## 1. Required reading order

Before changing code or shared documents, read:

1. `AGENTS.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/DECISIONS.md`
4. Relevant files under `docs/contracts/`
5. The Work log mapped to the current branch or code area

Use these sources for their assigned purpose:

- `docs/PROJECT_CONTEXT.md`: current product, architecture, privacy boundary, and MVP scope
- `docs/DECISIONS.md`: accepted cross-team decisions and rationale
- `docs/contracts/`: shared API, JSON Schema, matching, and fixture contracts
- `docs/worklogs/`: responsible area's current status, next actions, dependencies, and history
- `docs/TEAM_CODEX_SYNC_CONTEXT.md`: detailed collaboration, implementation, validation, and deployment procedures

Do not treat `docs/archive/` as the current specification.
If documents conflict, prefer accepted decisions and current contracts, then report and correct the stale document.

## 2. Branch, code area, and Work log mapping

| Branch | Owned code | Work log |
|---|---|---|
| `feat/agent-backend` | `backend/**` | `docs/worklogs/agent-backend/WORKLOG.md` |
| `feat/citizen-pwa` | `frontend/citizen/**` | `docs/worklogs/citizen-pwa/WORKLOG.md` |
| `feat/admin-integration` | `frontend/admin/**`, `infra/**` | `docs/worklogs/admin-integration/WORKLOG.md` |

Shared areas:

- `docs/contracts/**`: cross-team contract
- `demo-data/**`: shared demo and validation fixtures
- `docs/PROJECT_CONTEXT.md` and `docs/DECISIONS.md`: cross-team product truth
- `main`: stable, demo-ready integration branch

Use the branch first and the changed code area second to identify ownership.
When they disagree, stop and resolve the mismatch before editing.

## 3. Ownership boundaries

- Work primarily inside the current branch owner's code area.
- Do not make large changes in another owner's area without agreement.
- Do not select or complete another teammate's Work log actions.
- Keep API access, deterministic matching, UI, Agent logic, and deployment responsibilities in their mapped areas.
- Avoid unrelated refactoring, formatting, or cleanup.
- Preserve working fallback behavior unless the requested change replaces it.
- Shared fixture edits must remain compatible with the schemas that validate them.
- A helper contribution does not transfer ownership of the affected area.

## 4. Shared schema and API change procedure

Before implementing a change to shared payloads, API paths, fields, enums, matching behavior, or review states:

1. Identify every affected owner and consumer.
2. Record the accepted cross-team decision in `docs/DECISIONS.md` when behavior or architecture changes.
3. Update the relevant file under `docs/contracts/` before dependent code.
4. Prefer additive optional fields over breaking changes.
5. Update representative fixtures under `demo-data/` when applicable.
6. Validate schema syntax, `$ref` resolution, fixtures, and recursive structures where relevant.
7. Notify affected owners through the shared document commit.
8. Let each owner update their implementation and Work log after pulling the contract change.

Do not rename or remove shared fields independently in one frontend or backend implementation.
Do not publish a package that is unapproved or lacks required evidence.

## 5. Work log rules

- Read the mapped Work log before implementation.
- Keep `Current status` aligned with the actual repository.
- Keep `Next actions` ordered and mark an item complete only after its Completion criteria pass.
- Record blockers and cross-team dependencies explicitly.
- After meaningful implementation work, update the responsible Work log's status and Change history.
- Record only tests that were actually run and their actual result.
- Update only the Work log owned by the area changed.
- For a shared contract change, record affected owners in `docs/DECISIONS.md`; do not rewrite their implementation status.
- Typo-only or formatting-only edits do not require a Work log history entry.

## 6. Selecting the next task

When the user asks for their next task, current priority, or recommended work:

1. Check the current branch and repository status.
2. Open the mapped Work log.
3. Read `Current status`, `Next actions`, `Completion criteria`, `Dependencies`, and the latest history entry.
4. Compare the first incomplete action with `docs/DECISIONS.md` and relevant contracts.
5. Select the first incomplete action that has no unresolved dependency.
6. State the expected result, affected files, and verification commands.
7. Stay within the current owner's area.
8. If the Work log is stale, update it before implementation.
9. If the branch does not identify an owner, ask which role the user owns before changing code.

After completing the action, verify its criteria and advance the Work log to the next incomplete item.

## 7. Git, security, and commit rules

### Git safety

- Start from the latest shared `main` and work on the mapped feature branch.
- Do not commit directly to `main` unless the team explicitly requests a coordinated baseline or documentation change.
- Keep one logical change per commit.
- Do not force-push a shared branch.
- Do not use destructive Git or filesystem operations without explicit authorization.
- Do not discard or overwrite another person's staged, unstaged, or untracked work.
- Resolve conflicts carefully and rerun relevant checks.
- Never claim a push, test, or validation succeeded unless it actually did.

### Secrets and citizen data

- Never commit `.env`, API keys, passwords, tokens, AWS credentials, or private URLs.
- Read configuration from environment variables and keep `.env.example` current.
- Do not commit dependency directories, virtual environments, caches, build output, IDE settings, OS files, or real `storage/raw` collection data.
- Never send citizen profiles, sensitive attributes, or match results to the server.
- Never place citizen data in analytics, logs, URLs, or query strings.
- Agent execution logs may contain public notice processing data, but not citizen data or secrets.

### Commit messages

Use only: `Feat`, `Fix`, `Refactor`, `Docs`, `Test`, or `Chore`.

Format:

```text
Type: 한글 제목
```

- Keep the title concise and do not end it with a period.
- Add a body after a blank line when the reason or impact needs explanation.
- Do not mix unrelated work in one commit.

## 8. Completion criteria

A task is complete only when:

- The requested behavior or document change is present and understandable.
- Ownership boundaries and current shared contracts remain intact.
- No citizen profile data or secret is exposed.
- Relevant checks were run, with failures or skipped checks reported accurately.
- Schema and fixture changes were validated against their real contracts.
- Failure behavior and the demo fallback still work when affected.
- The responsible Work log reflects meaningful implementation changes and the next action.
- Changed files, important decisions, test results, and remaining blockers are reported.

For detailed coding, testing, collaboration, and deployment procedures, follow `docs/TEAM_CODEX_SYNC_CONTEXT.md`.
