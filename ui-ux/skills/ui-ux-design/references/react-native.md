# Expo and React Native

Examples assume Expo Router, NativeWind, Reanimated, Gesture Handler and
`expo-haptics`. Swap in your project's equivalents.

## Theme

- Keep tokens in one module (`src/theme` or a shared `tokens` package) and map
  them into NativeWind's config with CSS-variable theming (`vars()` for light
  and dark).
- Follow the system with `useColorScheme()`. With a black canvas, also set the
  `StatusBar` style and the `expo-system-ui` background, or a white flash shows
  on launch.

## Press feedback (the core primitive)

```tsx
// Every tappable surface uses this, so the feel is consistent app-wide.
import { Pressable, type PressableProps } from "react-native";
import Animated, { useSharedValue, useAnimatedStyle, withSpring, useReducedMotion } from "react-native-reanimated";
import * as Haptics from "expo-haptics";

const APressable = Animated.createAnimatedComponent(Pressable);
const SPRING = { damping: 15, stiffness: 300, mass: 0.6 }; // quick, slightly bouncy

export function PressableScale({ onPressIn, onPressOut, style, ...rest }: PressableProps) {
  const scale = useSharedValue(1);
  const reduce = useReducedMotion(); // honours the OS setting
  const animated = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  return (
    <APressable
      {...rest}
      style={[animated, style as object]}
      onPressIn={(e) => {
        if (!reduce) scale.value = withSpring(0.97, SPRING);
        void Haptics.selectionAsync();
        onPressIn?.(e);
      }}
      onPressOut={(e) => {
        scale.value = withSpring(1, SPRING);
        onPressOut?.(e);
      }}
    />
  );
}
```

## Building blocks

- **Screen:** `SafeAreaView` with the canvas colour, 16–20 horizontal padding,
  and a large title that collapses on scroll where it suits the platform.
- **Card:** surface colour, the project's card radius, a hairline border or
  its elevation token. Glass rules: `glass.md`.
- **Primary button:** brand fill, `on-brand` text, minimum height 48–52,
  wrapped in `PressableScale`.
- **Bottom sheet:** for create and edit flows, so the primary action stays in
  thumb reach (for example `@gorhom/bottom-sheet`), with a grabber.
- **Lists:** `FlashList` for long lists; animate rows with Reanimated
  `entering` and `layout` springs.
- **Skeleton:** blocks shaped like the content with a gentle pulse that stops
  under reduce-motion.
- **Celebration:** a spring-in tick plus a success haptic; save bigger moments
  for real milestones.

## Gotchas

- `Pressable` needs `accessibilityRole="button"` and an `accessibilityLabel`
  when it has no visible text.
- Use `hitSlop` to reach 44pt when an icon must look small.
- Test at the largest system font size; fixed-height rows break.
- Android: check the back button and edge-to-edge insets.
