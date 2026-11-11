"""The weekly check (CI's schedule, LIMINAL_VENDOR_PAGES=1): Anthropic's public pricing and rate-limit
pages read again, each written-in figure looked for. A figure gone means the table is stale and the
plugin needs a release; the failure names the table. And every address on the plugin's card (apis.py)
asked once. Nothing is read on a push or a pull request."""
from __future__ import annotations

import os

import pytest

from liminal_libs.assistants.verify import check_sources
from plugin_platform_claude import ASSISTANT

pytestmark = pytest.mark.skipif(not os.environ.get("LIMINAL_VENDOR_PAGES"),
                                reason="LIMINAL_VENDOR_PAGES=1 reads the vendor's pages (the weekly CI run)")


def test_the_tables_still_match_anthropics_pages():
    problems = check_sources(ASSISTANT)
    assert problems == [], "\n".join(problems)


def test_every_address_on_the_card_answers():
    """Each address on the card asked once (sources.apis.dead_links). Anthropic's docs answer an HTML reader with a
    page for any path, so those are asked for as markdown, which answers 404 for a page that is gone."""
    import requests

    from liminal_libs.sources.apis import CHECK_AGENT, dead_links
    from plugin_platform_claude.apis import APIS

    def get(url: str, timeout: float) -> int:
        accept = "text/markdown" if url.startswith("https://platform.claude.com/docs/") else "text/html,*/*"
        with requests.get(url, timeout=timeout, stream=True, allow_redirects=True,
                          headers={"User-Agent": CHECK_AGENT, "Accept": accept}) as resp:
            return resp.status_code

    assert dead_links(APIS, get=get) == []
