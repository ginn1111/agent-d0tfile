---
status: approved
scope: reusable Hermes model-provider plugin for gin1111
owner: Gin
---

# gin1111 model provider design

## Goal

Make `gin1111` a first-class choice in Hermes model pickers, backed by an OpenAI-compatible Chat Completions endpoint. The default endpoint is `http://localhost:20128/v1`; `coding` is the first/default model, and authenticated `GET /models` supplies additional choices.

## Approach

Add a minimal model-provider plugin under `hermes/plugins/model-providers/gin1111/`, with a `plugin.yaml` manifest and a module-level `register_provider(ProviderProfile(...))` in `__init__.py`. Use Hermes's standard API-key provider transport and model discovery; do not patch Hermes core or implement a second HTTP client. The profile declares `name="gin1111"`, `api_mode="chat_completions"`, `auth_type="api_key"`, `base_url="http://localhost:20128/v1"`, `env_vars=("GIN1111_API_KEY", "GIN1111_BASE_URL")`, and `fallback_models=("coding",)`. The base URL override is optional. The fallback is curated first, then discovered IDs are merged without duplicates.

## Configuration and data flow

Install the repo plugin in a chosen Hermes profile's `plugins/model-providers/` directory. The operator sets `GIN1111_API_KEY` privately in that profile's environment and may set `GIN1111_BASE_URL`; neither value is committed to the repo. Hermes loads the provider profile, lists it in `hermes model` and `/model`, resolves the key and endpoint, fetches `/models` with authentication, and sends inference through its existing Chat Completions client. Include a small README with installation and selection instructions. Do not modify profiles as part of producing the reusable artifact.

## Failure behavior

If `/models` is offline, unauthorized, or malformed, Hermes's fallback catalog still offers `coding`; this is not proof that inference will succeed. Missing or invalid credentials must surface as an authentication error, with no silent provider switch. Do not infer capabilities, pricing, or context window from the model ID. The endpoint returned HTTP 401 to an unauthenticated `/models` probe during design; live authenticated discovery requires operator credentials and is a separate verification step.

## Verification

Check manifest loading and provider registration in an isolated `HERMES_HOME`. Assert the provider name, API mode, endpoint, key/base-URL environment wiring, and `coding` fallback. Test model-list merging and catalog-failure fallback using a local fake server or equivalent fixture, without touching real profile credentials. Run the repository's canonical verification if available, plus targeted plugin tests; report any inaccessible live endpoint separately.

## Decision and scope

A named config entry alone would be smaller but would not provide the requested first-class plugin artifact. A Hermes-core modification would increase maintenance for no transport benefit. This design deliberately excludes custom HTTP transport, OAuth, invented model IDs, and automatic installation in every profile.

References: Hermes Agent developer guides, “Model Provider Plugins” and “Adding Providers.”
