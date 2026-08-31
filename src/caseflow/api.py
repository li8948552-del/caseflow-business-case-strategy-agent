from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from caseflow.config import Settings, get_settings
from caseflow.db import get_session, init_db
from caseflow.domain import AIPolicy, CaseView, GateDecision, JobView
from caseflow.errors import CaseBusyError, InvalidTransitionError, PolicyViolationError
from caseflow.logging import configure_logging
from caseflow.repository import (
    CaseNotFoundError,
    CaseRepository,
    JobNotFoundError,
)
from caseflow.runtime import OpenAIAgentRuntime
from caseflow.security import require_api_key
from caseflow.service import CaseService


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    await init_db()
    yield


app = FastAPI(
    title="CaseFlow Enterprise Agent API",
    version="1.0.0",
    lifespan=lifespan,
)


async def service_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CaseService:
    return CaseService(CaseRepository(session), OpenAIAgentRuntime(settings))


Service = Annotated[CaseService, Depends(service_dependency)]


@app.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/cases",
    response_model=CaseView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
async def create_case(
    service: Service,
    name: Annotated[str, Form(min_length=1, max_length=240)],
    ai_policy: Annotated[AIPolicy, Form()],
    case_file: Annotated[UploadFile, File()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CaseView:
    filename = case_file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF case files are accepted")
    data = await case_file.read(settings.max_case_bytes + 1)
    if len(data) > settings.max_case_bytes:
        raise HTTPException(status_code=413, detail="Case file exceeds configured size limit")
    try:
        reader = PdfReader(BytesIO(data))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to parse PDF") from exc
    if not text.strip():
        raise HTTPException(status_code=422, detail="PDF contains no extractable text")
    return await service.create(name=name, source_text=text, ai_policy=ai_policy)


@app.get(
    "/v1/cases/{case_id}",
    response_model=CaseView,
    dependencies=[Depends(require_api_key)],
)
async def get_case(case_id: str, service: Service) -> CaseView:
    return await service.get(case_id)


@app.post(
    "/v1/cases/{case_id}/advance",
    response_model=JobView,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_api_key)],
)
async def advance_case(case_id: str, service: Service) -> JobView:
    return await service.enqueue(case_id)


@app.get(
    "/v1/jobs/{job_id}",
    response_model=JobView,
    dependencies=[Depends(require_api_key)],
)
async def get_job(
    job_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobView:
    repository = CaseRepository(session)
    return repository.job_to_view(await repository.get_job(job_id))


@app.post(
    "/v1/cases/{case_id}/gates/{gate_number}",
    response_model=CaseView,
    dependencies=[Depends(require_api_key)],
)
async def decide_gate(
    case_id: str,
    gate_number: int,
    decision: GateDecision,
    service: Service,
) -> CaseView:
    return await service.decide_gate(case_id, gate_number, decision)


@app.get(
    "/v1/cases/{case_id}/audit",
    dependencies=[Depends(require_api_key)],
)
async def get_audit(case_id: str, service: Service) -> list[dict[str, object]]:
    return await service.audit(case_id)


@app.exception_handler(CaseNotFoundError)
@app.exception_handler(JobNotFoundError)
async def not_found_handler(_, exc: LookupError):
    return _problem(404, "Resource not found", str(exc))


@app.exception_handler(InvalidTransitionError)
async def transition_handler(_, exc: InvalidTransitionError):
    return _problem(409, "Invalid workflow transition", str(exc))


@app.exception_handler(CaseBusyError)
async def busy_handler(_, exc: CaseBusyError):
    return _problem(409, "Case is busy", str(exc))


@app.exception_handler(PolicyViolationError)
async def policy_handler(_, exc: PolicyViolationError):
    return _problem(422, "AI policy violation", str(exc))


def _problem(status_code: int, title: str, detail: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "type": "about:blank",
            "title": title,
            "status": status_code,
            "detail": detail,
        },
        media_type="application/problem+json",
    )
