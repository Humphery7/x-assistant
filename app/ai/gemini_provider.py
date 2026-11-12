from app.ai.provider import AiGenerationError


class GeminiProvider:
    def __init__(self, api_key: str, model: str):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_text(self, prompt: str) -> str:
        response = self._client.models.generate_content(model=self._model, contents=prompt)
        if not response.text:
            raise AiGenerationError("Gemini returned an empty response.")
        return response.text
