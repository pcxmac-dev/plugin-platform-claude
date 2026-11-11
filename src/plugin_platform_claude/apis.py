"""What the plugin attaches to (plugin API 2.2, liminal_libs.sources.apis), as Anthropic's own pages describe it (read
2026-11-11): the Claude API, every part of its reference (the Messages API and the models list the plugin calls first,
then token counting, batches, files, skills, Managed Agents, the Admin and Compliance APIs), how a caller proves who
it is, its usage tiers' limits, its prices, the status page and the Console's key page. The tables the evaluations
are costed and planned by stay the plugin's (PLANS, MODELS, SOURCES). The user, 2026-11-11: "each plugin should
reflect the the API its attached to, and present links that provide documentation ... it should also expose more of
what the API is about"."""
from __future__ import annotations

from liminal_libs.sources.apis import Api, Area, Call, Link

from .assistant import API, API_VERSION, ClaudeAssistant

DOCS = "https://platform.claude.com/docs/en/"
REF = DOCS + "api/"
CONSOLE = "https://platform.claude.com/"
VERIFIED = "2026-11-11"  # the day these facts were read from Anthropic's pages

MESSAGES = "Messages"
MODELS = "Models"
BATCHES = "Message Batches"
AGENTS = "Managed Agents"
ADMIN = "Admin API"

CLAUDE_API = Api(
    name="Claude API",
    maker="Anthropic",
    about=("Anthropic's REST API for its Claude models. The Messages API takes a conversation and returns the model's "
           "next message (tools, thinking and effort, structured outputs, prompt caching and streaming are parts of "
           "it); beside it are token counting, message batches at half price, the models list, files and skills, "
           "Claude Managed Agents (agents, sessions, environments, vaults, memory stores, in beta) and the Admin API "
           "for an organization's members, workspaces, keys, limits and its usage and cost reports."),
    kind="rest",
    base=API,
    version=f"anthropic-version {API_VERSION}",
    auth=("an API key from the Console in the x-api-key header (the documented first form is Authorization: Bearer; "
          "x-api-key its still-supported fallback), with anthropic-version; the Admin API takes an Admin API key"),
    limits=("by usage tier, for each model class, requests and input and output tokens a minute: Start 4,000 "
            "requests, 2,000,000 input and 400,000 output tokens a minute on the 5.5 models (Fable 5.1 and 5.2: "
            "500,000 and 100,000), Build 10,000, 5,000,000 and 1,000,000, Scale 13,000, 10,000,000 and 2,000,000; a "
            "new organization starts in the Evaluation tier, below Start. Monthly spend caps: Start $500, Build $1,000, "
            "Scale $200,000 (a 429 enforced_spend_limit_reached until the 1st). Cache reads don't count toward input "
            "limits; batches have limits of their own. The anthropic-ratelimit-* headers say what is left."),
    costs=("every token, from prepaid credits: per million input and output tokens, Haiku 5.5 $0.10 and $0.50 (prompts "
           "over 100,000 tokens $0.50 and $2.50), Sonnet 5.5 $2 and $10, Opus 5.5 $4 and $20, Fable 5.2 $8 and $40, "
           "Fable 5.1 $10 and $50; cache reads 2.5 to 10 percent of the input price; batches half price; web search "
           "$10 a thousand searches; US-only inference 1.1 times"),
    links=(
        Link("API overview", REF + "overview", "docs"),
        Link("Create a Message", REF + "messages/create", "reference"),
        Link("List Models", REF + "models/list", "reference"),
        Link("Errors", REF + "errors", "reference"),
        Link("Working with Messages", DOCS + "build-with-claude/working-with-messages", "guide"),
        Link("Models overview", DOCS + "models/overview", "guide"),
        Link("Authentication", DOCS + "manage-claude/authentication", "auth"),
        Link("Rate limits", REF + "rate-limits", "limits"),
        Link("Pricing", DOCS + "about-claude/pricing", "pricing"),
        Link("Claude status", "https://status.claude.com/", "status"),
        Link("Release notes", DOCS + "release-notes/overview", "changelog"),
        Link("API versions", REF + "versioning", "changelog"),
        Link("Migrating to API version 2026-10-21", REF + "migration-2026-10-21", "changelog"),
        Link("Beta headers", REF + "beta-headers", "reference"),
        Link("API keys (Console)", CONSOLE + "settings/keys", "console"),
        Link("Rate limits (Console)", CONSOLE + "usage/limits", "console"),
        Link("Spend limits (Console)", CONSOLE + "settings/spend-limits", "console"),
        Link("Python SDK", "https://github.com/anthropics/anthropic-sdk-python", "sdk"),
        Link("Anthropic CLI", DOCS + "cli-sdks-libraries/cli/quickstart", "tool"),
        Link("Commercial terms of service", "https://www.anthropic.com/legal/commercial-terms", "terms"),
    ),
    areas=(
        Area(MESSAGES, "a conversation in, the model's next message out: tools, thinking and effort, structured "
                       "outputs, prompt caching, citations, streaming", REF + "messages",
             covered=("each evaluation's answer, and Connect's probe of a few tokens: the system prompt, one user "
                      "message, max_tokens, output_config.effort where set, metadata.user_id (a digest of the account); "
                      "the usage counted with the cache reads and writes; the limits read from its headers")),
        Area("Token counting", "a message's input tokens counted before it is sent, free",
             REF + "messages/count_tokens"),
        Area(BATCHES, "many Messages requests processed asynchronously at half price, within 24 hours",
             REF + "messages/batches"),
        Area(MODELS, "the models the key reaches, newest first: id, name, context window, output cap, capabilities",
             REF + "models", covered="Connect: the key tried, the model chosen looked for, the table's models compared"),
        Area("Files", "files uploaded once and used across requests", REF + "files"),
        Area("Skills", "custom agent skills, versioned", REF + "skills"),
        Area("User profiles", "user profiles for end-customer attribution, and their verification links",
             REF + "user_profiles"),
        Area(AGENTS, "agents, sessions in managed sandboxes, environments, vaults, memory stores, deployments and their "
                     "runs (beta)", DOCS + "managed-agents/overview"),
        Area(ADMIN, "an organization's members, invites, workspaces, API keys, rate and spend limits, service accounts, "
                    "federation, and its usage and cost reports (an Admin API key)", DOCS + "manage-claude/admin-api"),
        Area("Compliance API", "activities, organizations and their users, for compliance", REF + "compliance"),
        Area("Webhooks and tunnels", "webhook events and MCP tunnels (beta)", REF + "beta/webhooks"),
    ),
    calls=(
        Call("POST " + ClaudeAssistant.answers_path, "create a message", MESSAGES,
             used="each evaluation's answer, and Connect's probe", docs=REF + "messages/create", costs=True),
        Call("GET " + ClaudeAssistant.models_path, "list the models", MODELS,
             used="Connect: the models the key reaches", docs=REF + "models/list"),
        Call("GET /v1/models/{model_id}", "one model's details", MODELS, docs=REF + "models/retrieve"),
        Call("POST /v1/messages/count_tokens", "count a message's tokens", "Token counting",
             docs=REF + "messages/count_tokens"),
        Call("POST /v1/messages/batches", "create a message batch", BATCHES, docs=REF + "messages/batches",
             writes=True, costs=True),
        Call("GET /v1/messages/batches/{message_batch_id}/results", "a batch's results", BATCHES,
             docs=REF + "messages/batches"),
        Call("POST /v1/files", "upload a file", "Files", docs=REF + "files", writes=True),
        Call("POST /v1/skills", "create a skill", "Skills", docs=REF + "skills", writes=True),
        Call("POST /v1/agents", "create an agent (beta)", AGENTS, docs=REF + "beta/agents", writes=True),
        Call("POST /v1/sessions", "start a session in a managed sandbox (beta)", AGENTS, docs=REF + "beta/sessions",
             writes=True, costs=True),
        Call("GET /v1/organizations/usage_report/messages", "the organization's token usage (Admin API)", ADMIN,
             docs=DOCS + "manage-claude/usage-cost-api"),
        Call("GET /v1/organizations/cost_report", "the organization's costs (Admin API)", ADMIN,
             docs=DOCS + "manage-claude/usage-cost-api"),
        Call("GET /v1/organizations/me", "the key's organization", ADMIN, docs=REF + "organization"),
    ),
    verified=VERIFIED,
)

APIS = (CLAUDE_API,)
