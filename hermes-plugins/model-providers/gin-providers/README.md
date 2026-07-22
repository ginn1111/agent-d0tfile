# gin-providers

Hermes model-provider plugin for Gin Interface.

## What it adds

Registers provider profile:

- provider name: `gin-interface`
- alias: `gin`
- display name: `Gin Interface`
- auth: API key
- default base URL: `https://agents.gin1111.dev/v1`
- signup URL: `https://agents.gin1111.dev`
- default aux model: `aux`
- fallback models: `aux`

Source: `__init__.py`

## Required env vars

- `GIN_API_KEY`
- `GIN_BASE_URL`

`GIN_BASE_URL` exists in provider env list. Plugin also ships default `base_url` in code, so env override only needed when pointing at different endpoint.

## Files

- `plugin.yaml` — Hermes plugin metadata
- `__init__.py` — provider registration

## Install into Hermes profile

From repo root:

```bash
make link-model-providers HERMES_PROFILE_NAME=gintary
```

Preview only:

```bash
make link-model-providers-list HERMES_PROFILE_NAME=gintary
```

Direct script:

```bash
./scripts/link-model-providers.sh link gintary
```

This creates symlink:

```text
~/.hermes/profiles/gintary/plugins/gin-providers
```

## Use in Hermes

After plugin linked into profile, start Hermes with that profile and select provider with Hermes config or model picker.

Examples:

```bash
hermes --profile gintary model
hermes --profile gintary config edit
```

Expected provider identifiers from plugin:

- `gin-interface`
- `gin`

## Notes

- Plugin kind: `model-provider`
- Version: `1.0.0`
- Description: `Gin Interface — OpenAI-compatible direct API`
- Author: `gin`
