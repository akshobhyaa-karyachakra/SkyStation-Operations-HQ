# SkyStation Frontend Redesign Execution Plan

**Goal:** Make the synthetic preview feel like a focused operations command surface while preserving the protected production boundary.

**Visual thesis:** One dominant management decision per page, supported by a small number of high-signal visuals and evidence paths.

**Execution order:**

1. **Reduce competition in the first viewport.** Keep the management statement and primary visual dominant; soften secondary panels, remove repeated preview chrome, and preserve the Mission Control palette.
2. **Make controls consequential.** Daily/Weekly/Monthly, Activity periods, and Inventory family tabs must alter the visible values or visual emphasis rather than only changing active styling.
3. **Strengthen data visualisation.** Add chart-side interpretation, explicit legends, and clear units for percentages, counts, hours, and currency.
4. **Improve fleet storytelling.** Use the existing asset imagery and show family, readiness, relation, maintenance, and next activity as one traceable unit.
5. **Keep demo and production separate.** Synthetic values remain confined to `design-preview.html`; production continues to fail closed when current protected data is unavailable.
6. **Verify.** Test direct preview access, all seven sections, hash navigation, controls, HTML integrity, responsive constraints, and the production unavailable-state behavior.

**Acceptance criteria:**

- The preview is clearly marked as synthetic and authentication-free.
- The first viewport has a readable dominant statement and no accidental overflow.
- Analytics and period controls visibly change content.
- The production shell never displays representative metrics when source state is unavailable.
- No credentials or internal snapshots are present in the preview or committed frontend.
