import json
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.llm.base import LLMProvider, clean_json_response

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.gemini_api_key
        self.model_name = model_name or self.settings.llm_model or "gemini-1.5-flash"
        self._client = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": 0.2,
                        "response_mime_type": "application/json",
                    },
                )
            except Exception as e:
                logger.warning(f"Could not initialize Google Generative AI client: {e}")

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
    ) -> Dict[str, Any]:
        if not self._client or not self.api_key:
            raise AppError(
                code=ErrorCode.LLM_FAILED,
                message="Gemini API key is not configured.",
                status_code=503,
                retryable=False,
            )

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_prompt = f"""{system_prompt}

TARGET JSON SCHEMA:
{schema_json}

{user_prompt}
"""

        current_prompt = augmented_prompt
        last_error = None

        for attempt in range(2):
            try:
                # generate_content runs synchronously in thread
                import asyncio
                response = await asyncio.to_thread(
                    self._client.generate_content,
                    current_prompt,
                )
                raw_text = response.text
                cleaned = clean_json_response(raw_text)
                parsed = json.loads(cleaned)
                # Validate against schema
                validated = schema.model_validate(parsed)
                return validated.model_dump()
            except ValidationError as ve:
                last_error = ve
                current_prompt = f"{augmented_prompt}\n\nPREVIOUS RESPONSE HAD VALIDATION ERRORS:\n{str(ve)}\nPlease fix the errors and output valid JSON only."
            except Exception as e:
                last_error = e

        raise AppError(
            code=ErrorCode.LLM_FAILED,
            message=f"LLM generation failed after retries: {str(last_error)}",
            status_code=502,
            retryable=True,
        )
