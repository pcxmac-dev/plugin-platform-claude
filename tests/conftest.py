"""Fakes and guards: tests never read the user's saved keys, never touch the machine's real ledgers,
and never send a request (a FakeSession answers)."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def no_saved_keys(monkeypatch, tmp_path):
    """Tests never read the user's saved keys (their user environment variables), never load the
    workspace's plugin directory, and count on scratch ledgers."""
    from liminal_libs import config, layout

    monkeypatch.setattr(config, "saved_user_keys", lambda: {})
    monkeypatch.setattr(layout, "plugins_dir", lambda: None)
    monkeypatch.setenv("LIMINAL_LIVE_LOCK", str(tmp_path / "machine" / "live.lock"))


class FakeResponse:
    def __init__(self, status: int = 200, body=None, headers: dict | None = None):
        self.status_code = status
        self._body = body if body is not None else {}
        self.headers = headers or {}
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


class FakeSession:
    """Queued answers; every request recorded as (method, url, params, json, headers)."""

    def __init__(self, *responses: FakeResponse):
        self.responses = list(responses)
        self.calls: list[tuple] = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(("GET", url, params, None, headers))
        return self.responses.pop(0)

    def post(self, url, params=None, json=None, headers=None, timeout=None):
        self.calls.append(("POST", url, params, json, headers))
        return self.responses.pop(0)


@pytest.fixture
def installed(monkeypatch):
    """The plugin loaded as an installed package's entry point, as the app loads it."""
    from liminal_libs.sources import registry

    def install(*plugins):
        eps = [SimpleNamespace(name=p.name, value=f"plugin_platform_{p.name}", load=(lambda p=p: p)) for p in plugins]
        monkeypatch.setattr(registry, "_entry_points", lambda: eps)
        registry.reload()
        return registry.assistants()

    yield install
    registry._providers = None


@pytest.fixture
def settings_for(tmp_path):
    from liminal_libs.config import load_settings

    def make(**env):
        return load_settings(env={"LIMINAL_DB": str(tmp_path / "m.db"), **env}, env_file=None)
    return make
