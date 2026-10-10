# Manual signal review (10 October 2026)

I reviewed 20 of the 59 generated signals: 7 historical social posts, 6
source-linked sample/GDELT headlines, and 7 live company-feed headlines.
The IDs below are row positions in the local `data/risk_signals.jsonl` from this
run; they may change when a feed is refreshed. This is a small sanity check,
not an accuracy estimate or an evaluation of market impact.

| Row | Ticker | Short description | Event judgement |
| --- | --- | --- | --- |
| 0 | AAPL | The Banker debut delayed | Other/Unclear; no defined risk-event rule |
| 2 | XOM | Refinery restart | Other/Unclear; operational event is not in current taxonomy |
| 3 | JPM | Dividend declared | Corporate Action |
| 4 | NVDA | Speculation ahead of earnings | Earnings/Guidance, but not actual results |
| 6 | AAPL | Multi-ticker options list | Other/Unclear; company relevance is weak |
| 9 | NVDA | Multi-ticker post about Uber/Tesla | Other/Unclear; company relevance is weak |
| 13 | XOM | Capital-spending forecast cut | Earnings/Guidance |
| 14 | AAPL | iPhone Duo unveiled | Product Launch |
| 15 | MSFT | Quarterly results reported | Earnings/Guidance |
| 18 | META | FTC appeal | Regulatory |
| 20 | JPM | Dividend and repurchase plan | Corporate Action |
| 21 | JNJ | Acquisition completed | Merger/Acquisition |
| 24 | META | Safety probe | Regulatory |
| 25 | AAPL | Education initiative launched | Other/Unclear; previously false Product Launch |
| 29 | AAPL | Devices arrive in stores | Other/Unclear under the current narrow launch rule |
| 33 | AAPL | iPhone Duo unveiled | Product Launch |
| 41 | MSFT | Earnings release *date* announced | Other/Unclear; previously false Earnings/Guidance |
| 44 | AMZN | New tablets announced | Product Launch; previously missed |
| 47 | GOOGL | Gemini agent introduced | Product Launch |
| 58 | META | Anti-scam education campaign launched | Other/Unclear; previously false Product Launch |

Four clear event-label errors in this sample drove the rule changes. I also
added a rule for company headlines saying a device "debuts," which fixes a
similar missed launch outside the 20 reviewed rows. The sentiment model was
trained and validated on social posts; its headline labels, and the 1–10
impact scores, have no independent ground-truth evaluation. A neutral class
can have a small nonzero sentiment score because the score is the model's
bullish probability minus bearish probability.

Qualitative sentiment concerns in the reviewed rows: row 0 describes a delay
but is labelled neutral; row 15 describes cloud and AI growth but is labelled
neutral; row 24 describes a safety probe but is labelled neutral. Row 0 is
excluded from rebalancing as `Other/Unclear`; row 15 is used but has an almost
zero score. Row 24 has a negative numeric score despite its neutral class.
These observations are not a measured error rate. Validating or retraining
headline sentiment needs a separate labelled news set.
