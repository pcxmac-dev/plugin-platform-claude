"""Anthropic's Messages API through the contract's client (liminal_lib.assistants.Assistant): the
headers, the request body, the answer's shape, the error types and the rate-limit headers, as the
API documents them at https://platform.claude.com/docs (verified 2026-11-03; API version 2026-10-21:
no sampling parameters, thinking adaptive, `output_config.effort` for how much)."""
from __future__ import annotations

from typing import Any, Mapping

from liminal_lib.assistants import Assistant, Parsed, Prompt, Usage
from liminal_lib.assistants.assistant import header
from liminal_lib.errors import NotEntitled, SourceError, Unauthorized

API = "https://api.anthropic.com"
API_VERSION = "2026-10-21"  # the anthropic-version header: the API version this plugin was written for
STOPS = {"end_turn": "end_turn", "stop_sequence": "end_turn", "max_tokens": "length", "refusal": "refusal"}
FINAL_CODES = ("enforced_spend_limit_reached",)  # a 429 that is the month's cap, not a rate limit: no retry


class ClaudeAssistant(Assistant):
    """Claude: POST /v1/messages with the key in x-api-key; GET /v1/models; the limits in the
    anthropic-ratelimit-* headers; every usage figure counted (cache reads and writes among the input)."""

    base_url = API
    models_path = "/v1/models"
    answers_path = "/v1/messages"
    request_id_header = "request-id"
    limit_prefixes = ("anthropic-ratelimit-",)

    def headers(self, key: str) -> dict:
        return {"x-api-key": key, "anthropic-version": API_VERSION, "content-type": "application/json"}

    def body(self, prompt: Prompt, model: str, user_id: str) -> dict:
        body: dict = {"model": model, "max_tokens": int(prompt.max_tokens), "system": prompt.system,
                      "messages": [{"role": "user", "content": prompt.user}]}
        if user_id:
            body["metadata"] = {"user_id": user_id}  # a digest of the account: the field takes no identifying information
        if self.settings.effort:
            body["output_config"] = {"effort": self.settings.effort}
        return body

    def parse(self, raw: Mapping[str, Any]) -> Parsed:
        blocks = [b for b in (raw.get("content") or ()) if isinstance(b, Mapping)]
        text = "".join(str(b.get("text", "")) for b in blocks if b.get("type") == "text")
        stop = STOPS.get(str(raw.get("stop_reason") or "end_turn"), "end_turn")
        u = raw.get("usage") or {}
        cached = int(u.get("cache_read_input_tokens") or 0)
        written = int(u.get("cache_creation_input_tokens") or 0)
        usage = Usage(int(u.get("input_tokens") or 0) + cached + written, int(u.get("output_tokens") or 0), cached, 0)
        return Parsed(text, usage, stop, str(raw.get("id") or ""), str(raw.get("model") or ""), None, raw)

    def parse_models(self, raw: Mapping[str, Any]) -> list[dict]:
        return [{"id": str(m.get("id", "")), "title": str(m.get("display_name") or m.get("id", "")),
                 "lifecycle": str(m.get("lifecycle") or "")}
                for m in (raw or {}).get("data", []) if isinstance(m, Mapping) and m.get("id")]

    def error(self, status: int, body, message: str) -> SourceError | None:
        err = (body or {}).get("error") if isinstance(body, Mapping) else None
        err = err if isinstance(err, Mapping) else {}
        kind, msg = str(err.get("type") or ""), str(err.get("message") or message)
        code = str((err.get("details") or {}).get("error_code") or "") if isinstance(err.get("details"), Mapping) else ""
        if status == 401 or kind == "authentication_error":
            return Unauthorized(401, msg)
        if status == 404 or kind == "not_found_error":
            return NotEntitled(status or 404, f"no such model: {msg} (choose one from Connect's list)")
        if status in (402, 403) or kind in ("billing_error", "permission_error"):
            return NotEntitled(status, msg)
        if status == 429 and code in FINAL_CODES:
            return NotEntitled(429, f"the organization's monthly spend cap: {msg}")
        if status == 400 and msg.startswith("You have reached your specified"):
            return NotEntitled(400, f"your own spend limit (the Console's Billing page): {msg}")
        return None

    def final(self, status: int, body) -> bool:
        err = (body or {}).get("error") if isinstance(body, Mapping) else None
        err = err if isinstance(err, Mapping) else {}
        details = err.get("details") if isinstance(err.get("details"), Mapping) else {}
        return status == 429 and str(details.get("error_code") or "") in FINAL_CODES

    def limits_from(self, headers: Mapping[str, Any]) -> tuple[int | None, int | None]:
        rpm = _int(header(headers, "anthropic-ratelimit-requests-limit"))
        tpm = _int(header(headers, "anthropic-ratelimit-input-tokens-limit")) or _int(header(headers, "anthropic-ratelimit-tokens-limit"))
        return rpm, tpm


def _int(value) -> int | None:
    try:
        return int(float(str(value).strip())) if value not in (None, "") else None
    except ValueError:
        return None
