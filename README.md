# CaseFlow — Enterprise Business Case Strategy Agent

CaseFlow v1 is a durable, human-gated agent system for business case competitions.
It turns a PDF case brief into a traceable problem frame, evidence base, strategy,
financial plan, deck outline, rubric review, and judge Q&A.

> The original lightweight harness is permanently preserved on the
> [v0.1 branch](https://github.com/li8948552-del/caseflow-business-case-strategy-agent/tree/v0.1).

## Why this is an agent

CaseFlow v1 observes persisted workflow state, selects the next permitted action,
invokes specialist agents and tools, validates structured outputs, changes durable
state, and either continues or pauses for human approval.

## Enterprise capabilities

- FastAPI service with PDF upload and API-key authentication
- PostgreSQL/SQLite persistence and Alembic migrations
- Durable background jobs and restart-safe workflow stages
- OpenAI Agents SDK with typed Pydantic outputs and web search
- Optimistic locking and duplicate-job prevention
- Three non-bypassable human approval gates
- Audit trail for agent actions and decisions
- JSON structured logging, retries, input limits, and AI-policy enforcement
- Docker Compose, non-root container, unit tests, and GitHub Actions CI

## Workflow

```text
Upload case
  → Frame
  → Gate 1
  → Research
  → Strategy
  → Gate 2
  → Finance / implementation / ghost deck
  → Red-team defense
  → Gate 3
  → Complete
```

## Quick start with Docker

```bash
git clone https://github.com/li8948552-del/caseflow-business-case-strategy-agent.git
cd caseflow-business-case-strategy-agent
cp .env.example .env
export OPENAI_API_KEY="your-key"
docker compose up --build
```

API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

Create a case:

```bash
curl -X POST http://localhost:8000/v1/cases \
  -H "X-API-Key: change-me-before-deploying" \
  -F 'name=Oliver Wyman Practice Case' \
  -F 'ai_policy=allowed' \
  -F 'case_file=@Case Brief.pdf'
```

Queue the next stage:

```bash
curl -X POST http://localhost:8000/v1/cases/CASE_ID/advance \
  -H "X-API-Key: change-me-before-deploying"
```

Approve a gate:

```bash
curl -X POST http://localhost:8000/v1/cases/CASE_ID/gates/1 \
  -H "X-API-Key: change-me-before-deploying" \
  -H "Content-Type: application/json" \
  -d '{"approved":true,"decided_by":"Hexin","reason":"Issue tree approved"}'
```

## Local development

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
make install
make run
```

Run `make worker` in a second terminal. Run `make lint test` before opening a PR.

## Repository versions

- `v0.1`: original Codex + Markdown harness, preserved and usable without API code.
- `feature/enterprise-agent-v1`: enterprise implementation under review.
- `main`: updated only after CI passes.

See [architecture](docs/architecture.md), [operations](docs/runbook.md), and
[security](SECURITY.md).
