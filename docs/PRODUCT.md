# What we are building

> This document describes the earlier MVP. The incremental Phase A/B evolution
> and its verified capabilities are described in [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md).

Explainable Market helps someone learning about or analyzing markets move from
“the price changed” to “what information can help me understand that change.”
It brings assets, daily series, verifiable headlines and educational questions
into one coherent experience.

## Reading the reference material

The original academic report defined an explainable watchlist, movements paired
with news and an asset timeline with reactions after one, three and seven sessions.
It described static data and providers that were pending at the time. It is kept
as a private reference outside the publishable tree because it contains old
credentials. This document records the original context; the [current README](../README.md)
describes present functionality and limits.

The supplied image explores a lightweight educational experience with simple
navigation, tracking and explanations. Its forecast percentages, scenarios and
predictor performance do not establish a validated model or an operational source.
They are not presented as real metrics or features.

The subsequent request extended this with a public landing page, full mobile
adaptation, a restrained Apple/Carbon visual language and a floating contextual assistant.

## Audience and proposition

The initial audience is students and people learning to interpret financial
information. Their main task is to choose an asset, inspect its data, open the
news and ask better questions. The app supports understanding and traceability;
it neither manages money nor executes transactions.

Users can examine whether a news item might relate to a movement, while keeping
visible that timing does not prove causation. Sentiment classification measures
the tone of a headline, not its actual economic effect.

## Main journey

1. The landing page explains the proposition and opens the market without mandatory registration.
2. The overview brings assets together and opens each asset's chart and news.
3. Details show real periods, price sources, dates, CSV and reaction windows.
4. Users can open each original article and request classification with DeepSeek.
5. A personal account saves the watchlist and separates conversation history.
6. The floating assistant accompanies every screen to explain the view or a concept.

## MVP decisions

| Decision | Reason |
| --- | --- |
| Retain Flask and SQLite | Build on the existing persistent, executable system without a framework migration that adds no immediate value. |
| A new database for verifiable data | Preserve the old file and avoid mixing generated prices with external sources. |
| Daily closes with source and date | Offer a verifiable integration without claiming a licensed real-time feed exists. |
| Public browsing; accounts for saved lists | Let people explore before registering and associate personal data with a real user. |
| Spanish interface and explanations in the original MVP | Follow the original request's language. Headlines retain the provider's text. |
| Carbon design with a clean composition | Local IBM Plex Sans, semantic tokens, blue interactions, grays, readable tables and explicit states. |
| Server-controlled AI context | Do not trust prices or instructions invented by a requesting client. |
| User-requested AI analysis | Avoid automatic paid analysis on every news refresh. |

## Implemented scope at that stage

Landing, overview, accounts, watchlists, asset search, period details, real sources,
news and filters, close-price export, complete reaction windows, DeepSeek chat and
sentiment integration, library and methodology, light/dark themes and responsive layouts.

Responsive controls and client logic were implemented but still required final
visual inspection in an available browser. DeepSeek required replacement of a
provider-rejected credential before real responses could be validated.

## Subsequent evolution

The next product steps required further decisions and work: a licensed financial
provider, account verification and recovery, operational observability and backups,
user testing, RPA for a specific source and a predictive model supported by data,
methods and evaluation. The original brief's “predictive analytics” label was not
used to imply nonexistent MVP predictions. See the current README for later work.
