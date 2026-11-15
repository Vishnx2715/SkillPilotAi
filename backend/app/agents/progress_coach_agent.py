from typing import List, Literal, Dict, Any
from pydantic import BaseModel
from app.agents.base_agent import BaseAgent
from app.schemas.assessment import WeakTopicItem


class WeakAreaItem(BaseModel):
    skill: str
    subtopic: str
    mastery: float
    recommended_action: str


class RoadmapChangeItem(BaseModel):
    module_title: str
    action: Literal["lock", "unlock", "add_revision", "keep"]
    reason: str


class ProgressCoachOutput(BaseModel):
    overall_status: Literal["on_track", "needs_support", "at_risk"]
    weak_areas: List[WeakAreaItem]
    roadmap_changes: List[RoadmapChangeItem]
    next_best_action: str
    mentor_message: str


class ProgressCoachAgent(BaseAgent):
    SYSTEM_PROMPT = """
You are an encouraging and supportive AI Career & Progress Coach for Skill Pilot AI.
Analyze diagnostic test performance, explain why certain modules stay locked or require revision,
and provide encouraging, actionable guidance.
"""

    @classmethod
    async def run(
        cls,
        skill_name: str,
        mastery: float,
        weak_topics: List[WeakTopicItem],
        roadmap_changes: List[Dict[str, Any]],
        fallback_action: str,
        fallback_msg: str
    ) -> Dict[str, str]:
        user_prompt = f"""
Assessed Skill: {skill_name}
Mastery: {mastery}%
Identified Weak Topics: {[w.model_dump() for w in weak_topics]}
Deterministic Roadmap Actions: {roadmap_changes}

Deliver an encouraging mentor message and the next best action.
"""
        parsed = await cls.call_structured_output(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ProgressCoachOutput
        )

        if not parsed:
            return {
                "next_best_action": fallback_action,
                "mentor_message": fallback_msg
            }

        return {
            "next_best_action": parsed.next_best_action or fallback_action,
            "mentor_message": parsed.mentor_message or fallback_msg
        }

