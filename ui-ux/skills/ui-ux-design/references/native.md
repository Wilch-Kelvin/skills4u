# SwiftUI and Jetpack Compose

The same rules apply natively: tokens, one radius scale, press feedback,
every state, both themes. The platform supplies most of the accessibility if
you use its building blocks.

## SwiftUI

- **Tokens:** colour sets in the asset catalog with Any/Dark appearances,
  exposed as `Color` extensions (`Color.brand`, `Color.surface`). Radii and
  spacing as static constants.
- **Type:** use text styles (`.font(.title.bold())`) or a custom font with
  `relativeTo:` so Dynamic Type still scales it.
- **Press:** a custom `ButtonStyle` that scales to 0.97 with
  `.animation(.spring(duration: 0.25, bounce: 0.3), value: configuration.isPressed)`,
  plus `.sensoryFeedback(.selection, trigger:)` for meaningful actions.
- **Reduce motion:** read `@Environment(\.accessibilityReduceMotion)` and
  swap movement for opacity.
- **Navigation:** `TabView` for top-level sections, `NavigationStack` for
  depth, sheets for create and edit.
- **Glass (iOS 26+):** see `glass.md`.

## Jetpack Compose

- **Tokens:** a `MaterialTheme` with your own `lightColorScheme` and
  `darkColorScheme` from the brand palette. Turn off dynamic colour if the
  brand must stay fixed. Add extra tokens with a `CompositionLocal`.
- **Type:** a custom `Typography` with your font family; use `sp` so system
  font scale works.
- **Press:** `Modifier.graphicsLayer { scaleX = s; scaleY = s }` driven by
  `animateFloatAsState(if (pressed) 0.97f else 1f, spring(...))` from
  `interactionSource.collectIsPressedAsState()`; haptics via
  `LocalHapticFeedback`.
- **Targets:** keep `minimumInteractiveComponentSize()`; give icons a
  `contentDescription`.
- **Navigation:** a `NavigationBar` with 3–5 destinations on phones, a
  `NavigationRail` or drawer on large screens; handle predictive back.
- **Edge to edge:** call `enableEdgeToEdge()` and apply window insets padding.
