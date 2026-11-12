# Explainable Market: technical speech

**Language:** English
**Main pitch:** 12 slides, approximately seven to eight minutes including transitions
**Spoken word count:** 945
**Backup:** Slides 13 and 14 are hidden Q&A slides.

## Main speech

### Slide 1: The data layer behind Explainable Market

A financial application has to understand its sources before it can help people understand a market. Prices may arrive as JSON messages, while news arrives as RSS or XML. Explainable Market uses source-specific adapters and validation to turn those inputs into predictable records. Today I will explain that translation layer, how it supports our news AI, and where Excel and BI could connect next.

### Slide 2: Delivery, format and destination

Three ideas make the architecture easy to follow. Delivery is how information reaches us, such as an API request or a WebSocket connection. Format is how that information is written, such as JSON or XML. Destination is where we use it, such as the web interface or an AI service. CSV and Excel are file formats. BI means business intelligence tools, which would consume prepared data. Keeping these ideas separate helps us design the right connector.

### Slide 3: What is connected today

Our current application receives JSON price data from APIs and Binance streams. It receives financial headlines through Yahoo Finance RSS, which uses XML. It also exports historical stock prices as CSV and provides JSON read APIs. We do not currently have a generic CSV news importer, an Excel upload pipeline, or a dedicated BI connector. Those are extension opportunities. Optional provider access also depends on credentials, quotas, and display rights.

### Slide 4: Middleware, in plain English

Think of the middleware as a translator with a checklist. First, an adapter reads the provider's format. Next, it maps names and values into the fields the application expects. Validation checks the information before storage. The application then serves consistent records to the interface and AI workflows. This role lives across our existing adapters, collectors, and repositories. It is an architectural layer, rather than a separate middleware server we have already deployed.

### Slide 5: One headline, one consistent record

Here is an illustration using the actual news parser. It reads a title, source, link, and publication date from an RSS item. The date in this example starts at nine in the morning in UTC plus eight. The parser converts it to one in the morning UTC. It attaches the instrument and preserves the source URL. The fields then have a consistent shape, whatever naming the next supported adapter uses. This example is fictional and demonstrates formatting, not a real news event.

### Slide 6: News and prices keep separate contracts

Consistency does not mean forcing every kind of data into the same record. A news item needs a headline and a source link. A market event needs an instrument, provider, observation time, and financial values. We use separate structures for those jobs. Both keep identity and provenance. New market events use decimal values and explicit quality flags. Legacy stock history still has a compatibility path, so we do not claim that every historical price already uses the new contract.

### Slide 7: How the news AI receives data

News sentiment is a specific workflow. After a user requests analysis, the application selects up to eight unclassified headlines. It sends their IDs and headline text as JSON to the configured external AI provider. The reply must use known IDs, an allowed sentiment value, and a short rationale. We filter invalid entries before storing accepted results. The model classifies the tone of a headline. It does not read every full article or establish what caused a market movement.

### Slide 8: The assistant uses richer context

The educational assistant has a different job from sentiment classification. The server prepares context about the screen, selected asset, and up to five news records. Those records retain links, sources, dates, and IDs that the assistant can cite. It also includes a bounded conversation history and the selected response language. We validate the answer structure before showing it. Structured fields make this handoff more predictable. We have not independently measured an improvement in answer accuracy caused by normalization.

### Slide 9: Freshness travels with the price

The delivery method alone does not tell us whether a price is current. Our market events keep the observation time and the time we received it. A live label requires recent events and a connected collector. Stock closes remain historical, and older streaming observations become stale. We keep unavailable markets explicit instead of filling them with invented prices. This is also how we would judge a future spreadsheet import: we would need to inspect its source and date before deciding how to present it.

### Slide 10: Workers keep continuous ingestion outside Flask

Continuous Binance collection runs in an independent worker. Provider tasks feed a bounded queue, and the writer persists accepted events in SQLite. Retry and reconnection policies handle upstream interruptions. The web application reads stored state and refreshes the browser every five seconds. News and daily stocks retain their existing collector path, and forecasting has its own worker. This preserves the Flask application while allowing data processing to evolve incrementally. Redis and a separate cloud deployment are not required by this initial design.

### Slide 11: The path to Excel and BI

There are two useful directions for expansion. For input, a CSV or Excel adapter would map columns into our news or market record, then check required fields, dates, duplicates, and source rights. That importer has not been built yet. For output, the application already supplies stock CSV exports and JSON APIs that another tool could consume. A dedicated BI dashboard or connector is still future work. We choose a source by its relevance, freshness, and permission to use it, rather than connecting it simply because we can parse its format.

### Slide 12: A consistent path from sources to understanding

The technical value is a consistent path from external sources to information people can inspect. We already connect JSON market data and RSS or XML headlines. We preserve provenance, structure AI context, and check responses before using them. The same design gives future CSV, Excel, and BI integrations a clear place to connect. Our next step is to validate the most useful additional source with real users, implement its adapter, and measure the result. More connections should make the learning experience more useful while keeping its meaning and limitations clear.

## Backup answers

### Slide 13: Forecasting is a separate workflow

The news AI is an external language-model integration. Price forecasting is a separate local workflow using persistence, ridge regression, and optional XGBoost. It trains from at least 120 closed daily observations, selects by calibration error, and uses chronological walk-forward evaluation. The displayed uncertainty interval is empirical with nominal 80% coverage. Neither model family has independent accuracy certification in this project.

### Slide 14: Engineering evidence and remaining work

The current checkout passes 79 automated tests. For this explanation, we also checked an offline RSS example: a timestamp changed from UTC plus eight to UTC, a malformed date was skipped, and invalid AI IDs or sentiment values were filtered. These checks verify processing behavior, not live provider uptime or AI prediction quality. Broader news adapters, generic file import, BI integration, independent hosting, and independent model evaluation remain future work.

## One-minute technical summary

Explainable Market connects external sources through adapters and validation. Current price inputs use JSON APIs or WebSocket messages, while financial headlines arrive through RSS/XML. The news parser maps them to consistent headline, source, URL, instrument, and UTC publication fields. The sentiment service receives selected IDs and headlines as JSON. We check returned IDs, allowed labels, and rationale types before saving accepted results. The educational assistant receives richer source-linked context. This creates a more predictable integration, although we have not independently measured an accuracy improvement from normalization. CSV exports and JSON read APIs already work. Generic CSV or Excel imports and dedicated BI connections remain future adapters. The source timestamp and usage rights matter as much as the file format.

## Plain-English glossary

| Term | Meaning in this product |
| --- | --- |
| Middleware | The translation and validation role between external sources and application workflows. Distributed across current modules, not a new standalone server. |
| Adapter | A reader that understands one provider's delivery method and format. |
| API | A defined way for software to request or exchange data. |
| WebSocket | A connection that can receive successive messages without a new HTTP request for every event. |
| JSON | Named fields and values that software can read consistently. |
| RSS/XML | The structured feed format used by the current news source. |
| CSV | A table saved as text. The app exports stock prices in this format. |
| Excel | A spreadsheet file format. Generic XLSX ingestion is not implemented. Excel can consume the existing CSV export manually. |
| BI | Business intelligence tools that could consume prepared data. No dedicated connector has been implemented. |
| Normalization | Mapping source-specific fields, values and timestamps into a consistent internal structure. |
| Contract | The agreed fields and rules a record must follow. News and market events have different contracts. |
| Provenance | Where an observation or headline came from, preserved with its time and source. |
| Validation | Checks on input or model output. These checks do not prove the truth of an article or the accuracy of an AI answer. |
| Sentiment | Positive, negative or neutral headline tone. It is not a trade signal. |

## Claims to keep precise

- Current news ingestion is RSS/XML from Yahoo Finance. It is not a generic reader for every publisher, full article, PDF, image, Excel workbook or BI system.
- The sentiment classifier receives selected IDs and headline text. The assistant receives richer context with source URLs, publication times, selected asset and language.
- Consistent input helps maintain a predictable software interface. Improved AI comprehension or accuracy remains an unmeasured hypothesis.
- BigModel and DeepSeek are external AI providers. We did not train a proprietary news language model.
- Existing CSV export and JSON read APIs are output capabilities. They do not imply an existing CSV/XLSX ingestion pipeline or a BI dashboard.
- Incompatible, outdated or unlicensed data needs review. A valid file format alone cannot establish freshness or redistribution permission.
- New market events use Decimal values. The legacy daily stock compatibility path still uses float/SQLite REAL values.
- Headline normalization and canonical market events follow distinct domain contracts. The code does not put every kind of information into one universal record.
- The news analysis action requires sign-in and CSRF protection. Public research pages remain accessible without sign-in.
- The format example is fictional. The automated checks are offline and do not constitute a live model accuracy evaluation.

## Evidence reviewed

The current checkout ran 79 automated tests successfully. An additional offline parser demonstration verified RSS field mapping, conversion from +0800 to UTC, skipping an invalid date and filtering unknown IDs and invalid sentiment labels from a mocked AI response. No live AI request or user-data modification was needed for this review.

## Source references

- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/README.md
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/collector.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/providers/base.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/providers/binance.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/api/routes.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/providers/twelve_data.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/application.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/markets/events.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/storage/repository.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/db.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/ai.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/tests/test_app.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/assistant/educational.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/tests/test_ai_providers.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/ingestion/workers.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/intelligence/worker.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/intelligence/forecasting.py
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/docs/PREDICTIVE_INTELLIGENCE.md
- https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/tests/test_market_data.py

## Presenter preparation

Use the commercial deck to sell the user's experience. Use this deck to explain why the architecture can accept additional sources while keeping clear contracts. The official ENT207TC Handbook and Assessment Brief still need to be checked before claiming complete module compliance. Hosting remains the supervised laptop demo described in the existing product documentation.
