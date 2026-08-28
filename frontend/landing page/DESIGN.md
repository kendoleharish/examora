---
name: Examora Institutional
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fd'
  surface-container: '#ededf8'
  surface-container-high: '#e7e7f2'
  surface-container-highest: '#e1e2ec'
  on-surface: '#191b23'
  on-surface-variant: '#434654'
  inverse-surface: '#2e3038'
  inverse-on-surface: '#f0f0fb'
  outline: '#737685'
  outline-variant: '#c3c6d6'
  surface-tint: '#1155d0'
  primary: '#003b9a'
  on-primary: '#ffffff'
  primary-container: '#0050cb'
  on-primary-container: '#c1cfff'
  inverse-primary: '#b3c5ff'
  secondary: '#5b5e6c'
  on-secondary: '#ffffff'
  secondary-container: '#e0e1f3'
  on-secondary-container: '#616473'
  tertiary: '#7b2400'
  on-tertiary: '#ffffff'
  tertiary-container: '#a23302'
  on-tertiary-container: '#ffc3b0'
  error: '#f87171'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#e0e1f3'
  secondary-fixed-dim: '#c3c5d7'
  on-secondary-fixed: '#181b27'
  on-secondary-fixed-variant: '#434654'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59c'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832700'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e1e2ec'
  light-bg: '#faf8ff'
  light-surface: '#ffffff'
  light-border: '#e2e8f0'
  dark-bg: '#0b0e14'
  dark-surface: '#11151d'
  dark-surface-elevated: '#171c26'
  dark-border: '#2a3140'
  dark-accent: '#4f8cff'
  success: '#34d399'
  warning: '#fbbf24'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 58px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  mono-technical:
    fontFamily: Courier Prime
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  max-width: 1280px
---

## Brand & Style

The design system embodies **Institutional Modernism**, a style that balances high-stakes security with effortless accessibility. The brand personality is authoritative yet approachable—think of a digital proctor that is both rigorous and helpful. 

The aesthetic is characterized by a "Secure Standard": clean layouts, structured information density, and a meticulous attention to alignment. It utilizes **Corporate Modernism**—eschewing unnecessary decoration in favor of clarity—while incorporating **Technical Accents** like monospace identifiers and subtle pulsing status indicators to signal real-time system integrity. The goal is to evoke a sense of calm, focused professionalism for both administrators and examinees.

## Colors

The system employs a adaptive color architecture that responds to the `examora-theme` key or system preferences.

### Light Mode (Institutional)
Rooted in clinical clarity. The background (`#faf8ff`) and surface (`#ffffff`) create a high-contrast environment. The primary brand blue (`#0050cb`) drives the hierarchy for actions and critical navigation.

### Dark Mode (Nocturnal)
Designed for reduced eye strain during long-form examinations. It uses a deep charcoal foundation (`#0b0e14`) with tiered surfaces to create depth. The accent blue is shifted to a more luminous, accessible tone (`#4f8cff`) to maintain high contrast against dark backgrounds.

### Semantic State
Semantic colors (Success, Warning, Error) are consistent across both modes but calibrated for vibrance to ensure critical alerts are never missed. Use these for validation, live session statuses, and encryption health.

## Typography

**Inter** is the backbone of the system, selected for its exceptional legibility in technical contexts.

- **Scale:** Large display styles use tighter letter-spacing to appear more compact and authoritative. 
- **Readability:** Body text uses a generous 1.5x line height to support sustained reading during exams.
- **Technical Identity:** Use the `mono-technical` style for IDs, hashes, and session tokens to signal machine-verified data. 
- **Responsiveness:** Transition from `headline-lg` to `headline-lg-mobile` at the tablet breakpoint to maintain vertical rhythm without overwhelming the viewport.

## Layout & Spacing

This design system utilizes a **Fixed Grid** model for administrative dashboards and a fluid approach for examination interfaces.

- **Desktop:** 12-column grid within a 1280px container. Use 40px outer margins and 24px gutters to allow the content "room to breathe," which reduces cognitive load.
- **Mobile:** 16px margins with a single-column stack. 
- **Rhythm:** All spacing must be a multiple of the 8px base unit. Component internal padding should default to `lg` (24px) for cards and `md` (16px) for compact lists.
- **Vertical Flow:** Use `2xl` (48px) spacing between major sections to maintain a clear visual hierarchy of content blocks.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and subtle contrast rather than aggressive shadows.

- **Light Mode:** Uses "Ghost Borders" (`#e2e8f0`) to define containers. Elevation is reserved for floating elements (modals, dropdowns) using a very soft, diffused shadow: `0 12px 40px -12px rgba(0,0,0,0.1)`.
- **Dark Mode:** Depth is conveyed via surface tinting. The base background is the darkest layer (`#0b0e14`), while cards and inputs use `#11151d`. Floating elements or active states use the Elevated Surface (`#171c26`).
- **Transparency:** The global header employs a `backdrop-blur-xl` at 80% opacity to maintain environmental context.
- **Interactive Depth:** Buttons use a localized tinted shadow in light mode (e.g., a blue glow for primary buttons) to emphasize clickability.

## Shapes

The shape language follows a dual-radius logic to differentiate between "Structure" and "Action."

- **Structure (Cards, Modals):** Use `rounded-xl` (1.5rem) to provide a modern, premium feel to large content containers.
- **Action (Buttons, Inputs):** Use `rounded-lg` (1rem) for standard interactive elements, providing a sturdy and reliable appearance.
- **Status (Badges, Toggles):** Use "Pill" (full) rounding for small status indicators and mode switches to distinguish them from functional inputs.

## Components

- **Buttons:** 
  - *Primary:* Institutional Blue background, white text. In Dark Mode, use Accessible Academic Blue. 8px radius.
  - *Secondary:* Outline style using the mode-specific border color and accent text.
- **Input Fields:** 
  - 8px radius. Background matches the surface tier (White in light, `#11151d` in dark). 
  - Focus state: 2px solid primary/accent color with a soft outer glow.
- **Cards:** 
  - Surface background with a 1px border. 
  - Headers within cards should be separated by a 1px horizontal divider to organize meta-data (e.g., "Exam Time Remaining") from content.
- **Chips/Badges:** 
  - Use semantic colors for backgrounds at 15% opacity with 100% opacity text for high readability and a "glass" technical look.
- **Lists:** 
  - Interactive list items should have a hover state that shifts the background color by one tonal tier (e.g., `surface` to `surface-elevated`).