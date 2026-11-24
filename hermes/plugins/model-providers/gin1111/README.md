# gin1111 Hermes model provider

OpenAI-compatible Chat Completions provider at `http://localhost:20128/v1`. The `builder` model is always listed first; authenticated `GET /models` adds any other available IDs. When the catalog is unavailable, `builder` remains selectable (inference still needs a working endpoint and credentials).

## Install into one profile

From this repo's root, replace `PROFILE` with the target Hermes profile name:

```bash
profile_home="$(dirname "$(hermes --profile PROFILE config path)")"
plugin="$PWD/hermes/plugins/model-providers/gin1111"
mkdir -p "$profile_home/plugins/model-providers"
ln -s "$plugin" "$profile_home/plugins/model-providers/gin1111"
```

Preview `profile_home` and the source path before running the two mutating commands. Do not replace an existing plugin directory or link without checking it first. Each profile has its own plugin directory; installing in one does not install in others.

Set `GIN1111_API_KEY` privately for that profile (for example, through `hermes --profile PROFILE auth add gin1111`, or in the profile's private `.env` file). Do **not** put the key in this repository. Optionally set `GIN1111_BASE_URL` in the same environment to override the default endpoint; include `/v1` in the URL. Then select `gin1111` and `builder` through `hermes --profile PROFILE model` or `/model`. Hermes uses its standard bearer-authenticated `/models` request for discovery.

If discovery fails with HTTP 401, verify the private API key and the provider's auth scheme. If the service is offline, the fallback entry remains visible but requests cannot succeed. The provider intentionally declares no unverified capabilities, pricing, or context window.

## Verify without profile changes

```bash
python3 -m unittest discover -s tests -p test_gin1111_provider.py -v
```

The repository's `./init.sh` performs its full baseline checks; use Python 3.11 or newer (`tomllib` is required by existing tests).
