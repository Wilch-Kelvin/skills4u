# <Product> design system

> The source of truth for how <Product> looks and feels. Agents and people
> read this before building UI. Change it here first, then in code.

## Point of view

<Product> feels like **<one sentence>**.
Mood words: <word>, <word>, <word>. Never: <what it must not feel like>.

## Colour

Brand colour: **<Name>** `<#HEX>`. Dark canvas: <true black / near-black>.

| Token | Light | Dark | Use |
|---|---|---|---|
| `brand` | | | primary actions, key accents |
| `brand-strong` | | | pressed, links, accent text |
| `brand-soft` | | | tinted chips, selected rows |
| `on-brand` | | | text and icons on brand |
| `canvas` | | | background |
| `surface` | | | cards |
| `surface-raised` | | | sheets, popovers |
| `hairline` | | | borders, dividers |
| `ink` | | | primary text |
| `ink-muted` | | | secondary text |
| `success` / `warning` / `danger` | | | status (always with icon or text) |

Contrast checked with `contrast.py` on <date>: <pairs and ratios>.

## Type

Display: <font, weights>. Text: <font, weights>. Mono: <font, if any>.

| Role | Size / line height | Weight | Tracking |
|---|---|---|---|
| Title | | | |
| Heading | | | |
| Body | 16 / 24 | | 0 |
| Caption | | | |

## Shape, space and depth

- Spacing scale: 4, 8, 12, 16, 24, 32, 48.
- Radius scale: <inputs>, <buttons>, <cards>, <sheets>. Nested = outer − padding.
- Depth model: <hairlines / elevation scale / glass>.
- Icons: <family>, <stroke width>, <filled or outline rule>.

## Motion

- Spring / easing token: <values>. Durations: <micro>, <transition>.
- Press: <scale or state layer>. Haptics: <when>.
- Reduced motion: <fallback>.

## Signature details

1. <The moment that makes this product recognisable>
2. <…>

## Do and don't

| Do | Don't |
|---|---|
| | |

## Page overrides

Pages that deviate from these rules, and how: <none yet>.
