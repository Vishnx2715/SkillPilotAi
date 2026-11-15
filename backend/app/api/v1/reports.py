"""Reports API — PDF and JSON career readiness reports."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_student
from app.core.rate_limit import check_rate_limit, get_client_identifier
from app.models.user import User
from app.services.report_service import ReportService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate")
async def generate_report(
    request: Request,
    body: dict,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identifier = get_client_identifier(request, current_user.id)
    allowed, err = check_rate_limit(identifier, "report_generate", 3, 3600)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    report_type = body.get("report_type", "career_readiness")
    return await ReportService.generate(db, profile.id, report_type)


@router.get("/")
async def list_reports(current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await ReportService.list_reports(db, profile.id)


@router.get("/{report_id}/pdf")
async def download_pdf(
    report_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    pdf_bytes = await ReportService.download_pdf(db, profile.id, report_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=skillpilot_report_{report_id}.pdf"},
    )


@router.get("/{report_id}/json")
async def download_json(
    report_id: int, current_user: User = Depends(require_student), db: AsyncSession = Depends(get_db)
):
    profile = await ProfileService.get_profile_by_user_id(db, current_user.id)
    return await ReportService.download_json(db, profile.id, report_id)
