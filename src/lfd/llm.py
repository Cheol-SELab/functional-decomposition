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
        max_output_tokens: int = 2048,
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
        max_output_tokens: int = 2048,
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
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Model did not return valid JSON: {text[:500]}") from e


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
        max_output_tokens: int = 2048,
        timeout_s: float = 60.0,
    ) -> Dict[str, Any]:
        if self.sleep_s:
            time.sleep(self.sleep_s)

        for k, v in self.scripted.items():
            if k in user:
                return v
        raise KeyError("No mock response matched user prompt")
