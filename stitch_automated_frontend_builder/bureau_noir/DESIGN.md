---
name: Bureau Noir
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#cac6bc'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#949087'
  outline-variant: '#49473f'
  surface-tint: '#cbc6bb'
  primary: '#ffffff'
  on-primary: '#323028'
  primary-container: '#e7e2d6'
  on-primary-container: '#67645b'
  inverse-primary: '#615e55'
  secondary: '#ffb4ab'
  on-secondary: '#630f0e'
  secondary-container: '#822621'
  on-secondary-container: '#ff998f'
  tertiary: '#ffffff'
  on-tertiary: '#332f34'
  tertiary-container: '#e8e0e7'
  on-tertiary-container: '#686369'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e7e2d6'
  primary-fixed-dim: '#cbc6bb'
  on-primary-fixed: '#1d1c14'
  on-primary-fixed-variant: '#49473e'
  secondary-fixed: '#ffdad6'
  secondary-fixed-dim: '#ffb4ab'
  on-secondary-fixed: '#410002'
  on-secondary-fixed-variant: '#822621'
  tertiary-fixed: '#e8e0e7'
  tertiary-fixed-dim: '#ccc4cb'
  on-tertiary-fixed: '#1e1a1f'
  on-tertiary-fixed-variant: '#4a454b'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
  ink-red: '#8F302A'
  paper-aged: '#E9E4D8'
  lead-charcoal: '#101010'
  carbon-gray: '#171717'
  typewriter-ribbon: '#34332F'
  verification-green: '#55785A'
typography:
  display-lg:
    fontFamily: Special Elite
    fontSize: 84px
    fontWeight: '400'
    lineHeight: '1.0'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Special Elite
    fontSize: 40px
    fontWeight: '400'
    lineHeight: '1.1'
  headline-lg-mobile:
    fontFamily: Special Elite
    fontSize: 32px
    fontWeight: '400'
    lineHeight: '1.1'
  stamp-lg:
    fontFamily: Special Elite
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.2'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  technical-sm:
    fontFamily: DM Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
    letterSpacing: 0.05em
  metadata-xs:
    fontFamily: DM Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.1em
  label-caps:
    fontFamily: DM Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: 0.15em
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 20px
  margin-desktop: 48px
  container-max: 1200px
---

## Brand & Style

This design system establishes a **Forensic Archival** aesthetic, positioning the product as a clinical, authoritative tool for deep investigation. The visual narrative mimics the experience of examining high-stakes physical evidence under cold, industrial lighting. It is a "Bureaucratic Noir" style that blends mid-century intelligence agency aesthetics with modern digital precision.

The emotional response should be one of serious scrutiny and intellectual rigor. We achieve this through:
- **Brutalist Structuralism:** Rigid grids, sharp corners, and heavy horizontal dividers that evoke filing cabinets and evidence logs.
- **Physical Skeuomorphism:** Digital surfaces are treated as "paper" or "folders" with subtle grain textures, "stamped" ink marks, and line-numbering systems.
- **Data-First Utility:** A focus on monospaced data, metadata eyebrows, and technical "scanline" indicators that prioritize information over decoration.

## Colors

The palette is strictly desaturated to maintain an archival tone. The primary interaction comes from the contrast between **Lead Charcoal** (#101010) backgrounds and **Aged Paper** (#E9E4D8) surfaces.

- **Lead Charcoal & Carbon Gray:** Used for the "desk" (background) and UI containers to provide a deep, high-contrast base.
- **Aged Paper:** Used for primary document areas and "evidence" containers to create a physical focal point.
- **Ink Red:** Reserved for high-impact status marks, "stamped" alerts, and primary call-to-actions. It should feel like physical rubber-stamp ink.
- **Verification Green:** Used sparingly for "Reliable" or "Supported" technical statuses.

## Typography

The typographic system uses a functional three-tier hierarchy to separate mechanical, technical, and human-readable content.

1.  **Mechanical (Special Elite):** Used for headings and "stamped" status marks. It conveys a typewriter's tactile history. Use `stamp-lg` with a slight rotation (-3 to -7 degrees) for authenticity.
2.  **Technical (DM Mono):** Used for all system data, case IDs, line numbers, and labels. This font represents the "forensic" layer of the UI.
3.  **Human (Inter):** Used for long-form body copy and interactive UI controls. This ensures high readability against the more expressive mechanical fonts.

**Text Treatments:**
- Line numbers must accompany all primary text areas in `technical-sm`.
- Eyebrow labels should always use `metadata-xs` with increased letter spacing.

## Layout & Spacing

The layout philosophy is based on a **Fixed Grid** within a central container, mimicking a case file laid out on a table.

- **Grid:** A 12-column grid system is used for general layout, while document-specific views use a 2-column "Evidence/Metadata" split.
- **Rhythm:** An 8px base unit drives all padding and margins. Use tight 16px gutters to reinforce the bureaucratic density of the design.
- **Breakpoints:**
    - **Mobile (<768px):** Single column. Margins shrink to 20px. "Paper" textures fill the screen width.
    - **Desktop (>1024px):** 1200px max-width. The central container uses a heavy shadow to "float" over the charcoal background.
- **Special Pattern:** Use negative margins (approx. -64px) to allow the primary "Investigation" card to overlap hero sections, creating visual depth.

## Elevation & Depth

Depth is used to distinguish the "Workspace" from the "Archive."

- **Tonal Layering:** The primary background is #101010. Content cards use #171717 (Carbon) to indicate interactive depth.
- **Physical Elevation:** The central "Investigation Paper" is the only element that uses a heavy shadow. Apply a diffused `0px 24px 60px rgba(0,0,0,0.5)` to make it feel physically separate from the digital desk.
- **Overlays:**
    - **Grid Overlay:** A 48px subtle CSS grid pattern (`rgba(255,255,255,0.03)`) should be applied to hero areas.
    - **Scanlines:** A semi-transparent vertical bar with a pulse animation moves across active "analyzing" states to simulate a scanner.
- **No Blurs:** Avoid soft glassmorphism. Surfaces are opaque and solid, like cardboard and thick paper.

## Shapes

The shape language is strictly **Sharp (0px)**. 

Every element—including buttons, cards, input fields, and tags—must have 90-degree corners. This reinforces the brutalist, archival nature of the system. The only exception is the `status-dot` used in list rows, which remains a perfect circle to distinguish it as a "light" or indicator.

**Visual Borders:**
- Use 1px solid lines for dividers.
- Use 3px solid lines for "Ink Stamp" borders to simulate the bleed of a physical stamp.
- Use a `repeating-linear-gradient` to create horizontal "lined paper" backgrounds for large text input areas.

## Components

- **Buttons:** Sharp corners. Primary buttons use a solid **Ink Red** fill with white text. Secondary buttons are ghost-style with 1px **Aged Paper** borders. All text in labels must be `label-caps`.
- **Archival File Rows:** Low-height list items with a 1px bottom border. Include a monospaced "File No." on the left and a "Status Stamp" on the right.
- **Evidence Cards:** Use a top-aligned "Tab" (Evidence Folder style). The card body uses the **Aged Paper** background and includes a grayscale filtered thumbnail.
- **Status Stamps:** Contained within a 3px border, rotated -5 degrees. Use the **Ink Red** color with a subtle noise texture mask to simulate physical ink.
- **Investigation Area:** A large text area with `body-md` Inter text, but featuring `technical-sm` line numbers on the left gutter. Background should have the "Lined Paper" gradient.
- **Input Fields:** No background; bottom-border only (1px). Focus state changes border color to **Ink Red**.
- **Scanline:** A horizontal or vertical bar with a `pulse` animation and high-transparency gradient, used as an overlay during data processing states.