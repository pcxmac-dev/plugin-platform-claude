# Changelog

## 0.2.0 (2026-11-03)

Renamed `plugin-platform-claude` (the package `plugin_platform_claude`; it was `platform-plugin-claude`) on 2026-11-03: the naming by system (plugins are `plugin-<app>-<name>`), on liminal-libs 1.4.0 (`liminal_libs`, the library renamed with it).

The first release: `ClaudePlugin` (an `AssistantPlugin`, plugin API 2.0, liminal-libs 1.3.0) and
`ClaudeAssistant` on Anthropic's Messages API (API version 2026-10-21). The plans (Free: no API
access; the Evaluation, Start, Build, Scale and Custom tiers with their limits and spend caps), the
models (Haiku 5.5 by default, Sonnet 5.5, Opus 5.5, Fable 5.1 with their prices per million tokens)
and the pages they were written from, verified 2026-11-03; Connect reads the tier from the servers'
rate-limit headers and compares the models listed with the table; the weekly CI run reads the pages
again. Every error scrubbed of the key and the account; a spend cap's 429 is final, not retried.
