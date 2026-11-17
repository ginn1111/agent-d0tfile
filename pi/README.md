# Pi local gateway models

`models.json` defines a `local` provider for the OpenAI-compatible gateway at
`http://localhost:20128/v1`. Its 88 model IDs and limits come from the saved
`models-catalog.json` response.

Replace the `redact` API key placeholder before using the provider. Pi reads
`~/.pi/agent/models.json`; copy this file there after setting the key. Then
select a model such as `local/coding` or `local/cx/gpt-6.1-sol` in Pi.
