"""Provider-agnostic BaseAgent with xAI Grok Structured Outputs.

All agents inherit from this class.  The call_structured_output method:
  - Uses xAI Grok (or OpenAI fallback) with response_format json_schema.
  - Validates the response with the caller-supplied Pydantic model.
  - Returns None on any failure so callers can apply deterministic fallbacks.
  - Never raises to the caller; never logs API keys.
"""
import json
import logging
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from app.core.ai_client import get_ai_client, get_active_model

logger = logging.getLogger("skillpilot.agents")
T = TypeVar("T", bound=BaseModel)


def _build_json_schema(model: Type[BaseModel], agent_name: str) -> dict:
    """Build a strict JSON-schema object from a Pydantic model for Grok Structured Outputs."""
    raw = model.model_json_schema()
    return {
        "type": "json_schema",
        "json_schema": {
            "name": agent_name,
            "strict": True,
            "schema": raw,
        },
    }


class BaseAgent:
    # Subclasses can override to customise the agent name used in json_schema.
    agent_name: str = "skillpilot_agent"

    @classmethod
    async def call_structured_output(
        cls,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        agent_name: Optional[str] = None,
    ) -> Optional[T]:
        client = get_ai_client()
        if not client:
            logger.info("No AI provider configured — using deterministic fallback.")
            return None

        name = agent_name or cls.agent_name
        response_format = _build_json_schema(response_model, name)
        model = get_active_model()

        try:
            completion = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_format,
                temperature=0.2,
            )
            raw_content = completion.choices[0].message.content
            if not raw_content:
                logger.warning(f"[{name}] Empty response from AI provider.")
                return None
            data = json.loads(raw_content)
            return response_model.model_validate(data)
        except json.JSONDecodeError as e:
            logger.warning(f"[{name}] JSON decode error: {e}")
        except Exception as e:
            # Mask credentials in log message
            safe_msg = str(e).replace(
                getattr(client, "api_key", ""), "***"
            ) if hasattr(client, "api_key") else str(e)
            logger.warning(f"[{name}] AI call failed ({type(e).__name__}): {safe_msg[:200]}")
        return None
