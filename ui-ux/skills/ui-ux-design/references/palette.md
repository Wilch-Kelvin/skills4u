# Colour and tokens

## 1. Pick the brand colour

- Start from the chosen direction's mood words. Most products want a vivid
  accent (roughly OKLCH chroma ≥ 0.15); calm or editorial directions can go
  deeper and quieter, but never muddy.
- Avoid colours taken by sibling products, close competitors, and the
  framework default blue unless it is a deliberate choice.
- Name it ("Electric lime", "Ultraviolet"). Named colours get used with intent.

## 2. Build the token set

Every token has a light and a dark value. Components use tokens only.

| Token | Light | Dark | Use |
|---|---|---|---|
| `brand` | base | slightly lighter or brighter | primary buttons, key accents |
| `brand-strong` | ~10–15% darker | ~10% lighter | pressed state, links, accent text |
| `brand-soft` | brand at ~12% on surface | brand at ~18% on canvas | tinted chips, selected rows |
| `on-brand` | white or near-black, by contrast | same rule | text and icons on `brand` |
| `canvas` | off-white (e.g. `#F7F7F9`) | near or true black (`#0B0B0F` / `#000`) | app background |
| `surface` | `#FFFFFF` | a step above canvas (e.g. `#121216`) | cards |
| `surface-raised` | `#FFFFFF` | another step (e.g. `#1C1C21`) | sheets, popovers |
| `hairline` | black at ~8% | white at ~12% | borders and dividers |
| `ink` | near-black (e.g. `#111114`) | near-white (e.g. `#F5F5F7`) | primary text |
| `ink-muted` | mid grey that passes 4.5:1 | light grey that passes 4.5:1 | secondary text |
| `success` / `warning` / `danger` | tuned to sit beside the brand | lighter variants | status, always with an icon or text |

Choose `on-brand` by measured contrast, not habit: yellows, limes and light
cyans need near-black text.

**Dark mode:** true black (`#000`) suits OLED-heavy mobile apps and glass;
near-black is easier on the eyes for long reading. Decide once and record it.
Raised surfaces get lighter, not shadowed, and accents usually need a lighter,
slightly less saturated variant.

## 3. Check contrast with the script

Run it on every pair that carries text or meaningful UI, in both themes:

```bash
python3 <skill-dir>/scripts/contrast.py "#7C3AED:#FFFFFF" "#A1A1AA:#000000"
```

It prints the ratio and WCAG AA pass or fail (4.5:1 for body text, 3:1 for
large text, icons and control borders). Colours with alpha (`#RRGGBBAA`) are
composited over the background first.

- If `brand` on `on-brand` fails, change the brand's lightness before you
  desaturate it.
- Over glass or gradients, measure against the *real composite* at its
  brightest point, not a flat colour.
- Keep at least two distinct grey levels for secondary and tertiary text.

## 4. Preview

Fill `assets/palette-preview.html`: replace `__TOKENS_JSON__` with an array of
`{ name, why, light: {...tokens}, dark: {...tokens} }`. It renders each
direction as a small phone mock in light and dark, side by side. Open it in a
browser, or share it however the user prefers.

## 5. Write the tokens into code

- A typed tokens module, for example `src/theme/colors.ts`:
  ```ts
  // One source of truth: screens read tokens, never hex values.
  export const colors = {
    light: { brand: "#…", canvas: "#…" },
    dark: { brand: "#…", canvas: "#…" },
  } as const;
  ```
- Web: CSS variables in `:root` plus a dark block (see `web.md`).
- Native: an asset catalog colour set (iOS) or `lightColorScheme` /
  `darkColorScheme` (Compose).
- Record the palette with names and hex values in `DESIGN.md`.
