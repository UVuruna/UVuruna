# DESIGN.md — UVuruna Design System

Universal UI design system for **all** UVuruna projects — desktop (PySide6/Qt)
and web (HTML/CSS/JS). Required reading before building or redesigning ANY GUI
(root CLAUDE.md, Rule #16).

**How this file works:**
- Read it FIRST — it exists so we do NOT re-research the internet for every project.
- If it does not cover your stack, or the *Last researched* date is over a year old,
  launch a web-research agent (cheapest capable tier, Rule #15) and **fold the
  findings back in here**.
- Projects may define their own theme (own hues, own personality) ON TOP of this
  system — the quality bar itself is non-negotiable.

**Last researched:** 2026-07-18

---

## Table of Contents

- [Design Language](#design-language)
- [Color](#color)
- [Depth & Effects](#depth-effects)
- [Shape & Spacing](#shape-spacing)
- [Typography](#typography)
- [Iconography & Emoji](#iconography)
- [Data Visualization](#data-visualization)
- [Forbidden — What Reads as Dated](#forbidden)
- [PySide6 / Qt Recipes](#qt-recipes)
- [Web Recipes](#web-recipes)

---

<a id="design-language"></a>

## Design Language

The UVuruna baseline is **dark-first, soft depth, one strong accent**:

- **Dark-first** — dark is the default, not an alternate mode. Base surfaces are
  charcoal / deep navy, never pure black. "Comfort, not drama."
- **Soft depth** — elevation via soft ambient shadows and subtle glow, never
  beveled 3D or hard-edged drop shadows.
- **Glass accents** — frosted semi-transparent panels (glassmorphism) for chrome:
  title bars, side panels, overlays. Used sparingly; body content stays opaque.
- **Bento grids** — dashboards are modular card clusters of varying sizes.
- **Flat minimalism underneath** — dense data views fall back to clean flat
  surfaces with a single accent; the effects above decorate, they never carry.

---

<a id="color"></a>

## Color

All values are TOKENS — they live in the project's config/theme file
(root Rule #4), never as literals in component code.

### Dark surfaces (elevation steps lighter, never flat gray)

| Token | Value | Use |
|-------|-------|-----|
| `surface-0` | `#121212`–`#1A1A1A` (brand-tinted navy `#0A0A2E` allowed) | window / page background |
| `surface-1` | `#1E1E1E` | cards, panels |
| `surface-2` | `#242424` | raised elements, popovers |
| `surface-3` | `#2A2A2A` | highest elevation |
| `border` | white @ 8–15% opacity | dividers, card edges — never a solid gray line |
| `text-primary` | `#F5F5F5` | body text — pure `#FFFFFF` glares |
| `text-secondary` | `#A0A0A0`–`#B3B3B3` | captions, labels |

### Accent

**ONE primary interactive hue per app** (indigo / cyan / gold family), used for
buttons, focus, active states, highlighted data. Multiple saturated accents at
equal weight = visual noise.

### Semantic (target WCAG AA, 4.5:1 on surface)

| Meaning | Value |
|---------|-------|
| Success | `#22C55E` |
| Warning | `#F59E0B` |
| Error | `#EF4444` |
| Info | `#3B82F6` |

### Gradients

- ✅ Subtle same-hue 2-stop linear gradients (depth on flat surfaces)
- ✅ Organic mesh gradients for web hero/backgrounds (sparingly — they date fast)
- ❌ Glossy high-saturation "Web 2.0" button gradients with specular highlight

---

<a id="depth-effects"></a>

## Depth & Effects

| Effect | Parameters |
|--------|-----------|
| **Shadow** | blur 20–40px, opacity 15–25%, offset (0, 4–8px), dark-tinted (not flat black). Two layers (tight short + soft long) beat one heavy shadow. |
| **Glow** | accent-colored, opacity 10–20%, blur 20–30px — focus rings, active states, highlighted data points |
| **Glass** | background blur 20–40px, panel fill 60–80% opacity, 1px edge border white @ 10–20% |

❌ Never: high-opacity hard shadows, beveled inset/outset borders, default
"Photoshop drop shadow" settings.

---

<a id="shape-spacing"></a>

## Shape & Spacing

### Corner radius (scaled per component, not one global value)

| Component | Radius |
|-----------|--------|
| Buttons, inputs, small controls | 6–10px |
| Cards, panels | 12–16px |
| Modals, large containers | 16–24px |
| Pills, avatars | full round (`999px`) |

Nesting rule of thumb: **inner radius = outer radius − padding**.

### Spacing — 8pt grid

Base unit 8px: `4 (micro) · 8 · 16 · 24 · 32 · 48 · 64+`.
4px only for icon-to-label micro-gaps. Always named tokens
(`space-xs/s/m/l/xl`), never raw pixel literals (Rule #4).

---

<a id="typography"></a>

## Typography

Free, embeddable (desktop bundling + web `@font-face`):

- **Inter** — the default UI typeface (OFL, variable, built for small-size legibility)
- **Geist / Geist Mono** — alternative for dense dashboards; the Mono for numeric columns
- **JetBrains Mono / IBM Plex Mono** — alternates for tabular/numeric data

Hierarchy: H1 28–32px/700 · H2 20–24px/600 · body 14–16px/400–500 ·
labels 12–13px/500. No thin weights (100–300) below 16px. Numeric/data columns
always get a monospace with tabular figures.

❌ Never ship system defaults (Arial/Tahoma/Segoe fallback look) as the primary
UI typeface.

---

<a id="iconography"></a>

## Iconography & Emoji

**SVG icons:** stroke-based, consistent 1.5–2px stroke, 24×24 grid,
single-color via `currentColor`/theme token so they re-tint with the theme.
ONE icon family per app — never mix styles.

Recommended free sets: **Lucide** (default), **Tabler** (dashboards),
**Phosphor** (when multiple weights are needed).

**Emoji policy:** emoji are welcome for informal indicators, empty states,
status flags, docs and changelogs — they are NOT a substitute for the icon set
inside toolbars, buttons or dense data UI (the weight/style mismatch reads
cheap). If a control row uses SVG icons, it uses ONLY SVG icons.

---

<a id="data-visualization"></a>

## Data Visualization

- Gridlines: none, or 5–10% opacity
- Marks: flat solid colors — no 3D extrusion, no glossy gradients on bars/slices
- Max 5–7 categorical colors; overflow grouped into neutral "Other"
- Ordered data: perceptually-uniform sequential/diverging scales — never rainbow
- Neutral base + 1–2 accents reserved for the highlight
- Animation: subtle entrance only (fade/grow on load), no continuous motion
- Prefer direct labeling over legends where space allows

---

<a id="forbidden"></a>

## Forbidden — What Reads as Dated

- Default unstyled OS/Qt widget gray (`palette(window)` untouched)
- Sharp 0px corners on cards and buttons
- Beveled inset/outset 3D buttons (Win95/XP era)
- Heavy hard-edged black drop shadows
- Glossy Web 2.0 gradient buttons
- Skeuomorphic textures (leather, wood, brushed metal)
- Full-page neumorphism (accessibility failure)
- 3D / rainbow pie charts
- Pure `#000000` surface with pure `#FFFFFF` text
- System default fonts as the primary typeface
- Emoji standing in for a proper icon set in professional tools
- Autoplaying carousels, marquee text

---

<a id="qt-recipes"></a>

## PySide6 / Qt Recipes

QSS is a **CSS2-level subset**. It CAN do: colors, borders, `border-radius`,
padding/margin, `qlineargradient`/`qradialgradient`, pseudo-states
(`:hover`, `:pressed`, `:disabled`, `:checked`), fonts, per-object-name theming.
It CANNOT do: `box-shadow`, blur, transitions, `text-shadow`.

### Base pattern — flat QSS + effects on top

```css
/* theme.qss — tokens injected from the project's theme config */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {accent}, stop:1 {accent-dark});
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    color: {text-primary};
}
QPushButton:hover  { background: {accent-light}; }
QPushButton:pressed { background: {accent-dark}; }
```

### Shadows & glow — `QGraphicsDropShadowEffect`

Qt's defaults (blur 1, offset (8,8), harsh gray) ARE the dated look — always
override toward the modern parameters:

```python
shadow = QGraphicsDropShadowEffect(card)
shadow.setBlurRadius(24)            # 20-30
shadow.setOffset(0, 6)              # (0, 4-8)
shadow.setColor(QColor(0, 0, 0, 50))  # ~20% opacity, tinted
card.setGraphicsEffect(shadow)
```

Glow = same effect, accent color at 10–20% alpha, offset (0, 0).

### Glass / frameless chrome

- Rounded outer chrome: frameless window + `Qt.WA_TranslucentBackground`,
  paint the rounded body yourself (`QPainter` + `QPainterPath`)
- True OS blur (Acrylic/Mica on Win 10/11): `PySideSix-Frameless-Window`
  library — the closest thing to real glassmorphism in Qt
- Cheap fake: translucent fill without blur — flatter, zero GPU cost

### Animation

QSS has no transitions — use `QPropertyAnimation` on geometry / opacity /
color properties alongside static QSS state styling.

---

<a id="web-recipes"></a>

## Web Recipes

### Tokens as CSS custom properties

```css
:root {
    --surface-0: #121212;
    --surface-1: #1e1e1e;
    --border: rgb(255 255 255 / 0.10);
    --text-primary: #f5f5f5;
    --text-secondary: #a8a8a8;
    --accent: /* per-project */;
    --radius-control: 8px;
    --radius-card: 14px;
    --shadow-card: 0 6px 24px rgb(0 0 0 / 0.20);
}
```

### Glass panel

```css
.glass {
    background: rgb(30 30 30 / 0.70);
    backdrop-filter: blur(24px);
    border: 1px solid rgb(255 255 255 / 0.12);
    border-radius: var(--radius-card);
}
```

### Depth & interaction

- Cards: `box-shadow: var(--shadow-card)`; hover lifts with a slightly longer,
  softer shadow + `transform: translateY(-2px)`
- Focus: accent-colored glow ring (`box-shadow: 0 0 0 3px` accent @ 20%)
- Transitions: 150–250ms `ease-out` on hover/focus states only
