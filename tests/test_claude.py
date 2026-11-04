"""The Claude plugin on fake answers: it loads as an assistant plugin, its tables hold together, its
requests carry the key and a digest of the account (never the email), its answers are read with
every usage figure, its errors are the API's types, Connect reads the tier from the headers, and the
free plan sends nothing."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pytest

from liminal_lib.assistants import Answer, Question, Usage, evaluate
from liminal_lib.errors import NotEntitled, SourceError, Unauthorized
from liminal_lib.ratelimit import fingerprint

import platform_plugin_claude as claude
from platform_plugin_claude import ASSISTANT, MODELS, PLANS, SOURCES, ClaudePlugin

from conftest import FakeResponse, FakeSession

NOW = datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc)
KEY, EMAIL = "sk-ant-test-key-000", "me@example.com"


def message(text, model="claude-haiku-5-5", stop="end_turn", input_tokens=100, output=30, cache_read=20, cache_write=5,
            headers=None):
    body = {"id": "msg_1", "type": "message", "role": "assistant", "model": model, "stop_reason": stop,
            "content": [{"type": "text", "text": text}],
            "usage": {"input_tokens": input_tokens, "output_tokens": output, "cache_read_input_tokens": cache_read,
                      "cache_creation_input_tokens": cache_write}}
    return FakeResponse(200, body, headers or {"request-id": "req_abc"})


def models(*ids, headers=None):
    return FakeResponse(200, {"data": [{"id": i, "display_name": i, "lifecycle": "active", "type": "model"} for i in ids],
                              "has_more": False}, headers or {})


def error(status, kind, msg, **details):
    err = {"type": kind, "message": msg}
    if details:
        err["details"] = details
    return FakeResponse(status, {"type": "error", "error": err}, {"request-id": "req_err"})


def test_it_loads_as_an_assistant_plugin(installed):
    found = installed(ASSISTANT)
    assert list(found) == ["claude"] and isinstance(found["claude"], ClaudePlugin)
    p = found["claude"]
    assert p.KIND == "assistant" and p.SYSTEM == "platform" and p.api == "2.0" and p.vendor == "Anthropic"
    assert p.origin == "package: platform_plugin_claude"
    assert [k.name for k in p.keys] == ["CLAUDE_API_KEY", "CLAUDE_ACCOUNT"] and p.keys[0].aliases == ("ANTHROPIC_API_KEY",)
    assert p.plan_vars == ("CLAUDE_PLAN", "CLAUDE_MODEL", "CLAUDE_REQUESTS_PER_DAY", "CLAUDE_TOKENS_PER_DAY")
    assert p.options == ("CLAUDE_MAX_OUTPUT_TOKENS", "CLAUDE_EFFORT") and p.has_scan and p.has_settings
    from liminal_lib.sources import registry

    assert registry.errors() == []
    assert set(registry.variables()) >= {"CLAUDE_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_ACCOUNT", "CLAUDE_PLAN", "CLAUDE_EFFORT"}


def test_the_tables_hold_together():
    assert PLANS[0].name == "free" and not PLANS[0].api_access and "Console" in PLANS[0].note
    assert [p.name for p in PLANS] == ["free", "evaluation", "start", "build", "scale", "custom"]
    assert all(m.input_usd > 0 and m.output_usd > 0 and (m.cached_usd or 0) >= 0 for m in MODELS)
    assert all(ASSISTANT.plan_of(n) is not None for m in MODELS for n in m.plans)
    assert MODELS[0].id == "claude-haiku-5-5" == ASSISTANT.default_model and ASSISTANT.plan_choices["CLAUDE_MODEL"][0] == "claude-haiku-5-5"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", claude.VERIFIED) and ASSISTANT.verified == claude.VERIFIED
    assert all(s.url.startswith("https://platform.claude.com/") and s.sentinel and s.markers for s in SOURCES)
    assert ASSISTANT.cost("claude-haiku-5-5", Usage(1_000_000, 0)) == 0.1 and ASSISTANT.cost("claude-opus-5-5", Usage(0, 1_000_000)) == 20.0
    assert {p.rpm for p in PLANS if p.rpm} == {4000, 10000, 13000}  # the tiers Connect can tell apart


def test_the_request_carries_the_key_the_digest_and_no_sampling(installed, settings_for, tmp_path):
    installed(ASSISTANT)
    settings = settings_for(ANTHROPIC_API_KEY=KEY, CLAUDE_ACCOUNT=EMAIL, CLAUDE_PLAN="start", CLAUDE_EFFORT="low",
                            CLAUDE_MAX_OUTPUT_TOKENS="512")
    own = settings.plugin("claude")
    assert own.has_key and own.plan == "start" and own.model == "claude-haiku-5-5" and own.caps.max_output_tokens == 512
    session = FakeSession(message("The exchange is closed.\nVerdict: no"))
    q = Question("Is the market open?", answer=Answer("verdict", scale=("yes", "no")))
    ev = evaluate(q, settings, assistant="claude", session=session, now=lambda: NOW)
    (call,) = session.calls
    method, url, _, body, headers = call
    assert method == "POST" and url == "https://api.anthropic.com/v1/messages"
    assert headers == {"x-api-key": KEY, "anthropic-version": "2026-10-21", "content-type": "application/json"}
    assert body["model"] == "claude-haiku-5-5" and body["max_tokens"] == 512 and body["system"].startswith("You are an analyst's assistant")
    assert body["messages"] == [{"role": "user", "content": "Question: Is the market open?"}]
    assert body["metadata"] == {"user_id": fingerprint(EMAIL)} and body["output_config"] == {"effort": "low"}
    assert "temperature" not in body and "thinking" not in body and EMAIL not in json.dumps(body)
    assert ev.assistant == "claude" and ev.provider == "Anthropic" and ev.model == "claude-haiku-5-5" and ev.verdict == "no"
    assert ev.usage == Usage(125, 30, 20, 0) and ev.request_id == "msg_1" and ev.stop == "end_turn" and ev.ok
    assert ev.cost_usd == pytest.approx(MODELS[0].cost(Usage(125, 30, 20, 0)))
    cut = FakeSession(message("Verdict: yes", stop="max_tokens"))
    assert evaluate(q, settings, assistant="claude", session=cut, now=lambda: NOW).stop == "length"
    declined = FakeSession(message("", stop="refusal"))
    out = evaluate(q, settings, assistant="claude", session=declined, now=lambda: NOW)
    assert out.stop == "refusal" and out.verdict is None and not out.ok
    quiet = settings_for(CLAUDE_API_KEY=KEY, CLAUDE_PLAN="start")  # no account, no effort: neither field sent
    session = FakeSession(message("ok"))
    evaluate(Question("x"), quiet, assistant="claude", session=session, now=lambda: NOW)
    assert "metadata" not in session.calls[0][3] and "output_config" not in session.calls[0][3]


def test_the_free_plan_sends_nothing_and_says_why(installed, settings_for):
    installed(ASSISTANT)
    settings = settings_for(CLAUDE_API_KEY=KEY)
    p = settings.plugin("claude")
    assert p.plan == "free" and ASSISTANT.keys_set(settings) and not ASSISTANT.served(settings)
    assert ASSISTANT.free_note(settings).startswith("the No API plan plan has no API access: a Claude.ai subscription")
    session = FakeSession()
    with pytest.raises(NotEntitled, match="No API plan plan has no API access"):
        evaluate(Question("x"), settings, assistant="claude", session=session)
    assert session.calls == []
    with pytest.raises(Unauthorized, match="no key"):
        evaluate(Question("x"), settings_for(CLAUDE_PLAN="start"), assistant="claude", session=session)


def test_the_apis_errors_are_mapped_and_the_final_ones_not_tried_again(installed, settings_for):
    installed(ASSISTANT)
    settings = settings_for(CLAUDE_API_KEY=KEY, CLAUDE_ACCOUNT=EMAIL, CLAUDE_PLAN="start")

    def run(*responses):
        session = FakeSession(*responses)
        a = ASSISTANT.build(settings, session=session, now=lambda: NOW)
        a.client._sleep = lambda s: None
        try:
            a.evaluate(Question("x"))
        except SourceError as e:
            return type(e), e.message, len(session.calls)
        return None, "", len(session.calls)

    kind, msg, n = run(error(401, "authentication_error", f"invalid x-api-key {KEY}"))
    assert kind is Unauthorized and n == 1 and KEY not in msg
    kind, msg, n = run(error(429, "rate_limit_error", "You have reached your API usage limits", error_code="enforced_spend_limit_reached"))
    assert kind is NotEntitled and "monthly spend cap" in msg and n == 1  # final: not tried again
    kind, msg, n = run(error(400, "invalid_request_error", "You have reached your specified API usage limits"))
    assert kind is NotEntitled and "your own spend limit" in msg
    kind, msg, n = run(error(404, "not_found_error", "model: claude-haiku-5-5"))
    assert kind is NotEntitled and "choose one from Connect's list" in msg
    kind, msg, n = run(error(403, "permission_error", "Your API key does not have permission"))
    assert kind is NotEntitled
    over = error(529, "overloaded_error", "Overloaded")
    kind, msg, n = run(over, over, over, over, over)
    assert kind is SourceError and n == 5  # tried again as a 5xx, then given up


def test_connect_reads_the_tier_from_the_headers_and_checks_the_models(installed, settings_for):
    installed(ASSISTANT)
    settings = settings_for(CLAUDE_API_KEY=KEY, CLAUDE_PLAN="evaluation")
    limits = {"anthropic-ratelimit-requests-limit": "4000", "anthropic-ratelimit-input-tokens-limit": "2000000",
              "anthropic-ratelimit-output-tokens-limit": "400000", "request-id": "req_9"}
    session = FakeSession(models("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-haiku-4-5"),
                          message("OK", input_tokens=12, output=1, cache_read=0, cache_write=0, headers=limits))
    scanned = ASSISTANT.run_scan(ASSISTANT.build(settings, session=session, now=lambda: NOW))
    rows = {w: (ok, d) for w, ok, d in scanned.results}
    assert rows["the key"] == (True, "accepted: 4 models listed by the server") and rows["the model claude-haiku-5-5"][0]
    assert rows["the table's models"] == (False, "no longer listed by the server: claude-fable-5-1 (the table is stale: update the plugin)")
    assert rows["models not in the table"] == (True, "claude-haiku-4-5") and rows["an answer"][0] and "13 tokens" in rows["an answer"][1]
    assert rows["its plan"] == (True, "the server allows 4,000 requests a minute and 2,000,000 tokens a minute: the Start tier plan")
    assert scanned.plan == {"CLAUDE_PLAN": "start"} and scanned.limits["perMinute"] == 4000
    assert session.calls[0][:2] == ("GET", "https://api.anthropic.com/v1/models") and session.calls[0][4]["x-api-key"] == KEY
    assert session.calls[1][3]["max_tokens"] == 16 and session.calls[1][3]["system"] == "Reply with the single word OK."
    from liminal_lib.config import with_detected

    assert with_detected(settings, scanned.plan).plugin("claude").plan == "evaluation"  # your own choice wins
    applied = with_detected(settings_for(CLAUDE_API_KEY=KEY), scanned.plan)  # no choice: the tier found applies
    assert applied.plugin("claude").plan == "start" and ASSISTANT.rate_window(applied) == (4000, 60.0)
