import asyncio

import structlog

from caseflow.config import get_settings
from caseflow.db import SessionFactory, init_db
from caseflow.logging import configure_logging
from caseflow.repository import CaseRepository
from caseflow.runtime import OpenAIAgentRuntime
from caseflow.service import CaseService

log = structlog.get_logger()


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.auto_create_schema:
        await init_db()
    runtime = OpenAIAgentRuntime(settings)
    log.info("worker_started")
    while True:
        async with SessionFactory() as session:
            repository = CaseRepository(session)
            job = await repository.claim_next_job()
            if job is None:
                await asyncio.sleep(1)
                continue
            service = CaseService(repository, runtime)
            try:
                await service.advance(job.case_id)
            except Exception as exc:
                await repository.finish_job(job, succeeded=False, error=str(exc)[:2000])
                log.exception("job_failed", job_id=job.id, case_id=job.case_id)
            else:
                await repository.finish_job(job, succeeded=True)
                log.info("job_succeeded", job_id=job.id, case_id=job.case_id)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
