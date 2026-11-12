# Explainable Market: Demo Day speech

**Language:** English
**Main pitch:** 11 slides, approximately five to six minutes including transitions
**Spoken word count:** 689
**Delivery:** Aim for 125–140 words per minute. Pause after the opening question and let the audience inspect the prediction chart.

Slides 12 and 13 are hidden Q&A backup slides. They remain editable and accessible in the slide sorter. The same main script appears in PowerPoint speaker notes.

## Main speech

### Slide 1: Explainable Market

Imagine opening a market app and seeing a sharp price movement. The number is clear. The context takes more work. Where did the data come from? What do the headlines actually say? How much confidence should you place in a forecast? We built Explainable Market to help people answer those questions.

### Slide 2: The confidence gap

Our starting user is a student or first-time market learner. They move between price charts, news articles, and unfamiliar terminology. Every extra tab makes the research harder to follow. Explainable Market keeps that journey together. Students can explore a real movement, check the evidence, and learn the concepts they need along the way. We want their first market experience to feel approachable.

### Slide 3: A complete research journey

Explainable Market brings prices, historical charts, source-linked news, and educational guidance into one workspace. A user can explore an asset, inspect its history, and follow the information behind it. The core research pages open without registration. When someone wants a personal watchlist, they can create an account and save it. We already have a working application that people can try.

### Slide 4: Different sources, one research experience

Behind that experience is a translation layer, our middleware. It receives information in the formats providers use and creates consistent records for each data type. Today, that includes JSON market feeds and RSS or XML news. We preserve the source and date, check the fields, and prepare structured context for AI. CSV export already works. CSV or Excel imports and BI connections would use additional adapters. Those integrations are our extension path.

### Slide 5: Live crypto, with a visible source

Here is one working example: Bitcoin and Ether prices arrive from Binance Spot. The browser refreshes the stored market state every five seconds, and the interface shows the provider and timestamp. If the feed becomes stale, the label changes. US stocks use daily historical closes. We make that distinction visible, so users can understand what kind of information they are seeing.

### Slide 6: Forecasts that show their limits

The prediction view makes uncertainty part of the experience. Green and red show observed price movements. The yellow section shows the next-close estimate, with an uncertainty band. Behind it, we compare persistence, ridge regression, and optional XGBoost using chronological evaluation. A simple baseline can win. The historical evaluation and model limits remain visible. Users can examine the estimate, question it, and understand the difference between an observation and a possible outcome.

### Slide 7: News prepared for analysis

News makes the benefit tangible. Our adapter takes RSS or XML headlines and prepares consistent records with a source, link, and publication time. The sentiment service receives selected headlines as structured JSON, and we validate its response before saving it. The assistant can use richer context to explain financial concepts. This creates a predictable path from incoming information to educational insight, while keeping the original source visible.

### Slide 8: Three languages, one learning experience

The interface supports English, Spanish, and Simplified Chinese. That lets different students explore the same product in a language they are comfortable using. External news retains its original language. Alongside the educational library, the assistant, and clear source labels, this gives us an accessible starting point for international campus communities.

### Slide 9: Students first. Campus pilots next.

Our initial audience is students and first-time learners. Our proposed business model keeps core exploration free, then tests demand for advanced learning tools and university pilots. We will validate willingness to pay before setting prices. Data licensing and AI operating costs will shape any commercial offer. The open-source core also gives us a practical way to invite contributors and show how the product works.

### Slide 10: Ten real users before Demo Day

Our next milestone is feedback from at least ten real users before Demo Day. Each tester will find an asset, check the source and freshness, explain the forecast in their own words, and tell us what needs to change. We will record task completion and connect each useful piece of feedback to a product improvement. The goal is a stronger product shaped by the people who will actually use it.

### Slide 11: Financial understanding should be for everyone

Explainable Market gives people a place to begin understanding financial information. We have built the research experience, connected real data, and made uncertainty visible. Now we are looking for student testers and campus partners to help shape the next step. Try one asset and tell us what becomes clearer. Our ambition is simple: financial understanding should be for everyone. Thank you.

## Short version, approximately 90 seconds

A price chart can show you what moved. Explainable Market helps you explore the context. We bring real-source market data, historical charts, news, and educational guidance into one workspace for students and first-time learners. A middleware layer maps JSON feeds and RSS/XML headlines into consistent records for the app and AI, while preserving source and time. Bitcoin and Ether prices arrive from Binance Spot, with visible timestamps and freshness labels. US stock prices use daily historical closes. Our prediction view separates observed prices from the yellow next-close estimate and keeps uncertainty visible. The interface supports English, Spanish, and Simplified Chinese, and core research pages open without registration. We have a working product people can try. Our next milestone is feedback from at least ten real users, then a clear record of what we improved because of that feedback. We are looking for student testers and campus partners to help make market information easier to understand.

## Judge questions: concise answers

**What does the middleware do?**
It describes the source adaptation and validation work across existing modules. Current inputs include JSON APIs/streams and RSS/XML news. It maps inputs to consistent records per data type, preserves source/time and prepares structured AI context. It is not a separate deployed middleware server.

**Do you already import Excel or CSV news and connect BI?**
No generic importer or dedicated BI connector is implemented. CSV price export and JSON read APIs work today. Additional inputs need adapters, validation, freshness checks and appropriate data rights.

**Does structured news guarantee more accurate AI answers?**
No independent accuracy improvement has been measured. It makes the input fields and validation more predictable. Sentiment classification receives IDs and headline text, while the assistant receives richer context with source links and dates. Full-article, PDF and image ingestion are not implemented.

**Did you train your own news language model?**
We integrate a selected external BigModel or DeepSeek service. Our contribution is source handling, contextual preparation, application logic and result validation. Local return forecasting uses a separate workflow.

**Who is the first user?**
Students and first-time market learners. This is our initial customer hypothesis. We still need real user evidence to confirm the strongest segment.

**What is the difference you want users to feel?**
A connected research journey: inspect a price, check its source and freshness, read related news, then explore an educational explanation. We focus on comprehension and visible limitations. We have not run an independent competitor benchmark.

**Does it use real data?**
Yes. Binance Spot supplies BTCUSDT and ETHUSDT events. Yahoo/Nasdaq supply US stock daily historical data. Each observation retains provenance. Prices on screenshots are examples captured on 12 November 2026, not current quotes for the presentation date.

**Is everything live?**
No. Binance ingestion streams continuously while the browser refreshes stored state every five seconds. Stocks use historical daily closes. The interface labels stale or unavailable data. Forex and gold depend on optional provider access and display permission. Indices remain unavailable with the tested access.

**How accurate are the predictions?**
We do not claim independently verified accuracy. The product compares persistence, ridge and optional XGBoost chronologically and shows historical evaluation and uncertainty. A persistence baseline can win. The nominal 80% interval does not guarantee future coverage.

**Does this give financial advice or place trades?**
The product provides educational information. It does not execute trades, connect brokerage accounts to place orders, promise returns or treat model contributions as causal evidence.

**What happens if AI is unavailable?**
AI assistance is optional. Core data ingestion and forecasting do not require the educational AI provider. Local educational guidance remains available without a selected AI credential. A failure from a configured AI provider can still produce an explicit error.

**How will you make money?**
Our proposed model keeps core exploration free and tests demand for advanced learning tools and campus pilots. Pricing, paid features and partnerships remain unvalidated. Data redistribution rights and AI costs affect viability.

**Do you already have ten users or feedback?**
We have not supplied a verified set of ten real users or feedback records. Ten testers is the next recruitment target. We will log dated observations, task completion and the changes those observations lead to. Never present invented quotes or engagement figures.

**Can visitors try it without signing in?**
Yes, core overview, market, prediction, news and learning pages are public. A personal watchlist requires an account. No authentication controls were removed or bypass links created for this presentation.

**Is this independently hosted and ready for a full public launch?**
The current demo uses a supervised laptop and a temporary Cloudflare tunnel. It depends on the laptop remaining awake and connected. Permanent independent hosting, broader operational acceptance and independent model evaluation remain pending.

**What about security?**
The application retains password hashing, CSRF controls and private server-side configuration. Historical sensitive material required repository cleanup. Branch history was sanitized, but credential revocation and removal of a cached historical GitHub file remain pending. Do not claim a completed security audit or a fully resolved incident.

## Poster copy suggestions, for your manual design

**Name:** Explainable Market

**Main headline:** Market intelligence you can understand

**Short description:** Explore real-source prices, financial news and educational forecasts in one workspace.

**Highlights:**

- Live Bitcoin and Ether data, with visible source and timestamp
- US stock history and source-linked financial news
- A data translation layer prepares consistent records for the app and AI
- Yellow forecast estimates with visible uncertainty
- English, Spanish and Simplified Chinese interface
- Educational assistant and learning library
- Core exploration without registration

**Invitation:** Try one asset. Tell us what becomes clearer.

**Small-print scope:** Educational information. No investment advice or trade execution. Stock data is historical. Forecasts can fail.

Use one actual product screenshot and your own QR for the tested public demo. Avoid calling every market live, claiming guaranteed accuracy, calling the product the world's best, or displaying invented testimonials, user counts or social reach.

## Presenter preparation, not part of the spoken pitch

- Recheck the public URL on another device before printing a QR or presenting. A temporary tunnel link can change after restart. Current link: https://total-simulation-transformation-together.trycloudflare.com/app?lang=en
- For a direct crypto view without sign-in: https://total-simulation-transformation-together.trycloudflare.com/markets?asset_class=crypto&lang=en
- Keep the laptop awake, connected, and the workers running. Do not restart the tunnel immediately before the demo.
- The promotion message supplied by the module asks for at least ten real users and dated evidence linking feedback to improvements. Recruitment, social posting, poster creation and QR generation remain your tasks. No promotion or outreach has been sent.
- Keep dated screenshots of views, likes, shares, comments, saves and visits when you collect them. The Social Media Impact Award is separate from the grade, according to the message you supplied. Uno is optional according to that same message.
- The official ENT207TC Module Handbook and Assessment Brief were not found in the reviewed material. A local older prototype brief describes a different prediction-market concept. This deck does not certify compliance with every module criterion. Confirm the assessment criteria and pitch duration against the official documents.
- Revenue model, campus partners, paid features and ten-user recruitment are proposals or targets, not existing commercial results.

## Product sources

- Repository state used: https://github.com/deepdevjose/explainable-market/tree/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/
- News normalization: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/collector.py
- AI input and output validation: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/ai.py
- Product scope: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/README.md
- Forecasting method: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/intelligence/forecasting.py
- Public routes: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/application.py and https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/api/routes.py
- Language handling: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/market_explained/localization.py
- Current demo hosting: https://github.com/deepdevjose/explainable-market/blob/f7bd85fe44f215ba83ba9e6e308c858a4f8b140d/docs/LAPTOP_DEMO.md

Screenshots show the actual running application captured on 12 November 2026. No external market-size statistics, invented user feedback or superiority rankings support this pitch.


## Presentation files

- Commercial deck: Explainable_Market_Commercial_EN.pptx
- Technical deck: Explainable_Market_Technical_EN.pptx
- Technical speech: Explainable_Market_Technical_Speech_EN.md

The previous ten-slide pitch has been superseded by the eleven-slide commercial version. Both versions preserve the existing app branding.
