from __future__ import annotations

from typing import Any

import structlog

from caseflow.domain import AIPolicy, CaseView, GateDecision, RunStage
from caseflow.errors import CaseBusyError, InvalidTransitionError, PolicyViolationError
from caseflow.repository import CaseRepository
from caseflow.runtime import AgentRuntime

log = structlog.get_logger()

BUSY_STAGES = {
    RunStage.FRAMING,
    RunStage.BUILDING,
    RunStage.DEFENDING,
}


class CaseService:
    def __init__(self, repository: CaseRepository, runtime: AgentRuntime):
        self.repository = repository
        self.runtime = runtime

    async def create(
        self,
        *,
        name: str,
        source_text: str,
        ai_policy: AIPolicy,
    ) -> CaseView:
        if ai_policy in {AIPolicy.PROHIBITED, AIPolicy.UNKNOWN}:
            raise PolicyViolationError(
                "AI policy must be explicitly allowed or restricted before creating a run"
            )
        record = await self.repository.create(
            name=name,
            source_text=source_text,
            ai_policy=ai_policy,
        )
        return self.repository.to_view(record)

    async def get(self, case_id: str) -> CaseView:
        return self.repository.to_view(await self.repository.get(case_id))

    async def advance(self, case_id: str) -> CaseView:
        record = await self.repository.get(case_id)
        stage = RunStage(record.stage)
        if stage in BUSY_STAGES:
            raise CaseBusyError(f"Case is already processing stage: {stage.value}")
        try:
            if stage == RunStage.CREATED:
                await self.repository.save(record, stage=RunStage.FRAMING)
                output = await self.runtime.frame(record.source_text)
                await self.repository.audit(case_id, "agent.framed", {})
                record = await self.repository.save(
                    record,
                    stage=RunStage.AWAITING_GATE_1,
                    artifact_name="frame",
                    artifact=output.model_dump(mode="json"),
                )
            elif stage == RunStage.RESEARCHING:
                output = await self.runtime.research(
                    record.source_text,
                    record.artifacts["frame"],
                )
                await self.repository.audit(case_id, "agent.researched", {})
                record = await self.repository.save(
                    record,
                    stage=RunStage.STRATEGIZING,
                    artifact_name="research",
                    artifact=output.model_dump(mode="json"),
                )
            elif stage == RunStage.STRATEGIZING:
                output = await self.runtime.strategize(
                    record.source_text,
                    record.artifacts["frame"],
                    record.artifacts["research"],
                )
                await self.repository.audit(case_id, "agent.strategized", {})
                record = await self.repository.save(
                    record,
                    stage=RunStage.AWAITING_GATE_2,
                    artifact_name="strategy",
                    artifact=output.model_dump(mode="json"),
                )
            elif stage == RunStage.BUILDING:
                output = await self.runtime.build(record.source_text, record.artifacts)
                await self.repository.audit(case_id, "agent.built", {})
                record = await self.repository.save(
                    record,
                    stage=RunStage.DEFENDING,
                    artifact_name="build",
                    artifact=output.model_dump(mode="json"),
                )
            elif stage == RunStage.DEFENDING:
                output = await self.runtime.defend(record.source_text, record.artifacts)
                await self.repository.audit(case_id, "agent.defended", {})
                record = await self.repository.save(
                    record,
                    stage=RunStage.AWAITING_GATE_3,
                    artifact_name="defense",
                    artifact=output.model_dump(mode="json"),
                )
            else:
                raise InvalidTransitionError(
                    f"Stage {stage.value} cannot advance; a gate decision may be required"
                )
        except (InvalidTransitionError, CaseBusyError):
            raise
        except Exception as exc:
            log.exception("case_stage_failed", case_id=case_id, stage=stage.value)
            await self.repository.audit(
                case_id,
                "agent.failed",
                {"stage": stage.value, "error_type": type(exc).__name__},
            )
            await self.repository.save(record, stage=RunStage.FAILED, error=str(exc)[:2000])
            raise
        return self.repository.to_view(record)

    async def decide_gate(
        self,
        case_id: str,
        gate_number: int,
        decision: GateDecision,
    ) -> CaseView:
        record = await self.repository.get(case_id)
        stage = RunStage(record.stage)
        transitions: dict[int, tuple[RunStage, RunStage, RunStage]] = {
            1: (RunStage.AWAITING_GATE_1, RunStage.RESEARCHING, RunStage.CREATED),
            2: (RunStage.AWAITING_GATE_2, RunStage.BUILDING, RunStage.STRATEGIZING),
            3: (RunStage.AWAITING_GATE_3, RunStage.COMPLETED, RunStage.BUILDING),
        }
        if gate_number not in transitions:
            raise InvalidTransitionError("Gate number must be 1, 2, or 3")
        expected, approved_stage, rejected_stage = transitions[gate_number]
        if stage != expected:
            raise InvalidTransitionError(
                f"Gate {gate_number} requires stage {expected.value}, not {stage.value}"
            )
        target = approved_stage if decision.approved else rejected_stage
        await self.repository.audit(
            case_id,
            "gate.decided",
            {
                "gate": gate_number,
                "approved": decision.approved,
                "decided_by": decision.decided_by,
                "reason": decision.reason,
            },
        )
        record = await self.repository.save(record, stage=target)
        return self.repository.to_view(record)

    async def audit(self, case_id: str) -> list[dict[str, Any]]:
        await self.repository.get(case_id)
        rows = await self.repository.list_audit(case_id)
        return [
            {
                "id": row.id,
                "case_id": row.case_id,
                "event_type": row.event_type,
                "payload": row.payload,
                "created_at": row.created_at,
            }
            for row in rows
        ]
