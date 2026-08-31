from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from caseflow.domain import (
    AIPolicy,
    BuildOutput,
    CaseFrame,
    DefenseOutput,
    GateDecision,
    Hypothesis,
    ResearchOutput,
    RunStage,
    StrategyOption,
    StrategyOutput,
)
from caseflow.errors import PolicyViolationError
from caseflow.repository import CaseRepository
from caseflow.service import CaseService


class FakeRepository:
    def __init__(self) -> None:
        self.records = {}
        self.events = []

    async def create(self, *, name, source_text, ai_policy):
        now = datetime.now(UTC)
        record = SimpleNamespace(
            id=str(uuid4()),
            name=name,
            source_text=source_text,
            ai_policy=ai_policy.value,
            stage=RunStage.CREATED.value,
            artifacts={},
            error=None,
            version=1,
            created_at=now,
            updated_at=now,
        )
        self.records[record.id] = record
        return record

    async def get(self, case_id):
        return self.records[case_id]

    async def save(self, record, *, stage=None, artifact_name=None, artifact=None, error=None):
        if stage is not None:
            record.stage = stage.value
        if artifact_name is not None:
            record.artifacts = {**record.artifacts, artifact_name: artifact}
        record.error = error
        record.version += 1
        record.updated_at = datetime.now(UTC)
        return record

    async def audit(self, case_id, event_type, payload):
        self.events.append((case_id, event_type, payload))

    async def list_audit(self, case_id):
        return []

    @staticmethod
    def to_view(record):
        return CaseRepository.to_view(record)


class FakeRuntime:
    async def frame(self, source_text):
        return CaseFrame(
            decision_question="How should the client grow?",
            objectives=["Grow"],
            constraints=["Budget"],
            stakeholders=["Client"],
            required_questions=["Strategy"],
            facts=["Current state"],
            unknowns=["Demand"],
            issue_tree={"root": ["market", "economics", "execution"]},
            hypotheses=[
                Hypothesis(
                    hypothesis_id="H-001",
                    statement="Demand exists",
                    importance="Changes decision",
                    evidence_needed=["Market data"],
                    falsification_condition="No demand",
                )
            ],
        )

    async def research(self, source_text, frame):
        return ResearchOutput(
            executive_findings=["Demand is plausible"],
            evidence=[],
            unresolved_questions=[],
            assumptions=["Adoption"],
        )

    async def strategize(self, source_text, frame, research):
        options = [
            StrategyOption(
                name=f"Option {index}",
                description="A distinct option",
                scores={"impact": 4},
                evidence_ids=[],
                risks=["Execution"],
            )
            for index in range(3)
        ]
        return StrategyOutput(
            options=options,
            recommendation="Option 0",
            rationale=["Highest impact"],
            rejected_options={"Option 1": "Lower impact", "Option 2": "Higher risk"},
            critical_tradeoffs=["Speed versus control"],
        )

    async def build(self, source_text, artifacts):
        return BuildOutput(
            financial_model={"roi": "benefit / cost"},
            scenarios={"base": {}},
            implementation_roadmap=[],
            kpis=[],
            deck_outline=[],
            risks_and_mitigations=[],
        )

    async def defend(self, source_text, artifacts):
        return DefenseOutput(
            rubric_scores={"strategy": 4},
            weighted_score=4,
            submission_blockers=[],
            judge_questions=[],
            contradictions=[],
            recommended_fixes=[],
        )


@pytest.mark.asyncio
async def test_full_human_gated_workflow() -> None:
    repository = FakeRepository()
    service = CaseService(repository, FakeRuntime())

    case = await service.create(
        name="Practice",
        source_text="Case",
        ai_policy=AIPolicy.ALLOWED,
    )
    case = await service.advance(case.id)
    assert case.stage == RunStage.AWAITING_GATE_1

    case = await service.decide_gate(
        case.id, 1, GateDecision(approved=True, decided_by="Hexin")
    )
    assert case.stage == RunStage.RESEARCH_READY

    case = await service.advance(case.id)
    assert case.stage == RunStage.STRATEGY_READY
    case = await service.advance(case.id)
    assert case.stage == RunStage.AWAITING_GATE_2

    case = await service.decide_gate(
        case.id, 2, GateDecision(approved=True, decided_by="Team")
    )
    case = await service.advance(case.id)
    assert case.stage == RunStage.DEFENSE_READY
    case = await service.advance(case.id)
    assert case.stage == RunStage.AWAITING_GATE_3

    case = await service.decide_gate(
        case.id, 3, GateDecision(approved=True, decided_by="Team")
    )
    assert case.stage == RunStage.COMPLETED


@pytest.mark.asyncio
async def test_unknown_ai_policy_is_blocked() -> None:
    service = CaseService(FakeRepository(), FakeRuntime())
    with pytest.raises(PolicyViolationError):
        await service.create(
            name="Blocked",
            source_text="Case",
            ai_policy=AIPolicy.UNKNOWN,
        )
