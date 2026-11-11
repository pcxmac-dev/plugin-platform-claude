"""What the plugin attaches to (plugin API 2.2, apis.py): the Claude API's card is sound, says how a key is sent, the
limits, the prices, the status page and the Console's key page, names the requests Connect and an evaluation really
send (read from a fake session's record) among the API's others, and every address on it is Anthropic's own. The page
check is the weekly one (tests/test_vendor_pages.py, LIMINAL_VENDOR_PAGES=1); nothing is sent here. The user,
2026-11-11: "each plugin should reflect the the API its attached to, and present links that provide documentation"."""
from __future__ import annotations

from datetime import date, datetime, timezone
from urllib.parse import urlsplit

from liminal_libs.sources.apis import problems, urls

import plugin_platform_claude as claude
from plugin_platform_claude import ASSISTANT
from plugin_platform_claude.apis import APIS, CLAUDE_API

from conftest import FakeResponse, FakeSession

NOW = datetime(2026, 11, 11, 15, 0, tzinfo=timezone.utc)
KEY = "sk-ant-test-key-000"


def test_the_card_is_sound_and_is_the_plugins():
    assert problems(APIS, today=date(2026, 11, 11)) == []
    assert ASSISTANT.apis == APIS and claude.ClaudePlugin.apis is APIS and claude.APIS is APIS
    assert CLAUDE_API.base == claude.API and claude.API_VERSION in CLAUDE_API.version and CLAUDE_API.verified == "2026-11-11"
    assert CLAUDE_API.link("console") == "https://platform.claude.com/settings/keys"
    assert all(CLAUDE_API.link(k) for k in ("docs", "reference", "auth", "limits", "pricing", "status", "changelog"))
    assert "x-api-key" in CLAUDE_API.auth and "4,000" in CLAUDE_API.limits and "$0.10" in CLAUDE_API.costs
    assert ASSISTANT.interface()["apis"] == ["Claude API"]
    assert ASSISTANT.api_facts() == {}  # the instance keeps nothing of a run: each Connect builds its own Assistant


def test_the_card_names_the_requests_the_plugin_really_sends(installed, settings_for):
    """A full Connect (the models list, then one answer of a few tokens) sends exactly the calls the card says it
    uses, as method and path on the card's base; an evaluation's answer is the same POST."""
    installed(ASSISTANT)
    settings = settings_for(CLAUDE_API_KEY=KEY, CLAUDE_PLAN="start")
    session = FakeSession(
        FakeResponse(200, {"data": [{"id": "claude-haiku-5-5", "display_name": "Claude Haiku 5.5"}], "has_more": False}),
        FakeResponse(200, {"id": "msg_1", "type": "message", "model": "claude-haiku-5-5", "stop_reason": "end_turn",
                           "content": [{"type": "text", "text": "OK"}], "usage": {"input_tokens": 12, "output_tokens": 1}},
                     {"request-id": "req_1"}))
    ASSISTANT.run_scan(ASSISTANT.build(settings, session=session, now=lambda: NOW))
    sent = {f"{method} {url.removeprefix(CLAUDE_API.base)}" for method, url, *_ in session.calls}
    assert sent == {c.name for c in CLAUDE_API.used} == {"POST /v1/messages", "GET /v1/models"}
    used = {c.name: c for c in CLAUDE_API.used}
    assert used["POST /v1/messages"].costs and not used["GET /v1/models"].costs  # an answer is billed, the list is not
    assert {a.name for a in CLAUDE_API.covered} == {"Messages", "Models"}
    assert all(c.area in {a.name for a in CLAUDE_API.areas} for c in CLAUDE_API.calls)
    assert len(CLAUDE_API.areas) > 2 * len(CLAUDE_API.covered) and len(CLAUDE_API.calls) > 2 * len(CLAUDE_API.used)


def test_every_address_is_anthropics_own():
    hosts = {urlsplit(u).hostname for u in urls(APIS)}
    assert hosts == {"platform.claude.com", "status.claude.com", "github.com", "www.anthropic.com"}
    assert all(u.startswith("https://github.com/anthropics/") for u in urls(APIS) if "github.com" in u)
