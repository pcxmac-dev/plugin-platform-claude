"""Claude (Anthropic) for Liminal: an AI assistant plugin (liminal_lib.assistants, plugin API 2.0) that
evaluates standardized arguments through Anthropic's Messages API on your own API key, with the
plans, models and prices written in, dated, and checked against Anthropic's pages.

A Liminal plugin released on its own, registered under the entry point group `liminal.providers` as
`claude` (the registry's name too): the plugin `ClaudePlugin` (ASSISTANT below), its
assistant `ClaudeAssistant` (assistant.py). It relies on plugin API 2.0 and nothing of the apps.

What the user sets (the Plugins view's Setup, or the app's key script): `CLAUDE_API_KEY` (read as
`ANTHROPIC_API_KEY` too), `CLAUDE_ACCOUNT` (the email or account name the key belongs to: shown with
its evaluations, sent to Anthropic only as a digest, in `metadata.user_id`); its plan `CLAUDE_PLAN`
(free: no API access; evaluation, start, build, scale, custom: the Console's usage tiers), its model
`CLAUDE_MODEL` (Haiku 5.5 by default: the cheapest), its caps on this machine `CLAUDE_REQUESTS_PER_DAY`
(50), `CLAUDE_TOKENS_PER_DAY` (200,000), `CLAUDE_MAX_OUTPUT_TOKENS` (1,024), and `CLAUDE_EFFORT` (the
API's effort levels; the vendor's default when unset).

The user, 2026-11-03: "the ai plugins should support free, and if that means they have no API access,
then so be it": a Claude.ai subscription is not an API key, so the free plan sends nothing; the API
needs a Console organization with credits bought. "every time any of the three vendors changes their
plans/rates there will have to be a way to query through the plugin to update itself, or worst
case, just version up every time w/ CI catching the disparity between code and latest rates through
unit testing": Connect (the capability scan) reads the limits Anthropic's servers send and names the
tier they show, and compares the models listed with the table; the weekly CI run reads the pricing
and rate-limit pages (SOURCES) and fails when a written-in figure is gone, which is a new release
of this plugin.
"""
from __future__ import annotations

from liminal_lib.assistants import AssistantPlugin, Caps, Model, Plan, Source

from .assistant import API, API_VERSION, ClaudeAssistant

__all__ = ["ASSISTANT", "ClaudePlugin", "ClaudeAssistant", "PLANS", "MODELS", "SOURCES", "VERIFIED", "API", "API_VERSION"]

VERIFIED = "2026-11-03"  # the day the tables below were checked against SOURCES

# Anthropic's usage tiers (platform.claude.com/docs/en/api/rate-limits, 2026-11-03): each a monthly spend
# cap and, per model class, requests and input and output tokens a minute. The figures here are the
# 5.5 models' (Haiku, Sonnet, Opus 5.5 share them; Fable 5.x has a quarter of the tokens).
PLANS = (
    Plan("free", "No API plan", api_access=False, price="a Claude.ai subscription, or nothing",
         note="a Claude.ai subscription (Free, Pro, Max) is not an API key: the API needs a Console organization "
              "(platform.claude.com) with credits bought; a new organization starts in the Evaluation tier"),
    Plan("evaluation", "Evaluation tier", price="credits bought; a new organization",
         note="limits below the Start tier's, not published, raised automatically as usage history builds"),
    Plan("start", "Start tier", rpm=4_000, tpm=2_000_000, price="credits bought", spend_cap="$500 a month",
         note="4,000 requests, 2,000,000 input and 400,000 output tokens a minute on the 5.5 models (Fable 5.x: 500,000 and 100,000)"),
    Plan("build", "Build tier", rpm=10_000, tpm=5_000_000, price="credits bought", spend_cap="$1,000 a month",
         note="10,000 requests, 5,000,000 input and 1,000,000 output tokens a minute on the 5.5 models (Fable 5.x: 1,500,000 and 300,000)"),
    Plan("scale", "Scale tier", rpm=13_000, tpm=10_000_000, price="credits bought", spend_cap="$200,000 a month",
         note="13,000 requests, 10,000,000 input and 2,000,000 output tokens a minute on the 5.5 models (Fable 5.x: 4,000,000 and 800,000)"),
    Plan("custom", "Custom tier", price="arranged with Anthropic", note="no monthly spend cap; limits arranged with the account team"),
)

# The current models (platform.claude.com/docs/en/about-claude/pricing and models/overview, 2026-11-03):
# prices per million tokens (input, output, a cache read), the context window; the cheapest first.
MODELS = (
    Model("claude-haiku-5-5", "Claude Haiku 5.5", 0.10, 0.50, 0.01, 1_000_000, reasoning=True,
          note="the fastest; prompts over 100,000 tokens cost $0.50 in and $2.50 out; effort medium by default"),
    Model("claude-sonnet-5-5", "Claude Sonnet 5.5", 2.00, 10.00, 0.10, 1_000_000, reasoning=True,
          note="speed and intelligence together; effort high by default"),
    Model("claude-opus-5-5", "Claude Opus 5.5", 4.00, 20.00, 0.20, 1_000_000, reasoning=True,
          note="long-running agentic and knowledge work; effort medium by default"),
    Model("claude-fable-5-1", "Claude Fable 5.1", 10.00, 50.00, 0.25, 1_000_000, reasoning=True,
          note="the most capable; thinking always on; needs 30-day data retention on the organization"),
)

# Where the tables come from, with what each page must still show (verify.check_sources, weekly in CI).
SOURCES = (
    Source("https://platform.claude.com/docs/en/about-claude/pricing.md", "the models' prices",
           "The following table shows pricing for all Claude models",
           ("Claude Haiku 5.5", "$0.10 / MTok", "$0.50 / MTok", "Claude Sonnet 5.5", "$2 / MTok", "$10 / MTok",
            "Claude Opus 5.5", "$4 / MTok", "$20 / MTok", "Claude Fable 5.1", "$50 / MTok")),
    Source("https://platform.claude.com/docs/en/api/rate-limits.md", "the usage tiers' limits and spend caps",
           "There are two types of limits:",
           ("Start", "$500 USD", "Build", "$1,000 USD", "Scale", "$200,000 USD", "Claude Haiku 5.5", "4,000", "10,000", "13,000",
            "2,000,000", "5,000,000", "10,000,000")),
    Source("https://platform.claude.com/docs/en/about-claude/models/overview.md", "the current models", "Compare models",
           ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-1")),
)


class ClaudePlugin(AssistantPlugin):
    """Claude: the plugin (see the module's docstring)."""

    name = "claude"
    title = "Claude"
    about = "Anthropic's Claude through the Messages API: evaluations of standardized arguments on your key"
    vendor = "Anthropic"
    signup = "https://platform.claude.com/"
    order = 500
    api = "2.0"
    assistant = ClaudeAssistant
    plans = PLANS
    models = MODELS
    default_model = "claude-haiku-5-5"
    verified = VERIFIED
    sources = SOURCES
    caps = Caps()  # 50 requests and 200,000 tokens a day on this machine, 1,024 output tokens an answer
    efforts = ("", "low", "medium", "high", "xhigh", "max")  # output_config.effort; "" leaves the model's default
    key_aliases = ("ANTHROPIC_API_KEY",)
    account_hint = "the email or account name the key belongs to: shown with its evaluations, sent to Anthropic only as a digest (metadata.user_id)"


ASSISTANT = ClaudePlugin()
