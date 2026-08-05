# AGENTS.md

## 1. Project

### Name
**Gangnam Change Agent**

### Goal
Build a 2-day hackathon MVP that:

1. Implements a real AI Agent.
2. Addresses a Gangnam-gu social problem.
3. Uses public Gangnam-gu notices and attachments.
4. Converts document changes into citizen actions.
5. Keeps citizen profile data on the user's device.

### Core flow

```text
Gangnam notice
→ HTML analysis
→ completeness check
→ attachment tool selection
→ PDF/HWPX extraction
→ previous notice comparison
→ evidence validation
→ retry or human handoff
→ admin approval
→ policy package publication
→ local citizen matching
```

### MVP priority
A working end-to-end demo is more important than broad coverage, infrastructure complexity, or visual polish.

Do not add features outside the MVP unless the core flow already works.

---

## 2. Repository ownership

Respect the assigned ownership boundaries.

| Area | Owner | Main responsibility |
|---|---|---|
| `backend/` | Agent·Backend | Crawling, LangGraph, document analysis, policy package API |
| `frontend/citizen/` | Citizen PWA | Local profile, rule evaluation, citizen result screens |
| `frontend/admin/` | Admin·Integration | Review UI, approval flow, Agent logs |
| `infra/` | Admin·Integration | AWS deployment, environment configuration |
| `docs/contracts/` | Shared | API and policy package contracts |
| `demo-data/` | Shared | Fixed fallback data for the demo |

Rules:

- Do not make large changes in another owner's main folder without agreement.
- Shared schema changes must be made in `docs/contracts/` first.
- Notify the team before changing API paths, response fields, enum values, or rule operators.
- Avoid unrelated refactoring during the hackathon.

---

## 3. Common coding rules

- Write one executable statement per line.
- Add spaces around binary operators and after commas.
- Keep comments at the same indentation level as the code they explain.
- Prefer clear names over abbreviations.
- Keep functions small enough to have one clear responsibility.
- Do not leave dead code, unused imports, commented-out implementations, or debug secrets.
- Use double quotes by default unless a formatter or language syntax requires otherwise.
- Do not hardcode API keys, passwords, tokens, AWS credentials, or private URLs.
- Read configuration from environment variables.
- Add new dependencies only when they are necessary for the MVP.
- Do not silently change existing behavior while “cleaning up” code.
- Preserve existing working code unless the requested task requires modifying it.

---

## 4. Python conventions

Use normal Python conventions.

### Naming

- Variables, functions, modules: `snake_case`
- Classes and Pydantic models: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private implementation helpers: prefix with `_` only when appropriate

### Syntax

- Do not use semicolons at line endings.
- Use `key=value` for keyword arguments and default values.
- Add type hints to public functions and Agent state structures.
- Prefer explicit return types.
- Use `pathlib.Path` for filesystem paths where practical.
- Use timezone-aware datetimes for persisted timestamps.
- Catch specific exceptions instead of broad `except Exception` unless re-raising or recording a final fallback error.

### Backend structure

- FastAPI route handlers should be thin.
- Business logic belongs in services, tools, or Agent nodes.
- External calls must have timeouts and error handling.
- LLM extraction results must use Pydantic structured output.
- Eligibility decisions must not be made by free-form LLM output.
- Each extracted change must reference evidence.

Example:

```python
MAX_RETRY_COUNT = 2


class PolicyPackage(BaseModel):
    policy_id: str
    title: str
    changes: list[dict]
    evidence: list[dict]


def load_notice(notice_url: str) -> str:
    return notice_client.fetch(notice_url)
```

---

## 5. TypeScript and React conventions

### Naming

- Variables and functions: `camelCase`
- React components, classes, types, interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- React component files: `PascalCase.tsx`
- Utility and hook files: `camelCase.ts` or `useSomething.ts`

### Syntax

- Use semicolons.
- Prefer TypeScript over plain JavaScript.
- Avoid `any`; define DTO and domain types.
- Keep API access in an adapter or service layer.
- Keep rule evaluation separate from UI components.
- Do not put citizen profile data in server requests.
- Do not use an LLM for `YES / NO / UNKNOWN / STALE` evaluation.
- Prefer deterministic templates for eligibility explanations.

Example:

```tsx
const MAX_VISIBLE_CHANGES = 5;

interface PolicyCardProps {
  title: string;
  deadlineAt: string | null;
}

export function PolicyCard(props: PolicyCardProps) {
  return <article>{props.title}</article>;
}
```

---

## 6. API and JSON naming

The backend contract is Python-oriented and uses `snake_case`.

Examples:

```json
{
  "policy_id": "demo-policy-v2",
  "deadline_at": "2026-09-10",
  "eligibility_rule": {},
  "required_actions": []
}
```

Rules:

- API payload keys remain `snake_case`.
- Do not rename payload fields independently in each frontend component.
- Frontend internal variables and functions remain `camelCase`.
- API DTO types may retain `snake_case` keys as an explicit external-contract exception.
- If conversion is needed, perform it once in the API adapter, not throughout the UI.
- Dates use ISO 8601 strings.
- Enum values must be documented and shared.

Required citizen match states:

```text
YES
NO
UNKNOWN
STALE
```

Do not replace these with ungrounded percentage scores.

---

## 7. Shared policy package contract

The minimum package shape is:

```json
{
  "policy_id": "demo-policy-v2",
  "policy_family_id": "demo-policy",
  "version": 2,
  "title": "청년 지원사업 변경",
  "category": "지원사업",
  "published_at": "2026-08-04",
  "effective_at": "2026-08-05",
  "deadline_at": "2026-09-10",
  "summary": "지원 연령이 확대되고 신청 마감이 앞당겨졌습니다.",
  "changes": [],
  "eligibility_rule": {},
  "required_profile_fields": [],
  "required_actions": [],
  "evidence": [],
  "review": {
    "status": "approved",
    "reviewed_at": "2026-08-04T15:00:00+09:00"
  }
}
```

Contract rules:

- Do not remove required fields without team agreement.
- Additive optional fields are preferred over breaking changes.
- Evidence must identify the source document and location.
- Only approved packages are exposed to the citizen app.
- Demo values must be marked as demo values and not represented as verified real policy.

---

## 8. Privacy rules

These rules are non-negotiable.

### Never send to the server

- Citizen age
- Residence profile
- Employment status
- Income
- Household information
- Health or disability information
- Citizen match result
- Full local profile

### Server may store

- Public notice data
- Policy packages
- Review status
- Agent execution logs without citizen profile data
- Broad non-sensitive app settings when required

### Frontend

- Store citizen profile data locally using IndexedDB.
- Do not include local profile fields in analytics, logs, query strings, or API payloads.
- Do not claim local storage is perfectly secure.
- Use this wording when needed:

> 중앙 서버에 개인 프로필을 모으지 않아 대규모 유출 위험을 줄입니다.

---

## 9. Agent rules

The server Agent must show actual decision-making.

Required behavior:

```text
Analyze HTML
→ decide whether information is complete
→ select attachment tool
→ evaluate tool output
→ retry another search path when evidence is missing
→ hand off to a human when unresolved
```

Rules:

- Crawling alone is not the Agent.
- Summarization alone is not the Agent.
- Store Agent node and tool execution logs.
- Limit retries with `max_retry`.
- Unsupported legacy `.hwp` files may be handed off.
- Prefer `.hwpx` automation when verified.
- Do not claim universal HWP support.
- Do not publish unsupported or weakly evidenced results automatically.
- Human approval is required before publication.

---

## 10. Git workflow

### Branches

- `main`: demo-ready stable branch
- `feat/agent-backend`: Agent·Backend
- `feat/citizen-pwa`: citizen application
- `feat/admin-integration`: admin, integration, deployment

Rules:

1. Do not commit directly to `main`.
2. Pull the latest shared changes before starting work.
3. Keep one logical change per commit.
4. Merge early; do not wait until the final hours.
5. Resolve conflicts carefully and rerun the relevant checks.
6. Do not force-push shared branches without agreement.
7. Do not commit `.env`, credentials, build output, virtual environments, or dependency directories.

---

## 11. Commit message convention

Use only these commit types:

| Type | Use |
|---|---|
| `Feat` | New feature |
| `Fix` | Bug fix |
| `Refactor` | Internal restructuring without behavior change |
| `Docs` | Documentation |
| `Test` | Test code |
| `Chore` | Configuration, package, deployment, maintenance |

Format:

```text
Type: 한글 제목
```

Examples:

```text
Feat: 강남구 공고 수집 기능 추가
Fix: HWPX 표 추출 실패 처리
Feat: 로컬 정책 판정 기능 추가
Chore: AWS 배포 환경변수 설정
Docs: 정책 패키지 API 계약 수정
```

For a substantial change, add a body after a blank line:

```text
Feat: 정책 패키지 승인 API 추가

- 관리자 승인 상태 저장
- 승인된 패키지만 사용자 API에 노출
```

Rules:

- Do not end the title with a period.
- Keep the title concise.
- Explain what changed and why when a body is needed.
- Do not mix unrelated work in one commit.

---

## 12. Formatting and checks

Before finishing a task:

### Python

Inspect the repository configuration and run the available checks.

Preferred when configured:

```bash
ruff check .
ruff format --check .
pytest
```

Alternative when configured:

```bash
black --check .
pytest
```

### Frontend

Use scripts already defined in `package.json`.

Typical checks:

```bash
npm run lint
npm run test
npm run build
```

Rules:

- Do not install a new formatter or test framework without agreement.
- Do not claim checks passed unless they were actually run.
- Report failed or skipped checks clearly.
- At minimum, run the relevant build or syntax check for changed code.

---

## 13. Deployment rules

- Local end-to-end operation comes before AWS deployment.
- Do not spend more than one hour blocked on initial AWS configuration.
- Prefer the simplest deployable architecture.
- Do not introduce Kubernetes or complex VPC design. Terraform is the agreed deployment tool.
- Keep `.env.example` current.
- Verify CORS, API base URL, health checks, and HTTPS.
- Keep fixed demo JSON as a fallback.
- Prepare screenshots or a short recording for network failure.

---

## 14. Codex working instructions

When working in this repository:

1. Read this file and inspect the existing repository before editing.
2. State a short implementation plan before making broad changes.
3. Do not overwrite working code without understanding it.
4. Make the smallest change that completes the requested task.
5. Respect folder ownership and shared contracts.
6. Do not perform destructive Git or filesystem operations unless explicitly requested.
7. Do not expose secrets in code, logs, commits, or responses.
8. Do not refactor unrelated files.
9. Add or update tests for deterministic logic.
10. Run relevant checks and report their exact results.
11. Report files changed, important decisions, and remaining blockers.
12. When blocked, preserve the working fallback instead of removing functionality.

---

## 15. Definition of done

A task is done only when:

- The requested behavior works.
- Shared contracts remain compatible.
- No citizen profile data is sent to the server.
- Relevant checks were run or explicitly reported as unavailable.
- Failure behavior is handled.
- Demo fallback still works.
- The change is understandable to the next teammate.

---

## 16. Central documentation and work logs

Before changing code, read in this order:

1. `AGENTS.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/DECISIONS.md`
4. Relevant files under `docs/contracts/`
5. The responsible area's `docs/worklogs/*/WORKLOG.md`

Documentation responsibilities:

- `docs/PROJECT_CONTEXT.md`: current product and architecture only
- `docs/DECISIONS.md`: accepted cross-team decisions and rationale
- `docs/contracts/`: shared API and JSON contracts
- `docs/worklogs/agent-backend/WORKLOG.md`: `backend/**`
- `docs/worklogs/citizen-pwa/WORKLOG.md`: `frontend/citizen/**`
- `docs/worklogs/admin-integration/WORKLOG.md`: `frontend/admin/**` and `infra/**`

Rules:

- Update shared contracts before implementations that depend on them.
- Record cross-team decisions in `docs/DECISIONS.md`.
- Update only the Work log owned by the area changed.
- Keep each Work log Current status aligned with the repository.
- Record only tests that were actually run.
- Do not use archived prompts as the current specification.
- Current project truth is `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, and `docs/contracts/`.

---

## 17. Responding to "What should I do next?"

When the user asks what to work on next:

1. Check the current branch and repository status.
2. Map `feat/agent-backend`, `feat/citizen-pwa`, or `feat/admin-integration` to its responsible Work log.
3. Read its Current status, Next actions, Completion criteria, Dependencies, and latest Change history entry.
4. Confirm that the first incomplete action does not conflict with `docs/DECISIONS.md` or `docs/contracts/`.
5. Recommend the first incomplete action with its expected result, affected files, and verification commands.
6. Do not select work owned by another teammate.
7. If the current branch does not identify an ownership area, ask which role the user owns before changing code.
8. If the Work log is stale or conflicts with a newer shared contract, report the conflict and update the Work log before implementation.
9. After completing and verifying work, mark the action complete and update Current status, Dependencies, and Change history.

Do not mark an action complete before its Completion criteria have been verified.
