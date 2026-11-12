# Demo Day presentations

Two English presentations explain the same product for different audiences.
The commercial pitch focuses on the user experience. The technical pitch explains
source adapters, normalization, validation, news AI and operational boundaries
in accessible language.

| Presentation | PowerPoint | Speech | Approximate duration |
| --- | --- | --- | --- |
| Commercial | [Commercial deck](Explainable_Market_Commercial_EN.pptx) | [Commercial speech](Explainable_Market_Speech_EN.md) | 5–6 minutes |
| Technical | [Technical deck](Explainable_Market_Technical_EN.pptx) | [Technical speech](Explainable_Market_Technical_Speech_EN.md) | 7–8 minutes |

The commercial deck has 11 main slides and two hidden Q&A slides. The technical
deck has 12 main slides and two hidden Q&A slides. Both include speaker notes.
The PowerPoint files contain editable slide content and actual application
screenshots; they do not require an online presentation account.

## Scope of the claims

- Implemented inputs include JSON over APIs/WebSockets and financial news in RSS/XML.
- CSV price export and JSON read APIs are implemented. Generic CSV/Excel ingestion
  and dedicated BI connectors are planned extensions, not working integrations.
- “Middleware” describes the adaptation/validation role across existing modules,
  rather than a separately deployed middleware server.
- News and market events have separate contracts. The sentiment workflow sends
  headline IDs and text to the configured external AI provider and validates the
  response. Structured input is not evidence of improved model accuracy.
- Forecasting is separate from generative AI and includes visible uncertainty.
- Student recruitment and proposed revenue models are targets, not achieved results.

Product evidence and screenshots were reviewed on 12 November 2026. Source links
in the speeches and notes identify the reviewed code revision. A temporary demo
URL is not a permanent deployment; verify it on the presentation device before use.
Do not publish private service configuration, account data or credential-bearing
screenshots alongside these materials.

These are the maintained public presentation files. Local `output/` and
`artifacts/` directories are ignored build/review material and are not uploaded.
See the [project README](../../README.md), [model evidence](../PREDICTIVE_INTELLIGENCE.md)
and [laptop demo guide](../LAPTOP_DEMO.md) for implementation and hosting limits.
