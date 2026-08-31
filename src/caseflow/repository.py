from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from caseflow.db import AuditEventRecord, CaseRunRecord
from caseflow.domain import AIPolicy, CaseView, RunStage


class CaseNotFoundError(LookupError):
    pass


class CaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        name: str,
        source_text: str,
        ai_policy: AIPolicy,
    ) -> CaseRunRecord:
        record = CaseRunRecord(
            id=str(uuid4()),
            name=name,
            source_text=source_text,
            ai_policy=ai_policy.value,
            stage=RunStage.CREATED.value,
            artifacts={},
        )
        self.session.add(record)
        await self.audit(record.id, "case.created", {"name": name, "ai_policy": ai_policy.value})
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get(self, case_id: str) -> CaseRunRecord:
        record = await self.session.get(CaseRunRecord, case_id)
        if record is None:
            raise CaseNotFoundError(case_id)
        return record

    async def save(
        self,
        record: CaseRunRecord,
        *,
        stage: RunStage | None = None,
        artifact_name: str | None = None,
        artifact: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> CaseRunRecord:
        if stage is not None:
            record.stage = stage.value
        if artifact_name is not None and artifact is not None:
            record.artifacts = {**record.artifacts, artifact_name: artifact}
        record.error = error
        record.version += 1
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def audit(self, case_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.session.add(
            AuditEventRecord(case_id=case_id, event_type=event_type, payload=payload)
        )

    async def list_audit(self, case_id: str) -> list[AuditEventRecord]:
        result = await self.session.execute(
            select(AuditEventRecord)
            .where(AuditEventRecord.case_id == case_id)
            .order_by(AuditEventRecord.id)
        )
        return list(result.scalars())

    @staticmethod
    def to_view(record: CaseRunRecord) -> CaseView:
        return CaseView(
            id=record.id,
            name=record.name,
            stage=RunStage(record.stage),
            ai_policy=AIPolicy(record.ai_policy),
            version=record.version,
            artifacts=record.artifacts,
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
