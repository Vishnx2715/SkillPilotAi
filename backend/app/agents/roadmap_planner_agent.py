from typing import List
from pydantic import BaseModel
from app.agents.base_agent import BaseAgent


class AgentResource(BaseModel):
    title: str
    url: str
    resource_type: str
    difficulty: str
    estimated_minutes: int
    reason: str


class AgentModule(BaseModel):
    title: str
    skill: str
    description: str
    estimated_hours: float
    resources: List[AgentResource] = []
    practical_task: str
    reason: str


class AgentPhase(BaseModel):
    phase: int
    title: str
    objective: str
    estimated_hours: float
    modules: List[AgentModule]


class RoadmapPlannerOutput(BaseModel):
    career_role: str
    readiness_score: float
    phases: List[AgentPhase]
    next_best_action: str


class RoadmapPlannerAgent(BaseAgent):
    SYSTEM_PROMPT = """
You are an expert AI Roadmap Planner for Skill Pilot AI.
Your role is to personalize phase objectives, module explanations, and practical tasks.
Rules:
1. Never invent prerequisite relationships that conflict with the provided graph.
2. Respect the learner's weekly study hours and preserve max 5 phases.
3. Every phase must contain a clear milestone and practical exercise or mini project.
4. Output must conform strictly to the JSON schema.
"""

    @classmethod
    async def run(
        cls,
        career_role: str,
        readiness_score: float,
        weekly_study_hours: int,
        phases_summary: str,
        fallback_action: str
    ) -> RoadmapPlannerOutput:
        user_prompt = f"""
Career Role: {career_role}
Current Readiness Score: {readiness_score}%
Weekly Study Hours: {weekly_study_hours}
Deterministic Roadmap Framework:
{phases_summary}

Please generate the personalized roadmap explanation and milestone objectives conforming to the JSON schema.
"""
        parsed = await cls.call_structured_output(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=RoadmapPlannerOutput
        )

        if not parsed:
            return RoadmapPlannerOutput(
                career_role=career_role,
                readiness_score=readiness_score,
                phases=[],
                next_best_action=fallback_action
            )
        return parsed

