# UI Enhancement Context for Claude Code

> **Purpose**: Quick reference for Claude Code when implementing UI improvements
> **Last Updated**: January 2025
> **Project**: Lyrics to Slides (and all future React projects)

---

## Preferred Tech Stack

### Core Foundation (Always Use)
```bash
# Styling & Components
- Tailwind CSS (utility-first styling)
- shadcn/ui (copy-paste components, not dependencies)

# Animation Libraries
- GSAP (@gsap/react) - Complex animations, scroll effects
- Framer Motion - React UI micro-interactions

# Icons
- Lucide React (preferred)
```

### Installation Commands (Copy-Paste Ready)

```bash
# Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# shadcn/ui
npx shadcn@latest init
npx shadcn@latest add button card dialog input select

# Animations
npm install gsap @gsap/react framer-motion

# Icons
npm install lucide-react
```

---

## Quick Decision Guide

| Need | Use This | File Location |
|------|----------|---------------|
| Complex scroll animation | GSAP + ScrollTrigger | See UI_ENHANCEMENT_GUIDE.md |
| Button hover effect | Framer Motion | See ANIMATION_PATTERNS.md #12 |
| Page transition | Framer Motion | See ANIMATION_PATTERNS.md #21 |
| Loading spinner | Framer Motion | See ANIMATION_PATTERNS.md #16 |
| Staggered list | Framer Motion variants | See ANIMATION_PATTERNS.md #9 |
| UI components | shadcn/ui | Run: `npx shadcn@latest add [component]` |
| SVG animation | GSAP MorphSVG | See UI_ENHANCEMENT_GUIDE.md |
| Parallax effect | GSAP ScrollTrigger | See ANIMATION_PATTERNS.md #7 |

---

## Key Facts to Remember

### GSAP
- ✅ **100% FREE** as of April 2025 (all premium plugins included!)
- Best for: Scroll-triggered animations, complex timelines, SVG manipulation
- Plugins available: ScrollTrigger, SplitText, MorphSVG, Draggable
- Use `useGSAP` hook for React (automatic cleanup)

### Framer Motion
- Best for: React component animations, page transitions, micro-interactions
- Declarative API (feels like React)
- Use `AnimatePresence` for mount/unmount animations
- Has `useReducedMotion()` hook for accessibility

### shadcn/ui
- NOT a package - components are copied into your project
- You own and control the code
- Built on Radix UI (accessible by default)
- Install with: `npx shadcn@latest add [component-name]`
- Components go to `src/components/ui/`

---

## Project Structure (Standard)

```
src/
├── components/
│   ├── ui/                    # shadcn components
│   │   ├── button.jsx
│   │   ├── card.jsx
│   │   └── ...
│   ├── animations/            # Reusable animation wrappers
│   │   ├── FadeIn.jsx
│   │   ├── ScrollReveal.jsx
│   │   └── StaggeredList.jsx
│   └── common/                # App-specific components
├── lib/
│   ├── gsap.js               # GSAP plugin registration
│   └── utils.js              # shadcn utils
├── hooks/
│   ├── useAnimation.js
│   └── ...
└── styles/
    └── globals.css
```

---

## Common Patterns (Quick Copy)

### 1. Fade In on Scroll
```jsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 40 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.6 }}
>
  {children}
</motion.div>
```

### 2. GSAP Scroll Trigger
```jsx
import { useGSAP } from '@gsap/react';
import { gsap, ScrollTrigger } from '@/lib/gsap';

useGSAP(() => {
  gsap.from('.element', {
    scrollTrigger: {
      trigger: '.element',
      start: 'top 80%',
      end: 'top 20%',
      scrub: 1
    },
    opacity: 0,
    y: 100
  });
}, []);
```

### 3. Staggered List
```jsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

<motion.ul variants={container} initial="hidden" animate="show">
  {items.map((item, i) => (
    <motion.li key={i} variants={item}>{item}</motion.li>
  ))}
</motion.ul>
```

### 4. Hover Button
```jsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
  Click me
</motion.button>
```

---

## Important Configuration Files

### tailwind.config.js (Required Setup)
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### src/index.css (Add Tailwind Directives)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### src/lib/gsap.js (GSAP Plugin Registration)
```javascript
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export { gsap, ScrollTrigger };
export default gsap;
```

---

## Best Practices (Must Follow)

### Performance
1. ✅ Animate `transform` and `opacity` only (GPU-accelerated)
2. ❌ Avoid animating `width`, `height`, `top`, `left`, `margin`
3. Use `will-change` sparingly, remove after animation
4. Limit concurrent animations to prevent jank

### Accessibility
1. **Always** respect `prefers-reduced-motion`:
```javascript
import { useReducedMotion } from 'framer-motion';

const shouldReduceMotion = useReducedMotion();
const animate = shouldReduceMotion ? { x: 0 } : { x: 100 };
```

2. Ensure keyboard navigation works with animations
3. Add ARIA labels to loading states

### UX Guidelines
- Micro-interactions: 100-300ms
- UI transitions: 300-500ms
- Page transitions: 300-600ms
- Scroll animations: 800-1200ms

### Easing
- **ease-out**: Elements entering (fast start, slow end)
- **ease-in**: Elements exiting (slow start, fast end)
- **ease-in-out**: Elements changing position
- **spring**: Natural, physics-based motion

---

## When Implementing UI Enhancements

### Step-by-Step Process

1. **Check existing stack**
   - Is Tailwind installed? (`tailwind.config.js` exists?)
   - Is shadcn/ui initialized? (`components.json` exists?)
   - Are animation libraries installed? (check `package.json`)

2. **Install missing dependencies** (see Installation Commands above)

3. **Create reusable components** in `src/components/animations/`
   - Don't repeat animation logic
   - Make components flexible with props

4. **Use shadcn for UI primitives**
   - `npx shadcn@latest add [component]`
   - Customize in `src/components/ui/`

5. **Apply animations consistently**
   - Use same timing/easing for similar interactions
   - Keep it subtle unless intentionally flashy

6. **Test accessibility**
   - Test with keyboard navigation
   - Respect `prefers-reduced-motion`
   - Ensure animations don't block core functionality

---

## Common Issues & Solutions

### Issue: Animations not smooth
**Solution**: Animate `transform` and `opacity` only, not layout properties

### Issue: GSAP not working
**Solution**: Check if plugins are registered in `src/lib/gsap.js`

### Issue: Framer Motion exit animations not working
**Solution**: Wrap with `<AnimatePresence mode="wait">`

### Issue: Page transition flicker
**Solution**: Use `mode="wait"` in AnimatePresence

### Issue: Scroll trigger not firing
**Solution**: Enable markers for debugging: `markers: true`

---

## Where to Find More Info

- **Full Guide**: `UI_ENHANCEMENT_GUIDE.md` (comprehensive documentation)
- **Code Examples**: `ANIMATION_PATTERNS.md` (35 ready-to-use patterns)
- **Official Docs**:
  - GSAP: https://gsap.com/docs/
  - Framer Motion: https://www.framer.com/motion/
  - shadcn/ui: https://ui.shadcn.com/
  - Tailwind: https://tailwindcss.com/docs

---

## Implementation Workflow Example

When user requests: **"Make the search results animate in"**

1. ✅ Check if Framer Motion is installed
2. ✅ Create `<StaggeredList>` component if not exists
3. ✅ Wrap search results with component:
   ```jsx
   <StaggeredList>
     {results.map(result => (
       <StaggeredItem key={result.id}>
         <ResultCard result={result} />
       </StaggeredItem>
     ))}
   </StaggeredList>
   ```
4. ✅ Customize timing/easing if requested
5. ✅ Test with `prefers-reduced-motion`

---

## What to Always Include

When creating new animation components:
1. **Props for customization** (delay, duration, direction, etc.)
2. **Sensible defaults** (don't require all props)
3. **Accessibility support** (reduced motion)
4. **TypeScript types** if project uses TS
5. **Example usage** in comments

---

## Quick Reference: Component Props

### FadeIn
- `delay`: number (default: 0)
- `duration`: number (default: 0.6)
- `direction`: 'up' | 'down' | 'left' | 'right'
- `once`: boolean (default: true)

### ScrollReveal (GSAP)
- `start`: string (default: 'top 80%')
- `end`: string (default: 'top 20%')
- `scrub`: boolean | number (default: false)
- `markers`: boolean (default: false)

### StaggeredList
- `stagger`: number (default: 0.1)
- `delay`: number (default: 0)

### AnimatedButton
- All regular button props
- `variant`: shadcn button variants

---

## Remember

- **Subtle is better than flashy** (usually)
- **Performance > Wow factor**
- **Every animation should serve a purpose** (feedback, guidance, delight)
- **Test on lower-end devices**
- **Users can disable animations** (respect their choice)

---

**When in doubt, check `UI_ENHANCEMENT_GUIDE.md` or `ANIMATION_PATTERNS.md`**
