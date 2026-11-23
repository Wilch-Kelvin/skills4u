# Quality checklist

Work top to bottom: earlier sections block release, later ones polish. Each
line is a check; fix anything that fails before delivering. Sources behind
these rules: WCAG 2.2, Apple Human Interface Guidelines, Material Design 3 and
Core Web Vitals.

## 1. Accessibility (blocking)

- [ ] Text contrast ≥ 4.5:1 (≥ 3:1 for large text, icons, control borders and
      focus rings) in **both** themes, measured with `scripts/contrast.py`.
- [ ] Every icon-only control has an accessible name (`aria-label`,
      `accessibilityLabel`, `contentDescription`).
- [ ] Visible focus indicator on every interactive element; never removed.
- [ ] Focus and reading order match the visual order; headings never skip a
      level.
- [ ] Meaning never relies on colour alone (add an icon, text or pattern).
- [ ] Text scales with the system setting (Dynamic Type, font scale, 200% zoom)
      without clipping; no fixed-height text rows.
- [ ] Reduced motion is respected; reduced transparency and increased contrast
      are respected where the design uses them.
- [ ] Modals and multi-step flows have a clear way out; focus is trapped in and
      returned from modals.
- [ ] Images that carry meaning have alt text; decorative ones are hidden.

## 2. Touch and interaction (blocking)

- [ ] Targets ≥ 44×44 pt (iOS) or 48×48 dp (Android), with ≥ 8 px between
      neighbours. Extend the hit area when the visual must stay small.
- [ ] Press feedback within ~100 ms, without shifting layout.
- [ ] Nothing important is hover-only or gesture-only; swipe actions have a
      visible alternative.
- [ ] System gestures (back swipe, home indicator) aren't hijacked.
- [ ] Async buttons show progress and can't be double-submitted.
- [ ] Destructive actions confirm first or offer undo, and look different from
      primary actions.

## 3. Layout and responsiveness

- [ ] Designed mobile first (~375 wide), then tablet and desktop.
- [ ] No horizontal scroll; never disable pinch zoom on web.
- [ ] Safe areas respected for headers, tab bars and bottom buttons; scroll
      content isn't hidden behind fixed bars.
- [ ] Readable line length (about 45–75 characters); desktop content sits in a
      sensible max width.
- [ ] Systematic breakpoints and spacing scale; one z-index scale.
- [ ] Layout survives landscape and the smallest supported phone.

## 4. Navigation

- [ ] Back is predictable and restores scroll position, filters and input.
- [ ] The current location is visibly marked.
- [ ] Mobile bottom navigation has 3–5 top-level items, each with icon *and*
      label.
- [ ] Primary and secondary navigation are clearly separated; patterns aren't
      mixed at one level (tabs plus sidebar plus bottom bar).
- [ ] Key screens are deep-linkable (URL or app link).
- [ ] Sign out and delete account are separated from everyday items.

## 5. Forms and feedback

- [ ] Every field has a visible label (placeholders aren't labels).
- [ ] Correct input types trigger the right keyboard; autofill works.
- [ ] Validate on blur or submit, not every keystroke; the error sits by the
      field, says what's wrong and how to fix it, and is announced to screen
      readers.
- [ ] After a failed submit, focus moves to the first error.
- [ ] Required fields are marked; helper text persists for complex inputs.
- [ ] Long forms save drafts; closing with unsaved changes asks first.
- [ ] Success is confirmed briefly (toast, tick, state change); toasts don't
      steal focus.

## 6. Type and colour

- [ ] Only tokens: `grep -nE "#[0-9a-fA-F]{3,8}\b"` on changed component files
      finds nothing new.
- [ ] A small type scale (3–5 sizes) with weight carrying hierarchy; body
      16px+ on mobile; tabular figures for numbers that change.
- [ ] Line height 1.4–1.6 for body; tight tracking only on large headings.
- [ ] Dark theme uses tuned variants, not inverted colours.
- [ ] Wrap rather than truncate; when truncating, the full text is reachable.

## 7. Motion

- [ ] Every animation explains a change (enter, exit, reorder, expand).
- [ ] 150–300 ms for micro-interactions, ≤ 400 ms for larger transitions;
      exits a little faster than entrances.
- [ ] Springs or ease-out; never linear for UI movement.
- [ ] Only transform and opacity animate; no layout-shifting animation.
- [ ] Animations are interruptible and never block input.
- [ ] At most one or two animated focal points per view; list items stagger
      by ~30–50 ms.
- [ ] One set of duration and easing tokens across the product.

## 8. Performance

- [ ] Images sized and lazy-loaded below the fold; dimensions reserved so
      nothing jumps (CLS < 0.1).
- [ ] Fonts load without invisible text (`font-display: swap` or the
      framework loader); only the weights used.
- [ ] Lists of 50+ rows are virtualised.
- [ ] Skeletons appear for waits over ~300 ms; offline and slow-network
      states exist where relevant.

## 9. Style consistency

- [ ] One icon family, one stroke width, filled vs outline used consistently;
      no emoji as icons.
- [ ] One depth model and one radius scale.
- [ ] Platform conventions respected (iOS vs Android controls and navigation)
      unless the brand deliberately overrides them.
- [ ] Official logos used unmodified.

## 10. Charts and data

- [ ] The chart type fits the data (trend → line, comparison → bar, share →
      bar or donut with ≤ 5 parts).
- [ ] Legends, axis labels with units, and exact values on hover or tap.
- [ ] Series are distinguishable without colour; a table or text summary is
      available for screen readers.
- [ ] Empty, loading and error states for every chart.

## Before you hand over

- [ ] Checked in light and dark, on a small phone and desktop.
- [ ] Loading, empty, error and success states all exist.
- [ ] Anti-generic pass done; at least one signature detail per screen.
- [ ] Anything you couldn't verify (no device, no screen reader) is listed.
