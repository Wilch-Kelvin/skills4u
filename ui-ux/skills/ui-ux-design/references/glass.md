# Liquid glass surfaces

An optional style family: translucent frosted panels over a soft glow of the
brand colour. Use it only when the project's direction calls for it.

## Surfaces

- A soft canvas with one or two blurred pools of the brand colour (the
  "glow") behind content: alpha about .10 in light, .16 in dark.
- Panels: translucent fill plus a 1px hairline border. No heavy shadows; in
  dark mode shadows become 1px rings.
- **Real `backdrop-filter` blur only on floating chrome:** sidebars, tab bars,
  headers, sheets, menus, popovers, toasts. In-flow cards get the translucent
  fill and hairline *without* blur, because blur over a smooth gradient is
  invisible and costs GPU on low-end phones.
- Long lists: **one** glass container with hairline-separated rows, never a
  glass card per row.
- Always ship solid fallbacks for: no `backdrop-filter` support,
  `prefers-reduced-transparency`, and `prefers-contrast: more` (stronger
  borders). iOS Safari ignores reduced transparency, so floating chrome needs a
  denser fill there.

## Colour on glass

- Split the brand colour by job: `brand` for fills and glows, a deeper
  `brand-ink` for accent text, a deeper gradient behind white text, `on-brand`
  for text on fills, and a `control-edge` (≥ 3:1) for checkbox and input
  borders.
- **Measure contrast over the real composite** (panel RGBA over glow over
  canvas, at the glow's brightest point), not against one flat colour.
- Placeholders get a lighter weight than filled values so empty fields never
  read as filled; disabled states must look disabled.

## Motion

- One spring curve as a token (CSS `linear()` sampled spring with a cubic
  fallback) when there's no motion library.
- Press: scale .97 using the standalone `scale` property so it composes with
  entrance transforms; skip disabled controls.
- Screens rise in on navigation, *or* sections stagger in reading order, not
  both; sheets slide up while the scrim fades.
- Navigation chrome never animates on route change.
- Entrance animations use `animation-fill-mode: backwards`, not `both`: a
  retained transform creates a containing block that breaks `position: fixed`
  children.
- Reduced motion: everything becomes fades; presses dim to ~.85 opacity.

## SwiftUI

On iOS 26+, prefer the system glass APIs (`.glassEffect()`,
`GlassEffectContainer`) over hand-made blur, with a material fallback for
older versions.
