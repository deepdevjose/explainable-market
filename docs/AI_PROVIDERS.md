# Educational assistant providers

## Implemented

The integration preserves the public functions in `ai.py`, JSON validation and
educational scope restrictions. Environment variables select one provider; a
failed request is not sent to a second provider.

| Provider | Selection | Private credential | Default model |
| --- | --- | --- | --- |
| Zhipu / BigModel | `AI_PROVIDER=bigmodel` | `BIGMODEL_API_KEY` | `BIGMODEL_MODEL=glm-5.3-flash` |
| DeepSeek | `AI_PROVIDER=deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL=deepseek-flash` |

DeepSeek remains the default for existing installations. The current demo selects
BigModel. Its credentials are outside the repository in
`~/.config/market-explained-demo/server.env`, with mode 0600. After changing
that configuration:

```bash
systemctl --user restart market-explained-demo-web
```

BigModel receives requests only at its official HTTPS endpoint, with the key in
Authorization. GLM-5.3-Flash requires reasoning to be enabled: current calls use
`thinking.type=enabled`, `reasoning_effort=low`, JSON output and a 4096-token budget.
The timeout is 45 seconds and responses are limited to 2 MB. Only final content is
processed; `reasoning_content` is neither returned to the browser nor stored in
conversation history. DeepSeek retains its previous parameters.

The interface identifies the provider and model and explains that the question
and context go to the selected provider. Accepted assistant responses use the
existing message storage; credentials never go to the client. Public errors do
not include provider error bodies or account details. Truncated or invalid JSON
responses produce a controlled error.

Without a key for the selected provider, the assistant offers existing local,
deterministic guidance. If a configured key is rejected, a local response does
not replace the failed call and risk being mistaken for model output. Headline
classification requires a valid provider. Prompt restrictions and schema
validation reduce risks but cannot guarantee generative answer accuracy.

Binance/Yahoo/Nasdaq/Twelve Data ingestion and numerical forecasting models are
independent of the assistant. An AI key cannot replace a Twelve Data key.
No image-upload interface has been added.

## Validated on 12 November 2026

- The official API accepted the credential and returned `glm-5.3-flash` and valid JSON.
- Public `/api/chat` returned HTTP 200 in Spanish, English and Simplified Chinese
  using a guest session with valid CSRF and Origin. Only the history generated
  by that test session was removed.
- The classifier returned three valid results for three existing real headlines.
  This check did not write classifications to the news database.
- All 70 automated tests passed without external requests. Seven new tests cover
  GLM/DeepSeek contracts, explicit selection, missing keys, safe errors, incomplete
  responses and scope/language validation.
- Ruff, mypy (22 selected files), medium/high-severity Bandit checks, Python
  compilation and JavaScript syntax checks passed.

Live checks verify connectivity and format, not financial accuracy or future
availability. The old DeepSeek credential was not rechecked. Keys shared in chat
should be rotated for a lasting installation; do not copy them into issues,
documentation or commits.

## Official references

- [BigModel API and authentication](https://docs.bigmodel.cn/cn/api/introduction)
- [GLM-5.3-Flash](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
- [GLM-5.3 parameters](https://docs.bigmodel.cn/cn/guide/models/text/glm-5.3)
- [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)
