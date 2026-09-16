---
name: Nordic Precision
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#3f493f'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#6f7a6e'
  outline-variant: '#becabc'
  surface-tint: '#006d30'
  primary: '#00652c'
  on-primary: '#ffffff'
  primary-container: '#15803d'
  on-primary-container: '#d3ffd5'
  inverse-primary: '#79db8d'
  secondary: '#545f73'
  on-secondary: '#ffffff'
  secondary-container: '#d5e0f8'
  on-secondary-container: '#586377'
  tertiary: '#4a586c'
  on-tertiary: '#ffffff'
  tertiary-container: '#627085'
  on-tertiary-container: '#eff3ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#95f8a7'
  primary-fixed-dim: '#79db8d'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#005323'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#d5e3fc'
  tertiary-fixed-dim: '#b9c7df'
  on-tertiary-fixed: '#0d1c2e'
  on-tertiary-fixed-variant: '#3a485b'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system draws its philosophy from contemporary Scandinavian industrial design and modern, calm fintech and agritech user experiences. It embodies restraint, operational clarity, and grounded confidence. The interface rejects gratuitous decoration, neon washouts, and heavy saturated gradients in favor of structural elegance, quiet off-white surfaces, and tactile typographic structure.

The target audience encompasses professionals, analysts, and operators who require rapid, friction-free interaction with complex data streams—balancing agricultural intelligence, operational metrics, and asset tracking. The UI evokes a sense of architectural calm, institutional precision, and environmental permanence. 

The aesthetic style merges modern functional minimalism with subtle tactile outlines. It relies on architectural layouts, disciplined spacing, and crisp edge definitions rather than heavy drop-shadows or layered blur noise.

## Colors

The color palette is deliberately disciplined. It centers on an organic, botanical forest green (`#15803d`) strictly reserved for active states, positive telemetry, confirmation actions, and critical data highlights. Backgrounds avoid blinding stark white, utilizing a serene slate off-white (`#f8fafc`) for daytime mode and transitioning to deep, muted slate-charcoal tones (`#0f172a` and `#1e293b`) for nighttime visualization.

### Palette Architecture

- **Primary Accent (`#15803d`):** Botanical green. Used purposefully for focused interactive triggers, active navigation toggles, progress bars, and positive trends.
- **Secondary (`#1e293b`):** Deep slate graphite. Applied to primary headings, high-contrast action buttons, and dominant visual anchors.
- **Tertiary (`#475569`):** Medium slate gray. Designates secondary body text, structural icons, and supplementary values.
- **Neutral Base (`#f8fafc`):** Pristine Nordic parchment canvas. Paired with surface containers at pure `#ffffff` and subtle structural partition borders (`#e2e8f0`).
- **Dark Mode Surface Equivalents:** Canvas at `#0b0f17`, card containers at `#131b26`, and hairline structural dividers at `#1e293b`.

## Typography

Typography establishes order through geometric sans-serif shapes and technical monospaced details:

- **Plus Jakarta Sans:** Selected for its clean geometry, high legibility at micro sizes, and warm, balanced modernism. It manages display titles, section headings, and primary body copy.
- **JetBrains Mono:** Introduced selectively for technical figures, financial counters, timestamps, status tags, and tabular sensor data. Its monospaced rhythm brings an industrial, calibrated aesthetic to agritech and fintech metrics.

All body copy strictly enforces comfortable line-height ratios (1.4–1.6) to guarantee effortless scanning across dense operational screens.

## Layout & Spacing

The layout model is governed by an 8pt architectural rhythm, utilizing generous breathing room around focal points to prevent visual fatigue during sustained operational use.

### Grid & Breakpoints
- **Mobile (under 768px):** 4-column fluid layout with `1rem` outer canvas padding and `1rem` gutters. Vertical stack flow with touch targets pegged to a minimum of 44px.
- **Tablet (768px - 1024px):** 8-column fluid grid, balancing side-by-side inspection widgets with master-detail list layouts.
- **Desktop (1024px+):** 12-column fixed grid with a max-width container cap of 1280px, `2.5rem` margins, and `1.5rem` gutters.

Component internals adhere strictly to modular spacing tokens: micro status labels use `space-xs` to `space-sm`, standard cards utilize `space-md` internally, and major section separations use `space-xl`.

## Elevation & Depth

Visual hierarchy is constructed entirely via tonal layering and crisp, low-contrast outlines rather than muddy drop-shadows or saturated glow overlays:

1. **Ground Layer (Canvas):** Off-white `#f8fafc` (Day) or deep charcoal `#0b0f17` (Night).
2. **First Elevation (Cards & Panels):** Solid `#ffffff` (Day) or `#131b26` (Night), encircled by an exact 1px structural hairline border (`#e2e8f0` in Day, `#1e293b` in Night). No elevation shadow is required in standard resting states.
3. **Hover & Active States:** An ultra-diffuse, subtle ambient shadow (`0 2px 8px -2px rgba(15, 23, 42, 0.04)`) provides a slight spatial lift without muddying neighboring data columns.
4. **Modal Overlays & Popovers:** Surface `#ffffff` elevated with a refined perimeter line and a controlled shadow (`0 12px 24px -6px rgba(15, 23, 42, 0.08)`), anchored against a dim, unblurred translucent backdrop (`rgba(15, 23, 42, 0.40)`).

## Shapes

The design system uses deliberate curvature variation based on component scale:

- **Cards, Containers, and Data Panels:** Standardized on `0.75rem` (12px) to `1rem` (16px) corners. This maintains structural cohesion and an architectural presence.
- **Interactive Pill Elements (Segmented switches, filter tags, badges, primary button caps):** Fully rounded pill geometry (`rounded-full`) to differentiate actionable triggers from structural display cards.
- **Form Inputs & Checkboxes:** Scaled at `0.5rem` (8px) for inputs and `0.25rem` (4px) for selection checks, preserving tactile clarity without unnecessary circular exaggeration.

## Components

### Buttons
- **Primary Button:** Deep graphite `#1e293b` fill (or `#15803d` for decisive confirmation tasks), pure white text, fully pill-shaped or 10px rounded, 44px minimum touch height, zero drop shadow.
- **Secondary / Outlined Button:** Transparent fill, crisp 1px border (`#e2e8f0`), `#1e293b` text. On hover: subtle `#f1f5f9` surface fill.
- **Destructive:** Soft tinted background (`#fef2f2`), `#b91c1c` text, 1px border (`#fecaca`).

### Segmented Controls & Pills
- Segmented pill track housed inside an enclosed `#f1f5f9` recess.
- Active toggle uses a crisp `#ffffff` pill indicator with a 1px border (`#e2e8f0`) and dark text, creating tactile mechanical feedback.
- Category filters use quiet outlined pills that fill with deep slate or botanical green only when active.

### Cards & Data Panels
- Flat white surface `#ffffff` encased in a single 1px hairline border (`#e2e8f0`).
- Header sections are neatly delineated by soft bottom dividers (`#f1f5f9`).
- Key performance metrics are paired with JetBrains Mono numbers, with percentage deltas framed in soft botanical badges (`#dcfce7` surface, `#15803d` text).

### Form Inputs
- 44px height with a solid `#ffffff` fill, framed by a 1px `#cbd5e1` outline.
- Active focus state swaps the gray stroke to an exact 1.5px `#15803d` ring without outer glow spread.
- Floating helper text and labels utilize `JetBrains Mono` at `label-sm` for an uncluttered technical appearance.

### Selection Controls (Checkboxes & Radios)
- Checkboxes: 18px squares with 4px border radius. In checked states, solid `#15803d` fill with crisp white vector tick.
- Radio buttons: 18px circle, filled with an interior 8px `#15803d` bullseye upon selection.