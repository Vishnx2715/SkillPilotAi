"""Career Readiness Report service — generates PDF and JSON reports."""
import json
import io
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_plan import CareerReadinessReport
from app.models.profile import StudentProfile
from app.models.skill import LearnerSkill
from app.models.roadmap import LearningPath, RoadmapModule
from app.models.assessment import AssessmentAttempt
from app.models.practice import CodeSubmission
from app.models.project import ProjectSubmission
from app.models.mentor import MentorFeedback
from app.agents.report_summary_agent import ReportSummaryAgent


async def _build_report_data(db: AsyncSession, profile_id: int) -> Dict[str, Any]:
    prof_res = await db.execute(
        select(StudentProfile)
        .options(
            selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill),
            selectinload(StudentProfile.target_role),
        )
        .where(StudentProfile.id == profile_id)
    )
    profile = prof_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # Readiness
    lp_res = await db.execute(
        select(LearningPath).where(
            LearningPath.student_profile_id == profile_id,
            LearningPath.status == "active",
        )
    )
    lp = lp_res.scalar_one_or_none()
    readiness = lp.readiness_score if lp else 0.0

    # Skills
    strengths = [ls.skill.name for ls in profile.learner_skills if ls.mastery_percentage >= 75 and ls.skill]
    gaps = [ls.skill.name for ls in profile.learner_skills if ls.mastery_percentage < 60 and ls.skill]
    skill_summary = [
        {"skill": ls.skill.name if ls.skill else "", "mastery": ls.mastery_percentage}
        for ls in sorted(profile.learner_skills, key=lambda x: -x.mastery_percentage)
    ]

    # Roadmap
    roadmap_summary: Dict[str, Any] = {}
    if lp:
        mod_res = await db.execute(select(RoadmapModule).where(RoadmapModule.learning_path_id == lp.id))
        mods = mod_res.scalars().all()
        total = len(mods)
        completed = sum(1 for m in mods if m.status == "completed")
        roadmap_summary = {
            "total_modules": total, "completed": completed,
            "progress_pct": round((completed / max(total, 1)) * 100, 1)
        }

    # Assessments
    a_res = await db.execute(
        select(func.avg(AssessmentAttempt.mastery_percentage), func.count(AssessmentAttempt.id))
        .where(AssessmentAttempt.student_profile_id == profile_id,
               AssessmentAttempt.submitted_at != None)
    )
    a_row = a_res.one()
    assessment_avg = float(a_row[0] or 0)
    assessment_count = a_row[1] or 0

    # Coding
    cs_res = await db.execute(
        select(func.count(CodeSubmission.id),
               func.sum(func.case((CodeSubmission.status == "passed", 1), else_=0)))
        .where(CodeSubmission.student_profile_id == profile_id)
    )
    from sqlalchemy import case as sa_case
    cs_res = await db.execute(
        select(
            func.count(CodeSubmission.id).label("total"),
            func.sum(sa_case((CodeSubmission.status == "passed", 1), else_=0)).label("solved")
        ).where(CodeSubmission.student_profile_id == profile_id)
    )
    cs_row = cs_res.one()
    coding_total = cs_row.total or 0
    coding_solved = cs_row.solved or 0

    # Projects
    proj_res = await db.execute(
        select(func.avg(ProjectSubmission.evaluation_score), func.count(ProjectSubmission.id))
        .where(ProjectSubmission.student_profile_id == profile_id,
               ProjectSubmission.status == "evaluated")
    )
    proj_row = proj_res.one()
    portfolio_avg = float(proj_row[0] or 0)
    project_count = proj_row[1] or 0

    # Mentor feedback
    fb_res = await db.execute(
        select(MentorFeedback).where(MentorFeedback.student_profile_id == profile_id)
        .order_by(MentorFeedback.created_at.desc()).limit(3)
    )
    mentor_feedback_list = [
        {"type": f.feedback_type, "comment": f.comment[:200]}
        for f in fb_res.scalars().all()
    ]

    return {
        "student_name": profile.full_name,
        "career_role": profile.target_role.name if profile.target_role else "Not selected",
        "readiness_score": readiness,
        "skill_summary": skill_summary,
        "strengths": strengths[:5],
        "gaps": gaps[:5],
        "roadmap": roadmap_summary,
        "assessment_avg": assessment_avg,
        "assessment_count": assessment_count,
        "coding_total": coding_total,
        "coding_solved": coding_solved,
        "portfolio_avg": portfolio_avg,
        "projects_count": project_count,
        "mentor_feedback": mentor_feedback_list,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_pdf(data: Dict[str, Any], narrative: Dict[str, Any]) -> bytes:
    """Generate a simple PDF report with ReportLab."""
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        h1 = styles["Heading1"]
        h2 = styles["Heading2"]
        normal = styles["Normal"]
        story = []

        # Title
        story.append(Paragraph("Skill Pilot AI — Career Readiness Report", h1))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"Student: {data['student_name']}", normal))
        story.append(Paragraph(f"Career Goal: {data['career_role']}", normal))
        story.append(Paragraph(f"Generated: {data['generated_at'][:10]}", normal))
        story.append(Spacer(1, 0.5*cm))

        # Readiness
        story.append(Paragraph("Career Readiness Score", h2))
        story.append(Paragraph(f"{data['readiness_score']:.0f}%", h1))
        story.append(Spacer(1, 0.3*cm))

        # Narrative
        if narrative.get("executive_summary"):
            story.append(Paragraph("Executive Summary", h2))
            story.append(Paragraph(narrative["executive_summary"], normal))
            story.append(Spacer(1, 0.3*cm))

        # Skills table
        if data.get("skill_summary"):
            story.append(Paragraph("Skill Mastery", h2))
            table_data = [["Skill", "Mastery %"]]
            for s in data["skill_summary"][:15]:
                table_data.append([s["skill"], f"{s['mastery']:.0f}%"])
            tbl = Table(table_data, colWidths=[10*cm, 5*cm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0fdf4")]),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.5*cm))

        # Stats
        story.append(Paragraph("Activity Summary", h2))
        stats_data = [
            ["Assessments completed", str(data.get("assessment_count", 0))],
            ["Avg assessment mastery", f"{data.get('assessment_avg', 0):.0f}%"],
            ["Coding problems solved", str(data.get("coding_solved", 0))],
            ["Projects evaluated", str(data.get("projects_count", 0))],
            ["Avg project score", f"{data.get('portfolio_avg', 0):.0f}%"],
        ]
        stats_tbl = Table(stats_data, colWidths=[10*cm, 5*cm])
        stats_tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(stats_tbl)

        # Recommended next steps
        story.append(Spacer(1, 0.5*cm))
        if narrative.get("recommended_next_steps"):
            story.append(Paragraph("Recommended Next Steps", h2))
            story.append(Paragraph(narrative["recommended_next_steps"], normal))

        doc.build(story)
        return buf.getvalue()
    except ImportError:
        # ReportLab not available — return a minimal text PDF substitute
        text = (
            f"Skill Pilot AI Career Readiness Report\n"
            f"Student: {data['student_name']}\n"
            f"Career Goal: {data['career_role']}\n"
            f"Readiness: {data['readiness_score']:.0f}%\n"
            f"Generated: {data['generated_at'][:10]}\n"
        )
        return text.encode()


class ReportService:
    @staticmethod
    async def generate(db: AsyncSession, profile_id: int, report_type: str) -> Dict[str, Any]:
        data = await _build_report_data(db, profile_id)
        narrative = await ReportSummaryAgent.run(data)

        # Save record
        report = CareerReadinessReport(
            student_profile_id=profile_id,
            report_type=report_type,
            report_data={**data, "narrative": narrative},
            generated_at=datetime.now(timezone.utc),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        return {"report_id": report.id, "data": data, "narrative": narrative}

    @staticmethod
    async def download_pdf(db: AsyncSession, profile_id: int, report_id: int) -> bytes:
        res = await db.execute(
            select(CareerReadinessReport).where(
                CareerReadinessReport.id == report_id,
                CareerReadinessReport.student_profile_id == profile_id,
            )
        )
        report = res.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        data = report.report_data
        narrative = data.get("narrative", {})
        return _build_pdf(data, narrative)

    @staticmethod
    async def download_json(db: AsyncSession, profile_id: int, report_id: int) -> Dict[str, Any]:
        res = await db.execute(
            select(CareerReadinessReport).where(
                CareerReadinessReport.id == report_id,
                CareerReadinessReport.student_profile_id == profile_id,
            )
        )
        report = res.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        # Strip sensitive fields
        safe = {k: v for k, v in report.report_data.items()
                if k not in ("user_id", "hashed_password", "access_token")}
        return safe

    @staticmethod
    async def list_reports(db: AsyncSession, profile_id: int) -> list:
        res = await db.execute(
            select(CareerReadinessReport)
            .where(CareerReadinessReport.student_profile_id == profile_id)
            .order_by(CareerReadinessReport.generated_at.desc())
        )
        return [
            {"id": r.id, "report_type": r.report_type,
             "generated_at": r.generated_at.isoformat()}
            for r in res.scalars().all()
        ]
