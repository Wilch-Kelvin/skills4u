# Choosing a design direction

Use this when a project has no design system, is being redesigned, or "looks
generic". The output is three concrete directions, the user's pick, and a
written `DESIGN.md`.

## 1. Gather the brief (ask at most two questions)

Find what you can in the repo and README first. You need:

- **Product type:** tool, productivity, social, commerce, finance, health,
  education, developer tool, creative, entertainment.
- **Audience and context:** who, on what device, in what moment (on the bus,
  at a desk, in a hurry, relaxing).
- **Three mood words:** for example *calm, precise, warm*.
- **Look-alikes to avoid:** competitors or apps it must not resemble, and any
  colours already taken by sibling products.

## 2. Propose three directions

Make them genuinely different, not three shades of one idea. For each give:

| Field | Example |
|---|---|
| Name | "Paper and ink" |
| Point of view (one sentence) | Feels like a well-made notebook: quiet, tactile, precise. |
| Style family | Editorial |
| Brand colour | Vermilion `#E4472B` |
| Type | Fraunces for display, Inter for text |
| Shape and depth | Small radii (6–10), hairlines, no shadows |
| Motion personality | Quick, minimal, crossfades |
| Signature detail | Completed items get a hand-drawn strike-through |

Show them with `assets/palette-preview.html` (or quick mockups) and let the
user pick or mix ("A's colour with C's type"). Iterate once or twice.

## 3. Style families

| Family | Looks like | Fits | Watch out for |
|---|---|---|---|
| Soft premium | Big radii (20–28), generous space, one vivid accent, gentle springs | Consumer apps, productivity, education | Turning into a bland "rounded card" kit; needs a strong accent and type |
| Liquid glass | Translucent panels, hairlines, blurred colour glow behind | Modern consumer apps, dashboards with light data | Contrast over glass, GPU cost; read `glass.md` |
| Editorial | Serif display, strong grid, small radii, lots of white | Content, journaling, reading, premium brands | Feeling static; add motion in micro-interactions |
| Swiss / minimal | Grotesk type, strict grid, black, white and one colour | Tools, finance, developer products | Coldness; let the accent and copy carry warmth |
| Neo-brutalist | Thick borders, hard offset shadows, flat bright fills | Youthful, creative, indie products | Accessibility of loud colour pairs; tiring at scale |
| Playful / clay | Chunky shapes, soft 3D, bouncy motion, bright palette | Kids, habits, games, onboarding | Childish for serious tasks; keep text crisp |
| Dark tech | Near-black, monospace accents, neon accent, dense data | Developer tools, analytics, crypto-free fintech | Low contrast secondary text; eye strain |
| Organic / warm | Earthy palette, rounded serif or humanist sans, texture | Wellness, food, sustainability | Muddy colours; check contrast on beige |

## 4. Product hints

- **Finance:** trust first. Tabular numbers, restrained motion, a clear
  positive/negative colour pair that also uses icons or signs, never colour
  alone.
- **Health and wellbeing:** calm palette, larger type, no streak shaming,
  gentle confirmation.
- **Education and habits:** progress you can see, celebrations for real wins,
  forgiving empty states.
- **Productivity:** speed and density, keyboard support on web, quick-add in
  thumb reach on mobile.
- **Commerce:** product imagery leads, price and the primary button always
  visible, a frictionless checkout.
- **Developer tools:** density, monospace for code, a strong dark theme,
  copy-to-clipboard everywhere.
- **Social and content:** content first, chrome recedes, fast media loading.

## 5. Type pairings that aren't the default

All are free (Google Fonts unless noted). Pick by personality, then check
legibility at 14–16px.

| Personality | Display | Text |
|---|---|---|
| Crisp modern | Geist | Geist |
| Friendly geometric | Plus Jakarta Sans | Plus Jakarta Sans |
| Warm rounded | Nunito (800) | Nunito Sans |
| Bold, characterful | Bricolage Grotesque | Inter |
| Technical | Space Grotesk | IBM Plex Sans + IBM Plex Mono |
| Editorial | Fraunces or Instrument Serif | Inter or Source Sans 3 |
| Elegant | Playfair Display | DM Sans |
| Confident sans | Satoshi (Fontshare) | Satoshi |
| Clean product | Manrope | Manrope |
| Futuristic | Sora or Outfit | Inter |

Load only the weights you use, and self-host or use the framework's font
loader so text never flashes invisible.

## 6. Write it down

Copy `assets/DESIGN.template.md` to `DESIGN.md` at the repo root and fill it
in: point of view, tokens (light and dark), type scale, radius scale, depth
model, motion tokens, signature details and do/don't examples. Point the
project's `CLAUDE.md` or `AGENTS.md` at it so every later session uses it.
Larger products can split it into `design-system/MASTER.md` plus
`design-system/pages/<page>.md` overrides.
