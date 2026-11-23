---
name: ui-ux-design
description: Use when designing, building, restyling, mocking up or reviewing any screen, component, flow, form, list, sheet, onboarding, landing page or dashboard, on web or mobile, even when no style is mentioned ("build the settings screen", "make this look premium", "it looks generic", "pick our colours", "design the onboarding", "review this UI"). Finds or creates the project's design system first, proposes distinctive directions instead of template defaults, builds light and dark tokens checked with a contrast script, and runs a priority-ranked quality pass (accessibility, touch, layout, navigation, forms, type, motion, states) before anything ships.
---

# UI/UX design

**The goal:** interfaces that work for everyone and look like *this* product,
not a UI kit with the logo swapped.

Two rules sit above everything else:

1. **The project's design system wins.** These defaults only fill gaps. Never
   override a project's tokens, fonts or patterns with your own taste.
2. **Generic is a defect.** A screen that could belong to any app is not done.
   Fix it the way you would fix a bug (see *Anti-generic pass*).

## Step 0: find the source of truth

Look, in this order, and stop at the first that defines the look:

1. `DESIGN.md` at the repo root, or `design-system/MASTER.md` (with page
   overrides in `design-system/pages/<page>.md`, which win for that page).
2. Design notes in `CLAUDE.md` / `AGENTS.md` / `docs/` (a "Brand" or "Design"
   section).
3. Token files: `tokens.json`, `theme.ts`, `colors.ts`, Tailwind `@theme`,
   `:root` variables in `globals.css`, an asset catalog or `MaterialTheme`.
4. The existing component library and screens.

- **Found a system:** follow it and list any gaps you had to fill.
- **Nothing found and the work is more than one component:** run
  `references/direction.md` to agree a direction with the user, then write
  `DESIGN.md` from `assets/DESIGN.template.md` *before* building screens.
- **Nothing found, one small component:** infer from the surrounding UI and
  say what you inferred.

## Workflow

1. **One job per screen.** Write one line: what the user comes here to do.
   Make that action the most prominent thing on the screen, and keep one
   primary button per view.
2. **Flow first.** Entry → key actions → success, plus the empty, loading and
   error paths. For 3+ screens, draw the flow before mocking anything.
3. **Build with tokens and primitives.** No raw hex, radius or font size in
   components. Create the shared primitives once (Screen, Card, Button with
   press feedback, Skeleton, EmptyState) and reuse them. Platform notes:
   `references/web.md`, `references/react-native.md`, `references/native.md`.
4. **Every state:** default, loading (skeleton), empty (friendly + one next
   step), error (what happened + how to fix, never blaming the user), success
   (a small, proportionate confirmation).
5. **Check.** Run `references/checklist.md` in priority order, in light *and*
   dark, at a small phone width (~360–375) and on desktop. Screenshot when a
   browser or simulator is available. Then do the anti-generic pass.
6. **Report** what you built, the tokens used, the design decisions and why,
   and anything unverified.

## Defaults when the system is silent

| Area | Default | Why |
|---|---|---|
| Colour | One brand colour used with intent; neutrals everywhere else; semantic tokens (`brand`, `surface`, `ink`, `ink-muted`, `hairline`, `danger`…), each with a light and dark value. Process: `references/palette.md`. | One accent reads as confident; tokens make dark mode and rebrands free. |
| Type | One characterful display face plus a highly legible text face (or one strong family). Titles heavy with slightly tight tracking; body 16px+, line height 1.4–1.6; 3–5 sizes total. | Hierarchy from size and weight reads as premium; tiny grey text reads unfinished. |
| Spacing | 4/8-pt scale; gutters 16–24; section gaps clearly bigger than item gaps. | Rhythm groups content without extra lines and boxes. |
| Shape | Pick one radius scale and keep to it. Nested radius = outer radius − padding. | Mismatched corners are the fastest tell of a cheap UI. |
| Depth | Pick one model (hairline borders, soft elevation scale, or glass from `references/glass.md`) and use it everywhere. | Mixed depth systems look assembled, not designed. |
| Press | Every tappable thing responds within ~100 ms (scale ~0.97, state layer or highlight); light haptic on mobile for meaningful actions. | Feedback is the "feel" users remember. |
| Motion | Springs or ease-out, 150–300 ms, transform and opacity only; animate state changes, not decoration; reduce-motion falls back to fades. | Motion should explain what changed. |
| Loading | Skeletons shaped like the content; optimistic updates when safe. | Skeletons feel faster than spinners. |
| Reach | Targets ≥ 44×44 pt (48 dp on Android); primary action in thumb reach on mobile. | Mobile users hold the phone in one hand. |
| Dark | Designed together with light, not inverted. Near-black or true-black canvas, lighter raised surfaces, contrast re-checked. | Dark mode is a second theme, not a filter. |

## Fix in this order

When time is short, work down this list; `references/checklist.md` has the
detail for each.

1. Accessibility (contrast, labels, focus, text scaling)
2. Touch and interaction (targets, feedback, gestures)
3. Layout and responsiveness (no horizontal scroll, safe areas)
4. Navigation (predictable back, clear current location)
5. Forms and feedback (visible labels, errors by the field)
6. Type and colour (tokens, hierarchy, readable measure)
7. Motion (purposeful, interruptible, reduce-motion)
8. Performance (no layout shift, virtualised long lists)
9. Style consistency (one icon set, one depth model)
10. Charts and data (legends, text alternatives)

## Anti-generic pass

Before showing anything, write one sentence: *"This product feels like ___."*
If you can't, the direction is missing; go back to `references/direction.md`.

Then look for these template smells and replace each with a deliberate choice:

- Default system font plus a default framework blue
- Centred hero, three equal feature cards, gradient blob
- Grey-on-grey text, a different shadow on every card
- Every card the same size in a uniform grid, whatever its importance
- Emoji used as icons; mixed outline and filled icons
- Copy that could be on any site ("Unlock your potential")
- Nothing happens on press; content snaps in with no transition

Each screen gets **at least one signature detail**: a moment tied to the
product, such as a celebration when a task completes, a distinctive empty
state, a custom data visual or a crafted transition. Keep it to one or two per
view; more becomes noise.

## References

| File | Read when |
|---|---|
| `references/direction.md` | No design system yet, a redesign, or "it looks generic" |
| `references/palette.md` | Choosing or fixing colours; dark mode |
| `references/checklist.md` | Before delivering or reviewing any UI |
| `references/glass.md` | The direction uses translucent or glass surfaces |
| `references/web.md` | Next.js, React or plain web |
| `references/react-native.md` | Expo or React Native |
| `references/native.md` | SwiftUI or Jetpack Compose |
| `assets/DESIGN.template.md` | Writing the project's `DESIGN.md` |
| `assets/palette-preview.html` | Showing colour directions side by side |
| `scripts/contrast.py` | Any foreground/background pair that carries text or UI |
