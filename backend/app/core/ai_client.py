"""Provider-agnostic AI client.

Priority: xAI Grok (XAI_API_KEY) → OpenAI fallback (OPENAI_API_KEY) → None.
Never exposes API keys to callers; all key handling stays inside this module.
"""
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("skillpilot.ai")


def get_ai_client() -> Optional[AsyncOpenAI]:
    """Return the best available async AI client, or None if none is configured."""
    if settings.XAI_API_KEY and settings.XAI_API_KEY.strip():
        return AsyncOpenAI(
            api_key=settings.XAI_API_KEY,
            base_url=settings.XAI_BASE_URL,
            timeout=float(settings.AI_TIMEOUT_SECONDS),
        )
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        return AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=float(settings.OPENAI_TIMEOUT_SECONDS),
        )
    return None


def get_active_model() -> str:
    """Return the model identifier matching the configured client."""
    if settings.XAI_API_KEY and settings.XAI_API_KEY.strip():
        return settings.XAI_MODEL
    return settings.OPENAI_MODEL
