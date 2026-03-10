from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class LLMClient(Protocol):
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: int = 4096,
        timeout_s: float = 60.0,
    ) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class OpenAIResponsesClient:
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"

    def _key(self) -> str:
        key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return key

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: int = 4096,
        timeout_s: float = 60.0,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }

        if schema_hint is not None:
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": schema_hint.get("name", "output"),
                    "schema": schema_hint.get("schema", {}),
                    "strict": bool(schema_hint.get("strict", False)),
                }
            }
        else:
            payload["text"] = {"format": {"type": "json_object"}}

        json_max_attempts = 3
        for json_attempt in range(1, json_max_attempts + 1):
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url=f"{self.base_url}/responses",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self._key()}",
                    "Content-Type": "application/json",
                },
            )

            raw: Optional[str] = None
            last_error: Optional[BaseException] = None
            retryable_http = {408, 409, 425, 429, 500, 502, 503, 504}
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                        raw = resp.read().decode("utf-8")
                    last_error = None
                    break
                except urllib.error.HTTPError as e:
                    detail = e.read().decode("utf-8", errors="replace")
                    if e.code in retryable_http and attempt < max_attempts:
                        last_error = RuntimeError(f"OpenAI HTTPError {e.code}: {detail}")
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"OpenAI HTTPError {e.code}: {detail}") from e
                except urllib.error.URLError as e:
                    is_timeout = isinstance(getattr(e, "reason", None), socket.timeout)
                    if is_timeout and attempt < max_attempts:
                        last_error = e
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"OpenAI connection error: {e}") from e
                except (TimeoutError, socket.timeout) as e:
                    if attempt < max_attempts:
                        last_error = e
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"OpenAI request timed out: {e}") from e

            if raw is None:
                raise RuntimeError(f"OpenAI request failed after {max_attempts} attempts: {last_error}")

            data = json.loads(raw)

            text = None
            for item in data.get("output", []):
                for c in item.get("content", []):
                    if c.get("type") in ("output_text", "summary_text") and isinstance(c.get("text"), str):
                        text = c["text"]
                        break
                if text:
                    break

            if not text:
                raise RuntimeError("OpenAI response did not contain output text")

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                if json_attempt < json_max_attempts:
                    print(f"[OpenAI] Invalid JSON on attempt {json_attempt}, retrying...")
                    time.sleep(1.0 * json_attempt)
                    continue
                raise RuntimeError(f"Model did not return valid JSON after {json_max_attempts} attempts: {text[:500]}")
        raise RuntimeError("Unreachable")


@dataclass(frozen=True)
class AnthropicClient:
    api_key: Optional[str] = None
    base_url: str = "https://api.anthropic.com/v1"

    def _key(self) -> str:
        key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        return key

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: int = 4096,
        timeout_s: float = 60.0,
    ) -> Dict[str, Any]:
        resolved_model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

        messages = [{"role": "user", "content": user + "\n\nRespond with JSON only."}]

        payload: Dict[str, Any] = {
            "model": resolved_model,
            "max_tokens": max_output_tokens,
            "temperature": temperature,
            "system": system,
            "messages": messages,
        }

        json_max_attempts = 3
        for json_attempt in range(1, json_max_attempts + 1):
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url=f"{self.base_url}/messages",
                data=body,
                method="POST",
                headers={
                    "x-api-key": self._key(),
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
            )

            raw: Optional[str] = None
            last_error: Optional[BaseException] = None
            retryable_http = {408, 429, 500, 502, 503, 504, 529}
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                        raw = resp.read().decode("utf-8")
                    last_error = None
                    break
                except urllib.error.HTTPError as e:
                    detail = e.read().decode("utf-8", errors="replace")
                    if e.code in retryable_http and attempt < max_attempts:
                        last_error = RuntimeError(f"Anthropic HTTPError {e.code}: {detail}")
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"Anthropic HTTPError {e.code}: {detail}") from e
                except urllib.error.URLError as e:
                    is_timeout = isinstance(getattr(e, "reason", None), socket.timeout)
                    if is_timeout and attempt < max_attempts:
                        last_error = e
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"Anthropic connection error: {e}") from e
                except (TimeoutError, socket.timeout) as e:
                    if attempt < max_attempts:
                        last_error = e
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"Anthropic request timed out: {e}") from e

            if raw is None:
                raise RuntimeError(f"Anthropic request failed after {max_attempts} attempts: {last_error}")

            data = json.loads(raw)

            text = None
            for block in data.get("content", []):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    text = block["text"]
                    break

            if not text:
                raise RuntimeError("Anthropic response did not contain text output")

            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = lines[1:]  # remove opening ```json
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                if json_attempt < json_max_attempts:
                    print(f"[Anthropic] Invalid JSON on attempt {json_attempt}, retrying...")
                    time.sleep(1.0 * json_attempt)
                    continue
                raise RuntimeError(f"Model did not return valid JSON after {json_max_attempts} attempts: {text[:500]}")
        raise RuntimeError("Unreachable")


@dataclass(frozen=True)
class GoogleGeminiClient:
    api_key: Optional[str] = None

    def _key(self) -> str:
        key = self.api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        return key

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: int = 4096,
        timeout_s: float = 60.0,
    ) -> Dict[str, Any]:
        resolved_model = model or os.getenv("GOOGLE_MODEL", "gemini-3-flash-preview")
        api_key = self._key()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{resolved_model}:generateContent?key={api_key}"

        # Pro models require thinking mode, Flash models work with or without it
        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
        }
        
        # Only disable thinking for Flash models (Pro models require it)
        if "flash" in resolved_model.lower():
            generation_config["thinkingConfig"] = {"thinkingBudget": 0}
        
        payload: Dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user + "\n\nRespond with JSON only."}]}],
            "generationConfig": generation_config,
        }

        json_max_attempts = 3
        for json_attempt in range(1, json_max_attempts + 1):
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url=url,
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )

            raw: Optional[str] = None
            last_error: Optional[BaseException] = None
            retryable_http = {408, 429, 500, 502, 503, 504}
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                        raw = resp.read().decode("utf-8")
                    last_error = None
                    break
                except urllib.error.HTTPError as e:
                    detail = e.read().decode("utf-8", errors="replace")
                    if e.code in retryable_http and attempt < max_attempts:
                        last_error = RuntimeError(f"Gemini HTTPError {e.code}: {detail}")
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"Gemini HTTPError {e.code}: {detail}") from e
                except urllib.error.URLError as e:
                    is_timeout = isinstance(getattr(e, "reason", None), socket.timeout)
                    if is_timeout and attempt < max_attempts:
                        last_error = e
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"Gemini connection error: {e}") from e
                except (TimeoutError, socket.timeout) as e:
                    if attempt < max_attempts:
                        last_error = e
                        time.sleep(0.8 * attempt)
                        continue
                    raise RuntimeError(f"Gemini request timed out: {e}") from e

            if raw is None:
                raise RuntimeError(f"Gemini request failed after {max_attempts} attempts: {last_error}")

            data = json.loads(raw)

            text = None
            for candidate in data.get("candidates", []):
                content = candidate.get("content", {})
                for part in content.get("parts", []):
                    if isinstance(part.get("text"), str):
                        text = part["text"]
                        break
                if text:
                    break

            if not text:
                raise RuntimeError("Gemini response did not contain text output")

            text = text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                if json_attempt < json_max_attempts:
                    print(f"[Gemini] Invalid JSON on attempt {json_attempt}, retrying...")
                    time.sleep(1.0 * json_attempt)
                    continue
                raise RuntimeError(f"Model did not return valid JSON after {json_max_attempts} attempts: {text[:500]}")
        raise RuntimeError("Unreachable")


def make_llm_client(model: Optional[str] = None) -> "LLMClient":
    if model is None:
        return OpenAIResponsesClient()
    m = model.lower()
    if m.startswith("claude"):
        return AnthropicClient()
    if m.startswith("gemini"):
        return GoogleGeminiClient()
    return OpenAIResponsesClient()


@dataclass
class MockLLMClient:
    scripted: Dict[str, Dict[str, Any]]
    sleep_s: float = 0.0

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: int = 4096,
        timeout_s: float = 60.0,
    ) -> Dict[str, Any]:
        if self.sleep_s:
            time.sleep(self.sleep_s)

        for k, v in self.scripted.items():
            if k in user:
                return v
        raise KeyError("No mock response matched user prompt")
