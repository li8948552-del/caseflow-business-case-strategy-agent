from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AIPolicy(StrEnum):
    ALLOWED = "allowed"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"


class RunStage(StrEnum):
    CREATED = "created"
    FRAMING = "framing"
    AWAITING_GATE_1 = "awaiting_gate_1"
    RESEARCHING = "researching"
    STRATEGIZING = "strategizing"
    AWAITING_GATE_2 = "awaiting_gate_2"
    BUILDING = "building"
    DEFENDING = "defending"
    AWAITING_GATE_3 = "awaiting_gate_3"
    COMPLETED = "completed"
    FAILED = "failed"


class Evidence(BaseModel):
    evidence_id: str
    claim: str
    source_title: str
    source_url: str | None = None
    confidence: float = Field(ge=0, le=1)
    supports_hypotheses: list[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str
    importance: str
    evidence_needed: list[str]
    falsification_condition: str


class CaseFrame(BaseModel):
    decision_question: str
    objectives: list[str]
    constraints: list[str]
    stakeholders: list[str]
    required_questions: list[str]
    facts: list[str]
    unknowns: list[str]
    issue_tree: dict[str, Any]
    hypotheses: list[Hypothesis]


class ResearchOutput(BaseModel):
    executive_findings: list[str]
    evidence: list[Evidence]
    unresolved_questions: list[str]
    assumptions: list[str]


class StrategyOption(BaseModel):
    name: str
    description: str
    scores: dict[str, float]
    evidence_ids: list[str]
    risks: list[str]


class StrategyOutput(BaseModel):
    options: list[StrategyOption] = Field(min_length=3)
    recommendation: str
    rationale: list[str]
    rejected_options: dict[str, str]
    critical_tradeoffs: list[str]


class BuildOutput(BaseModel):
    financial_model: dict[str, Any]
    scenarios: dict[str, Any]
    implementation_roadmap: list[dict[str, Any]]
    kpis: list[dict[str, Any]]
    deck_outline: list[dict[str, Any]]
    risks_and_mitigations: list[dict[str, str]]


class DefenseOutput(BaseModel):
    rubric_scores: dict[str, float]
    weighted_score: float = Field(ge=0, le=5)
    submission_blockers: list[str]
    judge_questions: list[dict[str, str]]
    contradictions: list[str]
    recommended_fixes: list[str]


class CaseView(BaseModel):
    id: str
    name: str
    stage: RunStage
    ai_policy: AIPolicy
    version: int
    artifacts: dict[str, Any]
    error: str | None
    created_at: datetime
    updated_at: datetime


class GateDecision(BaseModel):
    approved: bool
    decided_by: str = Field(min_length=1, max_length=120)
    reason: str = Field(default="", max_length=1000)


class AuditEvent(BaseModel):
    id: int
    case_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
