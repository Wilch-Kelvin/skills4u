# Web (Next.js, React, plain CSS)

Examples assume Next.js App Router, Tailwind CSS v4 and the `motion` package;
the ideas carry over to any stack.

## Tokens as CSS variables

```css
/* globals.css: dark mode swaps values, not class names */
@import "tailwindcss";
@theme {
  --color-brand: var(--brand);
  --color-canvas: var(--canvas);
  --color-surface: var(--surface);
  --color-ink: var(--ink);
  --color-ink-muted: var(--ink-muted);
  --radius-card: 20px;
}
:root {
  --brand: #…; --on-brand: #…; --canvas: #F7F7F9; --surface: #fff;
  --ink: #111114; --ink-muted: #5F5F6B; --hairline: #00000014;
}
@media (prefers-color-scheme: dark) {
  :root {
    --brand: #…; --canvas: #0B0B0F; --surface: #121216;
    --ink: #F5F5F7; --ink-muted: #A1A1AA; --hairline: #ffffff1f;
  }
}
body { background: var(--canvas); color: var(--ink); }
```

If users can pick a theme, mirror the dark block under `[data-theme="dark"]`
and guard the media query with `:root:not([data-theme="light"])`.

## Press feedback

```tsx
"use client";
import { motion, useReducedMotion } from "motion/react";

// A quick spring to 0.97 on press; skipped when the user asks for less motion.
export function Button(props: React.ComponentProps<typeof motion.button>) {
  const reduce = useReducedMotion();
  return (
    <motion.button
      whileTap={reduce ? undefined : { scale: 0.97 }}
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className="h-12 rounded-full bg-brand px-6 font-semibold text-[var(--on-brand)]
                 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      {...props}
    />
  );
}
```

Without a motion library: `transition: scale .18s cubic-bezier(.34,1.56,.64,1)`
and `:active { scale: .97 }`, disabled under `prefers-reduced-motion`.

## Layout

- Design at 375px, then add `md:` and `lg:` layouts. On desktop use a centred
  max-width column or sidebar plus content; don't stretch cards edge to edge.
- Use `min-h-dvh` rather than `100vh` on mobile.
- Page transitions: fade plus a small rise (~8px), under ~250 ms.
- With the App Router, put skeletons in `loading.tsx` so they stream
  automatically.

## Gotchas

- Anything that reads `localStorage` should render a skeleton until hydrated,
  or you get a hydration mismatch.
- `next/image` with explicit sizes; keep client components small.
- Focus rings are part of the look; style them, never remove them.
- Inputs at 16px or larger, or iOS Safari zooms on focus.
