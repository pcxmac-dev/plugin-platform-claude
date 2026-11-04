# platform-plugin-claude

Claude for [Liminal](https://github.com/pcxmac-dev/liminal-app): an AI assistant plugin (plugin API
2.0, `liminal_lib.assistants`) that evaluates standardized arguments (a question over headlines, an
assessment, a report; a judge over earlier answers) through Anthropic's Messages API on your own
API key, with Anthropic's plans, models and prices written in.

- `claude` on the Plugins view (the AI assistants group): Setup takes `CLAUDE_API_KEY` (read as
  `ANTHROPIC_API_KEY` too) and `CLAUDE_ACCOUNT`, the email or account name the key belongs to, shown
  with its evaluations and sent to Anthropic only as a digest (`metadata.user_id`).
- Plan: `CLAUDE_PLAN` is `free` by default, which has no API access (a Claude.ai subscription is not
  an API key; the API needs a Console organization with credits bought), so nothing is sent until
  the plan your key is on is chosen: `evaluation` (a new organization), `start`, `build`, `scale` or
  `custom`. Connect reads the limits Anthropic's servers send and names the tier they show, applied
  where you set none.
- Model: `CLAUDE_MODEL`, Claude Haiku 5.5 by default (the cheapest); Sonnet 5.5, Opus 5.5 and Fable
  5.1 are in the table with their prices. `CLAUDE_EFFORT` sets the API's effort level.
- Caps on this machine, every database together: `CLAUDE_REQUESTS_PER_DAY` (50),
  `CLAUDE_TOKENS_PER_DAY` (200,000), `CLAUDE_MAX_OUTPUT_TOKENS` (1,024); raised on the Plugins view.
- The tables were verified on the date the plugin says (`VERIFIED`) against Anthropic's pricing and
  rate-limit pages; the weekly CI run reads those pages again and fails when a figure is gone, which
  is a new release of this plugin.

Nothing is sent from an offline copy of the app (`LIMINAL_OFFLINE`).

## Install

Into the app's environment, from the app's folder:

```powershell
.venv\Scripts\python.exe -m pip install "platform-plugin-claude @ git+https://github.com/pcxmac-dev/platform-plugin-claude@release/0.2.0"
```

or with the app's plugins (`pip install -e ".[plugins]"` in liminal-app). The app loads it on its next
start. Save the key with the app's `tools/set-key.ps1` or on the Plugins view (it is read from your
user environment variables only, never written to a file).

## Tests

`python -m pytest -q`: fake answers, nothing sent. `LIMINAL_VENDOR_PAGES=1` adds the page check.
