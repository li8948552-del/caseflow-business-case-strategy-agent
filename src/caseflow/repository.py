from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from caseflow.db import AuditEventRecord, CaseRunRecord, JobRecord
from caseflow.domain import AIPolicy, CaseView, JobStatus, JobView, RunStage
from caseflow.errors import CaseBusyError


class CaseNotFoundError(LookupError):
    pass


class JobNotFoundError(LookupError):
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
        try:
            await self.session.commit()
        except StaleDataError as exc:
            await self.session.rollback()
            raise CaseBusyError("Concurrent case update detected") from exc
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

    async def enqueue_job(self, case_id: str) -> JobRecord:
        active = await self.session.scalar(
            select(JobRecord)
            .where(
                JobRecord.case_id == case_id,
                JobRecord.status.in_([JobStatus.QUEUED.value, JobStatus.RUNNING.value]),
            )
            .order_by(JobRecord.created_at.desc())
        )
        if active is not None:
            return active
        job = JobRecord(
            id=str(uuid4()),
            case_id=case_id,
            status=JobStatus.QUEUED.value,
        )
        self.session.add(job)
        await self.audit(case_id, "job.queued", {"job_id": job.id})
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, job_id: str) -> JobRecord:
        record = await self.session.get(JobRecord, job_id)
        if record is None:
            raise JobNotFoundError(job_id)
        return record

    async def claim_next_job(self) -> JobRecord | None:
        result = await self.session.execute(
            select(JobRecord)
            .where(JobRecord.status == JobStatus.QUEUED.value)
            .order_by(JobRecord.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None
        job.status = JobStatus.RUNNING.value
        job.attempts += 1
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def finish_job(
        self,
        job: JobRecord,
        *,
        succeeded: bool,
        error: str | None = None,
    ) -> JobRecord:
        job.status = JobStatus.SUCCEEDED.value if succeeded else JobStatus.FAILED.value
        job.error = error
        await self.session.commit()
        await self.session.refresh(job)
        return job

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

    @staticmethod
    def job_to_view(record: JobRecord) -> JobView:
        return JobView(
            id=record.id,
            case_id=record.case_id,
            status=JobStatus(record.status),
            attempts=record.attempts,
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
