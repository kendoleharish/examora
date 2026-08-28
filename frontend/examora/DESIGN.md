---
name: EXAMORA
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
  on-surface-variant: '#424656'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#51596f'
  on-tertiary: '#ffffff'
  tertiary-container: '#697188'
  on-tertiary-container: '#f7f7ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
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
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  card-gap: 24px
  section-margin: 48px
---

## Brand & Style
The design system for this premium online examination platform is built upon a **Corporate Modern** aesthetic with a strong emphasis on **Minimalism** and precision. It targets educational institutions and enterprise certification bodies that require a high-trust, distraction-free environment. 

The UI should evoke a sense of clarity, authority, and calm. By utilizing heavy whitespace and a restricted color palette, the interface reduces cognitive load for students during high-stakes testing while providing administrators with a sophisticated, data-rich dashboard. Visual interest is generated through precise alignment, generous breathing room, and premium micro-interactions rather than decorative elements.

## Colors
The color strategy employs a high-contrast primary blue for action-oriented elements and brand recognition. 

- **Primary (#0066FF):** Used for primary buttons, active states, and critical progress indicators.
- **Secondary Slate (#64748B):** Reserved for secondary text, icons, and non-interactive data visualizations to provide a professional, grounded feel.
- **Surface & Background:** The main application background uses a very light neutral tint (`#F8FAFC`) to differentiate from the pure white (`#FFFFFF`) used for elevated cards and content containers.
- **Functional Colors:** Success Green and Error Red are used sparingly and with low saturation for status badges, ensuring they do not distract from the primary task unless necessary.

## Typography
The system uses **Inter** for all primary reading and interface elements due to its exceptional legibility and neutral character. **Geist** is introduced for labels and technical data to provide a subtle "pro-tool" feel in the dashboard environment.

- **Headlines:** Use tighter letter spacing and heavier weights to establish clear sections.
- **Body Text:** Standard weight for maximum readability. 
- **Labels:** Uppercase Geist is used for table headers, metadata, and category labels to distinguish them from actionable content.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid Grid**. The sidebar remains fixed at 280px, while the main content area utilizes a 12-column fluid grid.

- **Rhythm:** A strict 8px base unit governs all dimensions.
- **Dashboard Metrics:** Performance cards (e.g., Average Score, Exams Completed) should be arranged in a flexible grid that collapses from 4 columns on desktop to 2 columns on tablet and 1 on mobile.
- **Safe Areas:** A minimum 32px container padding is required for all desktop views to maintain a "premium" airy feel.
- **Reflow:** On mobile, sidebars transition to a bottom navigation bar or a hidden hamburger menu to maximize screen real estate for exam content.

## Elevation & Depth
This design system utilizes **Tonal Layering** combined with **Ambient Shadows** to create a sense of organized depth without visual clutter.

- **Level 0 (Background):** Neutral Slate (`#F8FAFC`). No shadow.
- **Level 1 (Cards/Containers):** Pure White (`#FFFFFF`). A very soft, highly diffused shadow (0px 4px 20px rgba(0, 0, 0, 0.05)) is used to lift content off the background.
- **Level 2 (Modals/Dropdowns):** Elevated White. A more pronounced shadow with a wider spread (0px 10px 30px rgba(0, 0, 0, 0.1)) to indicate temporary interaction layers.
- **Outlines:** Subtle 1px borders in `#E2E8F0` are used on all cards to maintain definition even if the shadow is not visible on certain displays.

## Shapes
The shape language is defined as **Rounded**, leaning towards a modern SaaS aesthetic.

- **Standard Elements:** Buttons and input fields use a `0.5rem` (8px) radius.
- **Large Containers:** Dashboard cards and modal windows use `1rem` (16px) radius to soften the professional look and feel more approachable.
- **Badges:** Performance metrics and status chips use a full pill-shape (999px) to contrast against the more structured rectangular cards.

## Components

### Buttons
- **Primary:** Solid `#0066FF` with white text. High-contrast, 16px horizontal padding.
- **Secondary:** Transparent background with `#0066FF` border and text.
- **Micro-interaction:** On hover, primary buttons should scale by 1.02x using a spring physics transition (`stiffness: 400, damping: 25`).

### Metrics Cards
- Used for "Exams Completed" or "Average Score".
- Must include a subtle trend indicator (e.g., +2% from last month) in functional Success/Error colors.
- Backgrounds are always White (`#FFFFFF`) with a 16px corner radius.

### Input Fields
- Understated style: 1px Slate border (`#CBD5E1`) that transforms to 2px Primary Blue on focus.
- Floating labels or clear top-aligned labels in `label-md` style.

### Lists & Tables
- **Staggered Entrance:** List items (Student Performance, Question Bank) should fade in and slide up (20px) with a 50ms delay between each row.
- **Hover State:** Rows should highlight with a subtle `#F1F5F9` background change.

### Question Bank Component
- A specialized card containing tags for "Subject", "Difficulty", and "Last Modified".
- Includes a quick-action hover menu for Edit, Preview, and Delete.