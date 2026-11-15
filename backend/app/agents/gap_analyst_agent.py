from typing import List
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.models.profile import StudentProfile
from app.models.career import RoleSkillRequirement
from app.schemas.skill import GapAnalysisResponse, GapItem, StrengthItem


class GapAnalystOutput(BaseModel):
    readiness_score: int
    strengths: List[StrengthItem]
    gaps: List[GapItem]
    next_best_action: str
    summary: str


class GapAnalystAgent(BaseAgent):
    SYSTEM_PROMPT = """
You are an expert AI Career Gap Analyst for Skill Pilot AI.
Your role is to evaluate a learner's existing skills against target career role requirements.
Produce an explainable, evidence-based skill gap analysis.
Rules:
1. Always preserve calculated readiness_score and verified mastery percentages.
2. Provide human-readable, empowering explanations for every gap and strength.
3. Identify blocking skills where low mastery delays downstream prerequisite learning.
4. Recommend a clear, high-leverage next best action.
"""

    @classmethod
    async def run(
        cls,
        profile: StudentProfile,
        requirements: List[RoleSkillRequirement],
        fallback: GapAnalysisResponse
    ) -> GapAnalysisResponse:
        user_prompt = f"""
Student Name: {profile.full_name}
Target Career Role: {profile.target_role.name if profile.target_role else "Unknown"}
Weekly Study Hours: {profile.weekly_study_hours}
Experience Level: {profile.experience_level or "Beginner"}
Self-Reported / Verified Skills: {[f"{ls.skill.name}: {ls.mastery_percentage:.0f}% (level {ls.verified_level})" for ls in profile.learner_skills]}

Deterministic Base Analysis:
- Calculated Readiness Score: {fallback.readiness_score}
- Strengths: {[s.model_dump() for s in fallback.strengths]}
- Gaps: {[g.model_dump() for g in fallback.gaps]}
- Recommended Next Action: {fallback.next_best_action}

Please provide the final structured gap analysis JSON. Keep the readiness_score as {fallback.readiness_score}.
"""
        parsed = await cls.call_structured_output(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=GapAnalystOutput
        )

        if not parsed:
            return fallback

        # Ensure deterministic readiness score cannot be overridden
        parsed.readiness_score = fallback.readiness_score
        return GapAnalysisResponse(
            readiness_score=parsed.readiness_score,
            strengths=parsed.strengths if parsed.strengths else fallback.strengths,
            gaps=parsed.gaps if parsed.gaps else fallback.gaps,
            next_best_action=parsed.next_best_action or fallback.next_best_action,
            summary=parsed.summary or fallback.summary
        )

