# Changelog

## 0.3.0 (2026-11-11)

Its API on its page (plugin API 2.2, liminal-libs 1.49.0; the user: "each plugin should reflect the the API its attached to, and present links that provide documentation, the plugin interface should more or less contain what it already has, BUT, it should also expose more of what the API is about"). `ClaudePlugin.apis` (apis.py) is the Claude API's card, from Anthropic's pages, verified 2026-11-11: what it is, its base and version (`anthropic-version` 2026-10-21), how a key is sent (`x-api-key`, the documented fallback of `Authorization: Bearer`), the usage tiers' limits and spend caps, the prices, and Anthropic's pages (the API overview, the Messages and Models references, errors, authentication, rate limits, pricing, the status page, the release notes and API versions, the Console's API keys, rate limits and spend limits, the SDK, the CLI, the commercial terms). Every part of the reference is named: the Messages API and the Models list it uses (Connect and every evaluation), then token counting, batches, files, skills, user profiles, Managed Agents, the Admin and Compliance APIs, webhooks and tunnels; and its calls: `POST /v1/messages` and `GET /v1/models`, and the others worth knowing (each saying whether it changes something or costs money). The plans, models and sources tables stay as they were. The instance keeps nothing of a run, so `api_facts()` says nothing. Needs liminal-libs>=1.49.0. A test checks that the card names the requests Connect really sends; the weekly page check asks each address on it too.

## 0.2.1 (2026-11-08)

Its icon is Claude's spark, drawn in the library's line (liminal-libs 1.33.0's `claude`; the user: "for the AI icons, lets use the respective mascot/icon from the business, logo, etc.."). Needs liminal-libs>=1.33.0.

## 0.2.0 (2026-11-03)

Renamed `plugin-platform-claude` (the package `plugin_platform_claude`; it was `platform-plugin-claude`) on 2026-11-03: the naming by system (plugins are `plugin-<app>-<name>`), on liminal-libs 1.4.0 (`liminal_libs`, the library renamed with it).

The first release: `ClaudePlugin` (an `AssistantPlugin`, plugin API 2.0, liminal-libs 1.3.0) and
`ClaudeAssistant` on Anthropic's Messages API (API version 2026-10-21). The plans (Free: no API
access; the Evaluation, Start, Build, Scale and Custom tiers with their limits and spend caps), the
models (Haiku 5.5 by default, Sonnet 5.5, Opus 5.5, Fable 5.1 with their prices per million tokens)
and the pages they were written from, verified 2026-11-03; Connect reads the tier from the servers'
rate-limit headers and compares the models listed with the table; the weekly CI run reads the pages
again. Every error scrubbed of the key and the account; a spend cap's 429 is final, not retried.
