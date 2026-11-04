"""The weekly check (CI's schedule, LIMINAL_VENDOR_PAGES=1): Anthropic's public pricing and rate-limit
pages read again, each written-in figure looked for. A figure gone means the table is stale and the
plugin needs a release; the failure names the table. Nothing is read on a push or a pull request."""
from __future__ import annotations

import os

import pytest

from liminal_lib.assistants.verify import check_sources
from platform_plugin_claude import ASSISTANT

pytestmark = pytest.mark.skipif(not os.environ.get("LIMINAL_VENDOR_PAGES"),
                                reason="LIMINAL_VENDOR_PAGES=1 reads the vendor's pages (the weekly CI run)")


def test_the_tables_still_match_anthropics_pages():
    problems = check_sources(ASSISTANT)
    assert problems == [], "\n".join(problems)
