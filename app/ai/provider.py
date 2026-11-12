from typing import Protocol

from app.settings import Settings


class AiNotConfigured(Exception):
    pass


class AiGenerationError(Exception):
    pass


class AiProvider(Protocol):
    def generate_text(self, prompt: str) -> str: ...


class NotConfiguredProvider:
    def generate_text(self, prompt: str) -> str:
        raise AiNotConfigured("AI is not configured. Set GEMINI_API_KEY to enable generation.")


def get_ai_provider(settings: Settings) -> AiProvider:
    if not settings.gemini_api_key:
        return NotConfiguredProvider()
    from app.ai.gemini_provider import GeminiProvider

    return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
