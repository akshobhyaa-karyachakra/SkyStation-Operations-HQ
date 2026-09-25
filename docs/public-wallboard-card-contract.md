# Public wallboard card source contract

The wallboard is a public aggregate projection. Browser code must consume only the public projection endpoint or the local synthetic fixture; it must never call Monday, Google Docs, or other protected source systems directly.

## Card mapping

| Screen | Card | Public projection fields | Canonical source families | Refresh boundary |
|---|---|---|---|---|
| Pulse | Operations pulse | flown, scheduled, processed, reported, attention | Flight Operations, Processing/QA, Report Submission | 5 minutes |
| Pulse | Execution rate | flown / scheduled and denominator | Flight Operations | 5 minutes |
| Pulse | Operating chain | planned, flown, processed, reported | Flight Operations, Processing/QA, Report Submission | 5 minutes |
| Crew | Crew presence | classified, active denominator, status counts, safe team labels | Crew Repository / approved public projection | 5 minutes |
| Fleet | Fleet readiness | classified, ready, maintenance, incidents, unclassified | SkyStation Inventory, approved incident aggregate | 5 minutes |
| Fleet | Inventory split | explicit model/version aggregates for V2, V3, vehicle-mounted | SkyStation Inventory | 5 minutes |
| Regions | State activity | state-safe code, completed, in-progress, public status | Flight Operations / approved geographic projection | 5 minutes |
| Delivery | Journey of this month's work | stage counts, largest gap, queue aggregates | Flight Operations, Processing/QA, Report Submission | 5 minutes |
| Reports | Reporting outcomes | submitted, delivered, customer-ready, daily aggregate, open queue | Report Submission | 5 minutes |

## Refresh behavior

- The wallboard displays a five-minute countdown and refreshes the public projection at the expiry boundary.
- A source failure must preserve the card's unavailable treatment rather than display stale values as current.
- A stale source must dim the affected card and show its source age.
- A partial projection must show a bounded value and name the missing source category without exposing IDs or internal notes.
- V2/V3 values are shown only when the source model/version field is explicit. They must not be inferred from partial asset names.

## Google Docs / source logic

The canonical business-logic document is referenced by `docs/business-logic-index.md`. Live Google Docs access is deliberately outside the public browser: it requires an authenticated server-side adapter and a published, redacted projection. Credentials, tokens, document IDs, and protected source rows must never be shipped to GitHub Pages or placed in visible wallboard markup.
