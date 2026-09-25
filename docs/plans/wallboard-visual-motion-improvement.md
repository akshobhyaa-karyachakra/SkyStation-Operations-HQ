# Public Wallboard Visual and Motion Improvement Plan

**Goal:** Rework the public wallboard so it feels like a calm, authored Skylark operations product rather than a direct mockup transcription, with motion that explains operational change instead of decorating the screen.

**Design read:** A public office-TV operations wallboard for people scanning from a distance, with an industrial editorial language, restrained asymmetry, and low-frequency storytelling motion.

**Motion dial:** 3/10. The wallboard should feel alive when data changes or a screen changes, but it must remain readable and calm during a full-day TV loop.

**Visual density:** 5/10. Keep the core numbers legible at distance, reduce ornamental panels, and give each screen one visual idea.

---

## 1. Establish a new wallboard art direction

**Files:**
- Modify: `assets/wallboard.css`
- Modify: `assets/wallboard.js`
- Reference: `docs/public-dashboard-data-brief.md`

Replace the current mockup-transcription language with a consistent system:

- Use one dark mineral background, one Skylark orange accent, and muted operational colors only where they encode state.
- Retire the repeated rounded-panel treatment. Use open composition, aligned rules, sparse borders, and one primary surface per screen.
- Replace the repeated top eyebrow plus large headline formula with a smaller screen title, a clear question, and one dominant metric or visualization.
- Give each screen a different composition: pulse as a large number plus signal band, delivery as a horizontal flow, crew as a field of availability blocks, geography as a regional matrix, reporting as a cadence chart, and fleet as a silhouette-led readiness board.
- Keep the supplied mockup hierarchy as a reference for information priority, not as a pixel-level layout source.

Acceptance check: the six screens should be distinguishable by composition alone, even with text blurred.

## 2. Replace robotic copy and metadata rhythm

**Files:**
- Modify: `assets/wallboard.js`

Rewrite visible copy to be short, concrete, and operational. Avoid repeated labels such as `QUESTION`, `PUBLIC BOUNDARY`, and `INTERPRETATION` on every screen. Keep the required meaning, but express it through a shared small footer and screen-specific language.

Examples:

- Operations Pulse: `How much scheduled work is in the air?`
- Delivery Flow: `Where does work slow down?`
- Crew Presence: `Can today's work be covered?`
- Reporting Outcomes: `Are flown jobs becoming customer-ready reports?`

Acceptance check: each screen has one question, one interpretation, and one public-safe footer without repeating the same three-line metadata block.

## 3. Build a deliberate screen transition system

**Files:**
- Modify: `assets/wallboard.js`
- Modify: `assets/wallboard.css`

Remove the current generic `rise` and `focus-in` entrance treatment. Implement two motion layers:

1. **Screen transition:** outgoing screen fades and slightly desaturates; the incoming screen crossfades in with a short directional drift based on navigation direction. Automatic cycling uses the same short transition, with no theatrical zoom.
2. **Data storytelling:** the primary metric counts or interpolates only when its value changes. Bars and flow segments grow from their previous value. No element should repeatedly bounce, pulse, or shimmer while idle.

Use transform and opacity only. Keep automatic transitions below 500ms and keyboard navigation immediate. Respect `prefers-reduced-motion` by disabling interpolation and showing the final state immediately.

Acceptance check: a viewer can tell whether the screen changed because of navigation or because the data changed, and idle screens remain still.

## 4. Add one purposeful live cue

**Files:**
- Modify: `assets/wallboard.css`
- Modify: `assets/wallboard.js`

Replace the always-present decorative freshness dot with a restrained source-status cue. The cue changes only when the fixture/API is loaded, stale, unavailable, or refreshed. It must not pulse continuously.

Acceptance check: the wallboard has one visible sign of freshness, and it communicates a real data state.

## 5. Redesign each screen around one visual idea

**Files:**
- Modify: `assets/wallboard.js`
- Modify: `assets/wallboard.css`

Implement screen-specific composition updates:

- **Operations Pulse:** large execution rate, a single thin scheduled-to-flown band, and a small attention strip for the remaining work.
- **Delivery Flow:** six connected stages with proportional gaps, using one continuous path rather than stacked card rows.
- **Crew Presence:** compact availability matrix with team labels and one coverage statement, removing dashboard-like repeated panels.
- **Geographic Operations:** state tiles ordered by attention, with the table and tile map treated as one composition instead of separate boxed regions.
- **Reporting Outcomes:** a clean seven-day cadence chart with planned/submitted distinction and one late-day callout.
- **Fleet & Readiness:** equipment silhouettes or existing approved assets as the visual anchor, with readiness counts aligned to each family.

Acceptance check: each page answers its question within five seconds and has one obvious focal point.

## 6. Make the layout adaptive by composition, not only scale

**Files:**
- Modify: `assets/wallboard.css`
- Modify: `assets/wallboard.js`

Keep the fixed 1920x1080 kiosk stage for TV use, but define composition breakpoints inside the stage and a deliberate mobile reading mode. Avoid shrinking the entire desktop wallboard until text becomes illegible.

Acceptance targets:

- 1920x1080 and 1366x768: complete composition visible with no clipping.
- 390x844: single-column reading mode with the focal metric first and horizontal charts intentionally scrollable only where necessary.
- The stage transform must be measured and verified with real browser screenshots, not inferred from DOM smoke tests.

## 7. Add visual QA that can catch design regressions

**Files:**
- Create or modify: `scripts/wallboard-visual-qa.mjs`
- Modify: `docs/public-dashboard-data-brief.md` if assumptions change

Use a Chromium-capable browser in the QA environment to capture:

- All six screens at 1920x1080 and 1366x768.
- The mobile route at 390x844.
- One automatic transition and one keyboard transition.
- `current`, `stale`, `partial`, `needs_review`, `unavailable`, and `no_data` states.

The QA script must report viewport size, stage bounding box, horizontal overflow, console errors, and screenshot paths. Visual review must confirm that the stage bounding box is fully contained and that the focal content is not clipped.

## 8. Verification gates before publishing

Run:

```bash
node --check assets/wallboard.js
node --check assets/wallboard-data.js
node scripts/wallboard-visual-qa.mjs
node /opt/data/tmp/wallboard-jsdom/smoke.js

git diff --check
```

Verify that:

- Public-safe data rules remain intact.
- No direct Monday or protected-source calls are introduced.
- Reduced-motion behavior is static and readable.
- Keyboard navigation and automatic cycling still work.
- The hosted route is tested after GitHub Pages propagation.

Publish only after screenshot-level QA passes. The next implementation should be treated as a visual redesign, not another CSS containment patch.
