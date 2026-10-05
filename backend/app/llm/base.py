from abc import ABC, abstractmethod
import json
import re
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

def clean_json_response(raw_text: str) -> str:
    """
    Strips markdown code fences (```json ... ```) or leading/trailing commentary.
    """
    text = raw_text.strip()
    # Match ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    return text

class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
    ) -> Dict[str, Any]:
        """
        Generates structured JSON adhering to the specified Pydantic schema.
        """
        pass
