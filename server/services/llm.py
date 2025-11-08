from dotenv import load_dotenv
import os
import logging
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def call_llm(prompt: str, model: Optional[str] = None, temperature: float = 0.0, max_tokens: int = 512, **kwargs) -> str:
    if not prompt:
        raise ValueError("prompt must not be empty")

    provider = LLM_PROVIDER

    if provider == "google":
        try:
            from google import genai
        except ImportError as e:
            raise ImportError("google-genai SDK not installed. Please add it to requirements.") from e

        # Instantiate client. Some google-genai SDKs accept an api_key argument.
        client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else genai.Client()
        chosen_model = model or "gemini-1.0"
        # Call the SDK - adapt to your installed SDK version if needed
        resp = client.models.generate_content(model=chosen_model, contents=prompt, **kwargs)
        # Common SDKs expose text on resp.text, but adapt if different
        return getattr(resp, "text", str(resp))

    elif provider == "openai":
        try:
            import openai
        except ImportError as e:
            raise ImportError("openai SDK not installed. Please add it to requirements.") from e

        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY

        chosen_model = model or "gpt-4o"
        # Use ChatCompletion for typical chat-style prompts. Adjust if using new SDK.
        messages = [{"role": "user", "content": prompt}]
        resp = openai.ChatCompletion.create(model=chosen_model, messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs)
        if isinstance(resp, dict) and "choices" in resp and len(resp["choices"]) > 0:
            return resp["choices"][0]["message"]["content"]
        # Fallback: try attribute access or stringify
        return str(resp)

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
