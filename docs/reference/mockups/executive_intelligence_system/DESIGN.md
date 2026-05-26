---
name: Executive Intelligence System
colors:
  surface: '#f7f9ff'
  surface-dim: '#d7dadf'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f4f9'
  surface-container: '#ebeef3'
  surface-container-high: '#e5e8ee'
  surface-container-highest: '#e0e3e8'
  on-surface: '#181c20'
  on-surface-variant: '#5a4042'
  inverse-surface: '#2d3135'
  inverse-on-surface: '#eef1f6'
  outline: '#8e7071'
  outline-variant: '#e2bec0'
  surface-tint: '#b81840'
  primary: '#7a0024'
  on-primary: '#ffffff'
  primary-container: '#a50034'
  on-primary-container: '#ffafb5'
  inverse-primary: '#ffb2b8'
  secondary: '#5a5e6a'
  on-secondary: '#ffffff'
  secondary-container: '#dfe2f1'
  on-secondary-container: '#606471'
  tertiary: '#7b001a'
  on-tertiary: '#ffffff'
  tertiary-container: '#a60026'
  on-tertiary-container: '#ffb0b0'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdadb'
  primary-fixed-dim: '#ffb2b8'
  on-primary-fixed: '#40000f'
  on-primary-fixed-variant: '#91002d'
  secondary-fixed: '#dfe2f1'
  secondary-fixed-dim: '#c3c6d4'
  on-secondary-fixed: '#171b26'
  on-secondary-fixed-variant: '#424752'
  tertiary-fixed: '#ffdad9'
  tertiary-fixed-dim: '#ffb3b3'
  on-tertiary-fixed: '#400009'
  on-tertiary-fixed-variant: '#920021'
  background: '#f7f9ff'
  on-background: '#181c20'
  surface-variant: '#e0e3e8'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
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
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  section-gap: 48px
  container-padding: 32px
  gutter: 24px
  stack-sm: 12px
  stack-md: 20px
---

## Brand & Style
The design system embodies a "Strategic Intelligence" aesthetic—tailored for executive decision-makers at LG. It prioritizes clarity and high-signal data visualization over decorative elements. The visual style is **Minimalist Modern** with a focus on high-end editorial layouts. 

To signal AI-driven capabilities without resorting to clichéd tropes, the system utilizes "Luminous Minimalism." This involves using expansive whitespace, precise typography, and surgical applications of light and shadow to create a sense of depth and focus. The emotional response should be one of calm control, high-stakes reliability, and effortless technological sophistication.

## Colors
The palette is rooted in the heritage of LG Red, treated here as a sophisticated accent rather than a dominant wash.

- **Primary LG Red (#A50034):** Used sparingly for critical CTAs, brand moments, and key data points.
- **Deep Charcoal (#212529):** The anchor for all primary typography, ensuring WCAG AAA readability and an executive "ink on paper" feel.
- **Soft Gray Surfaces (#F8F9FA):** Used for background layering to define workspace boundaries without the harshness of pure white.
- **AI Accents:** Subtle gradients are used exclusively for "Insights." These should transition from a faint LG Red tint to a neutral slate, creating a "shimmer" effect on high-value data containers.

## Typography
The system utilizes **Inter** exclusively to maintain a systematic, utilitarian, yet modern feel. 

- **Scale:** High contrast between display titles and body text to facilitate rapid scanning of sales reports.
- **Hierarchy:** Use `label-sm` in uppercase with slight letter spacing for category headers and table column titles.
- **Weight:** Stick to Regular (400) for long-form data and Semi-Bold (600) for interactive elements. Bold (700) is reserved for Display sizes to ground the page.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. Content is housed in a centered container (max-width: 1440px) to prevent line lengths from becoming unreadable on ultra-wide executive monitors.

- **Grid:** A 12-column grid with generous 24px gutters.
- **Rhythm:** Use a strict 8px baseline grid. Section headers should have a minimum of 48px top-margin to provide visual breathing room.
- **Dashboards:** Utilize a "Bento Box" arrangement where cards vary in span (4, 6, or 8 columns) but maintain consistent vertical gaps.

## Elevation & Depth
Depth is communicated through **Tonal Layering** and **Ambient Shadows**. 

- **Surface Level 0:** Background (#FFFFFF).
- **Surface Level 1:** Secondary containers (#F8F9FA) with no shadow, used for grouping content.
- **Surface Level 2:** Interactive Cards. These use a very soft, diffused shadow: `0 8px 32px rgba(0,0,0,0.04)`.
- **AI Focus Glow:** For containers holding AI-generated strategy, apply a subtle inner glow using the Primary LG Red at 5% opacity and a 1px border of the same color at 10% opacity. This creates a "pulsing" importance without visual noise.

## Shapes
In line with the "Executive-friendly" requirement, the design system uses a **Rounded** language. 

- **Standard Components:** Buttons and inputs use a 0.5rem (8px) radius.
- **Dashboard Cards:** Use `rounded-lg` (16px) or `rounded-xl` (24px) to create a soft, approachable frame for complex data.
- **Status Badges:** Use a fully pill-shaped radius to distinguish them from interactive buttons.

## Components
- **Dashboard Cards:** Elevated with Level 2 shadows. Content should be padded by 32px. Titles are `headline-md` in Deep Charcoal.
- **Data Tables:** Remove all vertical borders. Use 1px soft gray (#E9ECEF) horizontal separators. On hover, the entire row should transition to a subtle LG Red tint (2% opacity).
- **AI-Insight Containers:** These feature a 1px border with a gradient transition from LG Red to Slate. The background uses the "AI Glow" variables.
- **Status Badges:** Soft backgrounds (e.g., a "Positive" badge uses a soft emerald background with dark emerald text). Avoid high-saturation backgrounds to maintain the minimalist aesthetic.
- **Buttons:** 
    - **Primary:** Solid LG Red with white text.
    - **Secondary:** Transparent with a 1px Charcoal border.
    - **Ghost:** No border, Charcoal text, 8px padding.
- **Input Fields:** Minimalist style. 1px light gray border that transitions to Primary Red on focus. Labels are always `label-md` placed above the field.