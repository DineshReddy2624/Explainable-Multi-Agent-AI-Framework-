import logging
import requests
import json
import time
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)


class LLMResponse:
    def __init__(self, content: str, model: str, provider: str, tokens_used: int = 0, latency_ms: float = 0.0):
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens_used = tokens_used
        self.latency_ms = latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms
        }


class BaseLLMProvider:
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.0) -> LLMResponse:
        raise NotImplementedError("Subclasses must implement generate()")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.0) -> LLMResponse:
        start_t = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": getattr(settings, "LLM_MAX_TOKENS", 1024)
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            latency = round((time.time() - start_t) * 1000, 2)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                logger.info(f"OpenAI LLM response received ({latency}ms, {tokens} tokens).")
                return LLMResponse(content=content, model=self.model, provider="openai", tokens_used=tokens, latency_ms=latency)
            else:
                logger.error(f"OpenAI API Error ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"OpenAI API call failed with status code {resp.status_code}")
        except Exception as e:
            logger.error(f"OpenAI Generation Exception: {str(e)}")
            raise


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434", timeout: int = 30):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.0) -> LLMResponse:
        start_t = time.time()
        url = f"{self.base_url}/api/generate"
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            latency = round((time.time() - start_t) * 1000, 2)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("response", "")
                return LLMResponse(content=content, model=self.model, provider="ollama", tokens_used=0, latency_ms=latency)
            else:
                raise RuntimeError(f"Ollama call failed with status code {resp.status_code}")
        except Exception as e:
            logger.error(f"Ollama Generation Exception: {str(e)}")
            raise


_quota_exhausted_models = {}

class GeminiProvider(BaseLLMProvider):
    """Google Gemini free-tier provider with ultra-fast sub-second multi-model fallback."""
    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest", timeout: int = 15):
        self.api_key = api_key.strip("'\"")
        self.primary_model = model
        self.fallback_models = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemma-4-26b-a4b-it"]
        self.timeout = timeout

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> LLMResponse:
        start_t = time.time()
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096
            }
        }

        now = time.time()
        last_err = None

        for target_model in self.fallback_models:
            # Skip model if flagged 429 within last 120 seconds
            if target_model in _quota_exhausted_models and (now - _quota_exhausted_models[target_model]) < 120:
                continue

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                latency = round((time.time() - start_t) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    candidate = data["candidates"][0]
                    parts = candidate.get("content", {}).get("parts", [])
                    text_parts = []
                    for part in parts:
                        txt = part.get("text", "").strip()
                        if txt:
                            text_parts.append(txt)
                    content = "\n".join(text_parts).strip()
                    tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                    logger.info(f"Gemini LLM ({target_model}) response received ({latency}ms, {tokens} tokens).")
                    return LLMResponse(content=content, model=target_model, provider="gemini", tokens_used=tokens, latency_ms=latency)
                elif resp.status_code == 429:
                    logger.warning(f"Model {target_model} hit 429 quota. Caching 429 cooldown & switching model...")
                    _quota_exhausted_models[target_model] = time.time()
                    continue
                else:
                    last_err = f"Gemini API Error ({resp.status_code}): {resp.text}"
                    logger.warning(f"Model {target_model} returned {last_err}")
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Model {target_model} Exception: {last_err}")

        # Final fallback if all quota exhausted: clear cache and try last model
        _quota_exhausted_models.clear()
        raise RuntimeError(f"Gemini API call failed across all fallback models: {last_err}")



class GroqProvider(BaseLLMProvider):
    """Groq Cloud LLM provider using OpenAI-compatible API."""
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7) -> LLMResponse:
        start_t = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 512
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            latency = round((time.time() - start_t) * 1000, 2)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                logger.info(f"Groq LLM response received ({latency}ms, {tokens} tokens).")
                return LLMResponse(content=content, model=self.model, provider="groq", tokens_used=tokens, latency_ms=latency)
            else:
                logger.error(f"Groq API Error ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"Groq API call failed with status code {resp.status_code}")
        except Exception as e:
            logger.error(f"Groq Generation Exception: {str(e)}")
            raise


class MockLLMProvider(BaseLLMProvider):
    """Deterministic, keyless fallback LLM synthesis provider."""
    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.0) -> LLMResponse:
        content = "Synthesized dataset analysis response based strictly on tool execution results."
        return LLMResponse(content=content, model="mock-model", provider="mock", tokens_used=0, latency_ms=1.0)


class LLMFactory:
    @staticmethod
    def get_provider() -> BaseLLMProvider:
        gemini_key = getattr(settings, "GEMINI_API_KEY", "")
        groq_key = getattr(settings, "GROQ_API_KEY", "")
        provider_name = getattr(settings, "LLM_PROVIDER", "mock").lower()
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        model_name = getattr(settings, "LLM_MODEL", "gpt-4o-mini")

        # Priority 1: Gemini (free tier)
        if gemini_key:
            try:
                return GeminiProvider(api_key=gemini_key)
            except Exception:
                pass

        # Priority 2: Groq (free tier)
        if groq_key:
            try:
                return GroqProvider(api_key=groq_key)
            except Exception:
                pass

        # Priority 3: OpenAI
        if provider_name == "openai" and api_key:
            try:
                return OpenAIProvider(api_key=api_key, model=model_name)
            except Exception:
                pass

        # Priority 4: Ollama (local)
        elif provider_name == "ollama":
            try:
                return OllamaProvider(model=model_name)
            except Exception:
                pass

        # Fallback: smart template
        return MockLLMProvider()


llm_factory = LLMFactory()
