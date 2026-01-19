# Liftoff Theming Guide

> Catppuccin-based theming system for consistent, accessible, and beautiful UI.

---

## Table of Contents

1. [Overview](#overview)
2. [Catppuccin Palette](#catppuccin-palette)
3. [Theme Architecture](#theme-architecture)
4. [Implementation](#implementation)
5. [Configuration](#configuration)
6. [Component Guidelines](#component-guidelines)
7. [Accessibility](#accessibility)
8. [Extending Themes](#extending-themes)

---

## Overview

Liftoff uses the [Catppuccin](https://catppuccin.com/) color palette exclusively for all UI elements. No hardcoded colors are permitted in CSS, templates, or components.

### Design Principles

1. **No hardcoded colors** — All colors reference CSS custom properties or Tailwind theme tokens
2. **Semantic naming** — Colors are named by purpose, not appearance (e.g., `--color-surface`, not `--color-gray`)
3. **Consistent contrast** — All text meets WCAG 2.1 AA standards (4.5:1 for normal text, 3:1 for large text)
4. **Dark-first** — Frappé is the default; light theme (Latte) is fully supported
5. **User preference** — Respects system preference, allows user override

### Available Themes

| Theme | Description | Use Case |
|-------|-------------|----------|
| **Latte** | Light theme with warm tones | Bright environments, accessibility preference |
| **Frappé** | Medium dark with muted tones | **Default** — balanced, easy on eyes |
| **Macchiato** | Darker with subtle warmth | Preference for darker UI |
| **Mocha** | Darkest with rich tones | Low-light environments, OLED screens |

---

## Catppuccin Palette

### Frappé (Default)

The base palette for Liftoff. All examples in this document use Frappé values.

#### Base Colors

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| `rosewater` | `#f2d5cf` | `242, 213, 207` | Links, subtle highlights |
| `flamingo` | `#eebebe` | `238, 190, 190` | Secondary accents |
| `pink` | `#f4b8e4` | `244, 184, 228` | Attention, badges |
| `mauve` | `#ca9ee6` | `202, 158, 230` | **Primary accent** |
| `red` | `#e78284` | `231, 130, 132` | Errors, destructive actions |
| `maroon` | `#ea999c` | `234, 153, 156` | Warnings (alt) |
| `peach` | `#ef9f76` | `239, 159, 118` | Warnings |
| `yellow` | `#e5c890` | `229, 200, 144` | Caution, highlights |
| `green` | `#a6d189` | `166, 209, 137` | Success, positive |
| `teal` | `#81c8be` | `129, 200, 190` | Info, secondary actions |
| `sky` | `#99d1db` | `153, 209, 219` | Info (alt) |
| `sapphire` | `#85c1dc` | `133, 193, 220` | Links (alt) |
| `blue` | `#8caaee` | `140, 170, 238` | Interactive elements |
| `lavender` | `#babbf1` | `186, 187, 241` | Focus rings, selections |

#### Surface Colors

| Name | Hex | RGB | Role |
|------|-----|-----|------|
| `text` | `#c6d0f5` | `198, 208, 245` | Primary text |
| `subtext1` | `#b5bfe2` | `181, 191, 226` | Secondary text |
| `subtext0` | `#a5adce` | `165, 173, 206` | Muted text, placeholders |
| `overlay2` | `#949cbb` | `148, 156, 187` | Disabled text |
| `overlay1` | `#838ba7` | `131, 139, 167` | Subtle borders |
| `overlay0` | `#737994` | `115, 121, 148` | Borders |
| `surface2` | `#626880` | `98, 104, 128` | Elevated surfaces, hover |
| `surface1` | `#51576d` | `81, 87, 109` | Cards, panels |
| `surface0` | `#414559` | `65, 69, 89` | Input backgrounds |
| `base` | `#303446` | `48, 52, 70` | **Main background** |
| `mantle` | `#292c3c` | `41, 44, 60` | Sidebars, secondary bg |
| `crust` | `#232634` | `35, 38, 52` | Deepest background |

### All Palettes Reference

<details>
<summary><strong>Latte (Light Theme)</strong></summary>

| Name | Hex | Role |
|------|-----|------|
| `rosewater` | `#dc8a78` | Links, subtle highlights |
| `flamingo` | `#dd7878` | Secondary accents |
| `pink` | `#ea76cb` | Attention, badges |
| `mauve` | `#8839ef` | **Primary accent** |
| `red` | `#d20f39` | Errors, destructive |
| `maroon` | `#e64553` | Warnings (alt) |
| `peach` | `#fe640b` | Warnings |
| `yellow` | `#df8e1d` | Caution, highlights |
| `green` | `#40a02b` | Success, positive |
| `teal` | `#179299` | Info, secondary |
| `sky` | `#04a5e5` | Info (alt) |
| `sapphire` | `#209fb5` | Links (alt) |
| `blue` | `#1e66f5` | Interactive |
| `lavender` | `#7287fd` | Focus, selections |
| `text` | `#4c4f69` | Primary text |
| `subtext1` | `#5c5f77` | Secondary text |
| `subtext0` | `#6c6f85` | Muted text |
| `overlay2` | `#7c7f93` | Disabled text |
| `overlay1` | `#8c8fa1` | Subtle borders |
| `overlay0` | `#9ca0b0` | Borders |
| `surface2` | `#acb0be` | Elevated surfaces |
| `surface1` | `#bcc0cc` | Cards, panels |
| `surface0` | `#ccd0da` | Input backgrounds |
| `base` | `#eff1f5` | **Main background** |
| `mantle` | `#e6e9ef` | Sidebars |
| `crust` | `#dce0e8` | Deepest background |

</details>

<details>
<summary><strong>Macchiato</strong></summary>

| Name | Hex | Role |
|------|-----|------|
| `rosewater` | `#f4dbd6` | Links, subtle highlights |
| `flamingo` | `#f0c6c6` | Secondary accents |
| `pink` | `#f5bde6` | Attention, badges |
| `mauve` | `#c6a0f6` | **Primary accent** |
| `red` | `#ed8796` | Errors, destructive |
| `maroon` | `#ee99a0` | Warnings (alt) |
| `peach` | `#f5a97f` | Warnings |
| `yellow` | `#eed49f` | Caution, highlights |
| `green` | `#a6da95` | Success, positive |
| `teal` | `#8bd5ca` | Info, secondary |
| `sky` | `#91d7e3` | Info (alt) |
| `sapphire` | `#7dc4e4` | Links (alt) |
| `blue` | `#8aadf4` | Interactive |
| `lavender` | `#b7bdf8` | Focus, selections |
| `text` | `#cad3f5` | Primary text |
| `subtext1` | `#b8c0e0` | Secondary text |
| `subtext0` | `#a5adcb` | Muted text |
| `overlay2` | `#939ab7` | Disabled text |
| `overlay1` | `#8087a2` | Subtle borders |
| `overlay0` | `#6e738d` | Borders |
| `surface2` | `#5b6078` | Elevated surfaces |
| `surface1` | `#494d64` | Cards, panels |
| `surface0` | `#363a4f` | Input backgrounds |
| `base` | `#24273a` | **Main background** |
| `mantle` | `#1e2030` | Sidebars |
| `crust` | `#181926` | Deepest background |

</details>

<details>
<summary><strong>Mocha (Darkest)</strong></summary>

| Name | Hex | Role |
|------|-----|------|
| `rosewater` | `#f5e0dc` | Links, subtle highlights |
| `flamingo` | `#f2cdcd` | Secondary accents |
| `pink` | `#f5c2e7` | Attention, badges |
| `mauve` | `#cba6f7` | **Primary accent** |
| `red` | `#f38ba8` | Errors, destructive |
| `maroon` | `#eba0ac` | Warnings (alt) |
| `peach` | `#fab387` | Warnings |
| `yellow` | `#f9e2af` | Caution, highlights |
| `green` | `#a6e3a1` | Success, positive |
| `teal` | `#94e2d5` | Info, secondary |
| `sky` | `#89dceb` | Info (alt) |
| `sapphire` | `#74c7ec` | Links (alt) |
| `blue` | `#89b4fa` | Interactive |
| `lavender` | `#b4befe` | Focus, selections |
| `text` | `#cdd6f4` | Primary text |
| `subtext1` | `#bac2de` | Secondary text |
| `subtext0` | `#a6adc8` | Muted text |
| `overlay2` | `#9399b2` | Disabled text |
| `overlay1` | `#7f849c` | Subtle borders |
| `overlay0` | `#6c7086` | Borders |
| `surface2` | `#585b70` | Elevated surfaces |
| `surface1` | `#45475a` | Cards, panels |
| `surface0` | `#313244` | Input backgrounds |
| `base` | `#1e1e2e` | **Main background** |
| `mantle` | `#181825` | Sidebars |
| `crust` | `#11111b` | Deepest background |

</details>

---

## Theme Architecture

### File Structure

```
src/liftoff/
├── static/
│   └── css/
│       ├── themes/
│       │   ├── _variables.css      # CSS custom properties
│       │   ├── latte.css           # Latte overrides
│       │   ├── frappe.css          # Frappé (default)
│       │   ├── macchiato.css       # Macchiato overrides
│       │   └── mocha.css           # Mocha overrides
│       ├── base.css                # Reset + base styles
│       ├── components.css          # Component styles
│       └── utilities.css           # Utility classes
├── core/
│   └── theme.py                    # Theme configuration
└── templates/
    └── base.html                   # Theme class application
```

### CSS Custom Properties

All colors are defined as CSS custom properties in `:root` and overridden per theme.

```css
/* static/css/themes/_variables.css */

/* Semantic color mappings - these are what components use */
:root {
  /* === Primary palette === */
  --color-primary: var(--ctp-mauve);
  --color-primary-hover: var(--ctp-lavender);
  --color-secondary: var(--ctp-teal);

  /* === Semantic colors === */
  --color-success: var(--ctp-green);
  --color-warning: var(--ctp-peach);
  --color-error: var(--ctp-red);
  --color-info: var(--ctp-blue);

  /* === Text colors === */
  --color-text: var(--ctp-text);
  --color-text-secondary: var(--ctp-subtext1);
  --color-text-muted: var(--ctp-subtext0);
  --color-text-disabled: var(--ctp-overlay2);

  /* === Surface colors === */
  --color-bg: var(--ctp-base);
  --color-bg-secondary: var(--ctp-mantle);
  --color-bg-tertiary: var(--ctp-crust);
  --color-surface: var(--ctp-surface0);
  --color-surface-hover: var(--ctp-surface1);
  --color-surface-active: var(--ctp-surface2);

  /* === Border colors === */
  --color-border: var(--ctp-overlay0);
  --color-border-subtle: var(--ctp-overlay1);
  --color-border-focus: var(--ctp-lavender);

  /* === Interactive states === */
  --color-link: var(--ctp-rosewater);
  --color-link-hover: var(--ctp-flamingo);
  --color-focus-ring: var(--ctp-lavender);

  /* === Issue type colors === */
  --color-issue-task: var(--ctp-blue);
  --color-issue-bug: var(--ctp-red);
  --color-issue-story: var(--ctp-green);
  --color-issue-epic: var(--ctp-mauve);

  /* === Priority colors === */
  --color-priority-critical: var(--ctp-red);
  --color-priority-high: var(--ctp-peach);
  --color-priority-medium: var(--ctp-yellow);
  --color-priority-low: var(--ctp-blue);
  --color-priority-none: var(--ctp-overlay1);

  /* === Status category colors === */
  --color-status-todo: var(--ctp-overlay1);
  --color-status-inprogress: var(--ctp-blue);
  --color-status-done: var(--ctp-green);

  /* === Spacing (not theme-dependent but defined here for consistency) === */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* === Border radius === */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;

  /* === Shadows (using palette colors) === */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.15);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.2);
}
```

```css
/* static/css/themes/frappe.css - Default theme */

:root,
[data-theme="frappe"] {
  --ctp-rosewater: #f2d5cf;
  --ctp-flamingo: #eebebe;
  --ctp-pink: #f4b8e4;
  --ctp-mauve: #ca9ee6;
  --ctp-red: #e78284;
  --ctp-maroon: #ea999c;
  --ctp-peach: #ef9f76;
  --ctp-yellow: #e5c890;
  --ctp-green: #a6d189;
  --ctp-teal: #81c8be;
  --ctp-sky: #99d1db;
  --ctp-sapphire: #85c1dc;
  --ctp-blue: #8caaee;
  --ctp-lavender: #babbf1;

  --ctp-text: #c6d0f5;
  --ctp-subtext1: #b5bfe2;
  --ctp-subtext0: #a5adce;
  --ctp-overlay2: #949cbb;
  --ctp-overlay1: #838ba7;
  --ctp-overlay0: #737994;
  --ctp-surface2: #626880;
  --ctp-surface1: #51576d;
  --ctp-surface0: #414559;
  --ctp-base: #303446;
  --ctp-mantle: #292c3c;
  --ctp-crust: #232634;

  /* RGB values for alpha compositing */
  --ctp-base-rgb: 48, 52, 70;
  --ctp-text-rgb: 198, 208, 245;
  --ctp-mauve-rgb: 202, 158, 230;
}
```

```css
/* static/css/themes/latte.css - Light theme */

[data-theme="latte"] {
  --ctp-rosewater: #dc8a78;
  --ctp-flamingo: #dd7878;
  --ctp-pink: #ea76cb;
  --ctp-mauve: #8839ef;
  --ctp-red: #d20f39;
  --ctp-maroon: #e64553;
  --ctp-peach: #fe640b;
  --ctp-yellow: #df8e1d;
  --ctp-green: #40a02b;
  --ctp-teal: #179299;
  --ctp-sky: #04a5e5;
  --ctp-sapphire: #209fb5;
  --ctp-blue: #1e66f5;
  --ctp-lavender: #7287fd;

  --ctp-text: #4c4f69;
  --ctp-subtext1: #5c5f77;
  --ctp-subtext0: #6c6f85;
  --ctp-overlay2: #7c7f93;
  --ctp-overlay1: #8c8fa1;
  --ctp-overlay0: #9ca0b0;
  --ctp-surface2: #acb0be;
  --ctp-surface1: #bcc0cc;
  --ctp-surface0: #ccd0da;
  --ctp-base: #eff1f5;
  --ctp-mantle: #e6e9ef;
  --ctp-crust: #dce0e8;

  --ctp-base-rgb: 239, 241, 245;
  --ctp-text-rgb: 76, 79, 105;
  --ctp-mauve-rgb: 136, 57, 239;
}
```

---

## Implementation

### Tailwind CSS Integration

Extend Tailwind to use Catppuccin colors via CSS custom properties.

```javascript
// tailwind.config.js

module.exports = {
  content: [
    './src/liftoff/templates/**/*.html',
    './src/liftoff/static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Catppuccin palette colors (reference CSS vars)
        ctp: {
          rosewater: 'var(--ctp-rosewater)',
          flamingo: 'var(--ctp-flamingo)',
          pink: 'var(--ctp-pink)',
          mauve: 'var(--ctp-mauve)',
          red: 'var(--ctp-red)',
          maroon: 'var(--ctp-maroon)',
          peach: 'var(--ctp-peach)',
          yellow: 'var(--ctp-yellow)',
          green: 'var(--ctp-green)',
          teal: 'var(--ctp-teal)',
          sky: 'var(--ctp-sky)',
          sapphire: 'var(--ctp-sapphire)',
          blue: 'var(--ctp-blue)',
          lavender: 'var(--ctp-lavender)',
          text: 'var(--ctp-text)',
          subtext1: 'var(--ctp-subtext1)',
          subtext0: 'var(--ctp-subtext0)',
          overlay2: 'var(--ctp-overlay2)',
          overlay1: 'var(--ctp-overlay1)',
          overlay0: 'var(--ctp-overlay0)',
          surface2: 'var(--ctp-surface2)',
          surface1: 'var(--ctp-surface1)',
          surface0: 'var(--ctp-surface0)',
          base: 'var(--ctp-base)',
          mantle: 'var(--ctp-mantle)',
          crust: 'var(--ctp-crust)',
        },
        // Semantic colors (use these in components)
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        error: 'var(--color-error)',
        info: 'var(--color-info)',
      },
      backgroundColor: {
        DEFAULT: 'var(--color-bg)',
        secondary: 'var(--color-bg-secondary)',
        tertiary: 'var(--color-bg-tertiary)',
        surface: 'var(--color-surface)',
        'surface-hover': 'var(--color-surface-hover)',
        'surface-active': 'var(--color-surface-active)',
      },
      textColor: {
        DEFAULT: 'var(--color-text)',
        secondary: 'var(--color-text-secondary)',
        muted: 'var(--color-text-muted)',
        disabled: 'var(--color-text-disabled)',
      },
      borderColor: {
        DEFAULT: 'var(--color-border)',
        subtle: 'var(--color-border-subtle)',
        focus: 'var(--color-border-focus)',
      },
      ringColor: {
        focus: 'var(--color-focus-ring)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### Python Theme Configuration

```python
# src/liftoff/core/theme.py

from enum import Enum
from typing import Any
from pydantic import BaseModel


class ThemeName(str, Enum):
    """Available Catppuccin themes."""

    LATTE = "latte"
    FRAPPE = "frappe"
    MACCHIATO = "macchiato"
    MOCHA = "mocha"


class ThemeConfig(BaseModel):
    """Theme configuration."""

    # Default theme for new users
    default_theme: ThemeName = ThemeName.FRAPPE

    # Allow users to override theme
    allow_user_override: bool = True

    # Respect system preference (prefers-color-scheme)
    respect_system_preference: bool = True

    # Map system preference to themes
    system_light_theme: ThemeName = ThemeName.LATTE
    system_dark_theme: ThemeName = ThemeName.FRAPPE

    # Available themes (can be restricted)
    available_themes: list[ThemeName] = [
        ThemeName.LATTE,
        ThemeName.FRAPPE,
        ThemeName.MACCHIATO,
        ThemeName.MOCHA,
    ]


# Default configuration
DEFAULT_THEME_CONFIG = ThemeConfig()


def get_theme_for_user(
    user_preference: ThemeName | None,
    system_preference: str | None,  # "light" or "dark"
    config: ThemeConfig = DEFAULT_THEME_CONFIG,
) -> ThemeName:
    """
    Determine the theme for a user based on preferences.

    Priority:
    1. User explicit preference (if allowed and set)
    2. System preference (if enabled)
    3. Default theme
    """
    # User preference takes priority
    if config.allow_user_override and user_preference is not None:
        if user_preference in config.available_themes:
            return user_preference

    # System preference
    if config.respect_system_preference and system_preference:
        if system_preference == "light":
            return config.system_light_theme
        elif system_preference == "dark":
            return config.system_dark_theme

    # Default
    return config.default_theme


def get_theme_css_class(theme: ThemeName) -> str:
    """Get the CSS data attribute value for a theme."""
    return theme.value
```

### Configuration File

```yaml
# config/liftoff.yaml

# Theme configuration
theme:
  # Default theme for new users and anonymous visitors
  # Options: latte, frappe, macchiato, mocha
  default: frappe

  # Allow users to select their preferred theme
  allow_user_override: true

  # Respect browser/OS prefers-color-scheme setting
  respect_system_preference: true

  # Which theme to use for system "light" preference
  system_light_theme: latte

  # Which theme to use for system "dark" preference
  system_dark_theme: frappe

  # Restrict available themes (empty = all available)
  # Useful for enforcing brand consistency
  available_themes: []
  # available_themes:
  #   - frappe
  #   - mocha
```

### Base Template Integration

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en" data-theme="{{ theme }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="{% if theme == 'latte' %}light{% else %}dark{% endif %}">

    <title>{% block title %}Liftoff{% endblock %}</title>

    <!-- Theme CSS (order matters) -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/themes/_variables.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', path='css/themes/frappe.css') }}">
    {% if theme != 'frappe' %}
    <link rel="stylesheet" href="{{ url_for('static', path='css/themes/' + theme + '.css') }}">
    {% endif %}

    <!-- Base styles -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/base.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', path='css/components.css') }}">

    <!-- Tailwind (compiled) -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/tailwind.css') }}">

    <!-- Theme detection script (runs before render to prevent flash) -->
    <script>
        (function() {
            // Check for saved preference
            const saved = localStorage.getItem('liftoff-theme');
            if (saved && ['latte', 'frappe', 'macchiato', 'mocha'].includes(saved)) {
                document.documentElement.setAttribute('data-theme', saved);
                return;
            }

            // Check system preference
            {% if config.respect_system_preference %}
            if (window.matchMedia('(prefers-color-scheme: light)').matches) {
                document.documentElement.setAttribute('data-theme', '{{ config.system_light_theme }}');
            }
            {% endif %}
        })();
    </script>
</head>
<body class="bg-ctp-base text-ctp-text min-h-screen">
    {% include "partials/_header.html" %}

    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>

    {% include "partials/_footer.html" %}

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <!-- Theme switcher -->
    <script src="{{ url_for('static', path='js/theme.js') }}"></script>
</body>
</html>
```

### Theme Switcher Component

```html
<!-- templates/partials/_theme_switcher.html -->
<div class="relative" x-data="{ open: false }">
    <button
        @click="open = !open"
        class="p-2 rounded-md hover:bg-surface-hover focus:outline-none focus:ring-2 focus:ring-focus"
        aria-label="Change theme"
    >
        <!-- Sun icon for light theme -->
        <svg
            class="w-5 h-5 hidden [data-theme='latte']_&:block"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <!-- Moon icon for dark themes -->
        <svg
            class="w-5 h-5 [data-theme='latte']_&:hidden"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
    </button>

    <div
        x-show="open"
        @click.away="open = false"
        class="absolute right-0 mt-2 w-48 bg-surface rounded-lg shadow-lg border border-default py-1 z-50"
    >
        <button
            onclick="setTheme('latte')"
            class="w-full px-4 py-2 text-left hover:bg-surface-hover flex items-center gap-2"
        >
            <span class="w-3 h-3 rounded-full bg-[#eff1f5] border border-overlay0"></span>
            Latte (Light)
        </button>
        <button
            onclick="setTheme('frappe')"
            class="w-full px-4 py-2 text-left hover:bg-surface-hover flex items-center gap-2"
        >
            <span class="w-3 h-3 rounded-full bg-[#303446] border border-overlay0"></span>
            Frappé
        </button>
        <button
            onclick="setTheme('macchiato')"
            class="w-full px-4 py-2 text-left hover:bg-surface-hover flex items-center gap-2"
        >
            <span class="w-3 h-3 rounded-full bg-[#24273a] border border-overlay0"></span>
            Macchiato
        </button>
        <button
            onclick="setTheme('mocha')"
            class="w-full px-4 py-2 text-left hover:bg-surface-hover flex items-center gap-2"
        >
            <span class="w-3 h-3 rounded-full bg-[#1e1e2e] border border-overlay0"></span>
            Mocha (Dark)
        </button>
        <hr class="my-1 border-overlay0">
        <button
            onclick="setTheme('system')"
            class="w-full px-4 py-2 text-left hover:bg-surface-hover flex items-center gap-2"
        >
            <span class="w-3 h-3 rounded-full bg-gradient-to-r from-[#eff1f5] to-[#303446] border border-overlay0"></span>
            System
        </button>
    </div>
</div>

<script>
function setTheme(theme) {
    if (theme === 'system') {
        localStorage.removeItem('liftoff-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'frappe' : 'latte');
    } else {
        localStorage.setItem('liftoff-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
    }

    // Sync with server for authenticated users
    if (document.body.dataset.authenticated === 'true') {
        fetch('/api/v1/users/me/preferences', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme: theme })
        });
    }
}

// Listen for system preference changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('liftoff-theme')) {
        document.documentElement.setAttribute('data-theme', e.matches ? 'frappe' : 'latte');
    }
});
</script>
```

---

## Configuration

### Environment Variables

```bash
# .env

# Default theme (latte, frappe, macchiato, mocha)
LIFTOFF_THEME_DEFAULT=frappe

# Allow users to change theme
LIFTOFF_THEME_USER_OVERRIDE=true

# Respect system preference
LIFTOFF_THEME_SYSTEM_PREFERENCE=true
```

### Application Settings

```python
# src/liftoff/core/config.py

from pydantic_settings import BaseSettings
from liftoff.core.theme import ThemeName, ThemeConfig


class Settings(BaseSettings):
    # ... other settings ...

    # Theme settings
    theme_default: ThemeName = ThemeName.FRAPPE
    theme_user_override: bool = True
    theme_system_preference: bool = True
    theme_available: list[ThemeName] | None = None

    @property
    def theme_config(self) -> ThemeConfig:
        return ThemeConfig(
            default_theme=self.theme_default,
            allow_user_override=self.theme_user_override,
            respect_system_preference=self.theme_system_preference,
            available_themes=self.theme_available or list(ThemeName),
        )

    class Config:
        env_prefix = "LIFTOFF_"
```

---

## Component Guidelines

### Using Colors in Components

**Always use semantic color names, not raw palette colors.**

```html
<!-- ✅ CORRECT: Uses semantic colors -->
<button class="bg-primary text-ctp-base hover:bg-ctp-lavender">
    Primary Action
</button>

<div class="bg-surface border border-default rounded-lg p-4">
    <h3 class="text-ctp-text font-semibold">Card Title</h3>
    <p class="text-secondary">Card description</p>
</div>

<span class="text-success">Success message</span>
<span class="text-error">Error message</span>
<span class="text-warning">Warning message</span>

<!-- ❌ INCORRECT: Hardcoded colors -->
<button class="bg-purple-500 text-white">
    Don't do this
</button>

<div class="bg-gray-800 border-gray-600">
    Never hardcode colors
</div>
```

### Component Examples

#### Buttons

```html
<!-- Primary button -->
<button class="
    px-4 py-2 rounded-md font-medium
    bg-ctp-mauve text-ctp-crust
    hover:bg-ctp-lavender
    focus:outline-none focus:ring-2 focus:ring-ctp-lavender focus:ring-offset-2 focus:ring-offset-ctp-base
    disabled:opacity-50 disabled:cursor-not-allowed
">
    Primary
</button>

<!-- Secondary button -->
<button class="
    px-4 py-2 rounded-md font-medium
    bg-ctp-surface0 text-ctp-text
    hover:bg-ctp-surface1
    border border-ctp-overlay0
    focus:outline-none focus:ring-2 focus:ring-ctp-lavender
">
    Secondary
</button>

<!-- Destructive button -->
<button class="
    px-4 py-2 rounded-md font-medium
    bg-ctp-red text-ctp-crust
    hover:bg-ctp-maroon
    focus:outline-none focus:ring-2 focus:ring-ctp-red
">
    Delete
</button>

<!-- Ghost button -->
<button class="
    px-4 py-2 rounded-md font-medium
    text-ctp-text
    hover:bg-ctp-surface0
    focus:outline-none focus:ring-2 focus:ring-ctp-lavender
">
    Ghost
</button>
```

#### Cards

```html
<div class="bg-ctp-surface0 rounded-lg border border-ctp-overlay0 shadow-md overflow-hidden">
    <div class="px-4 py-3 border-b border-ctp-overlay0 bg-ctp-surface1">
        <h3 class="text-ctp-text font-semibold">Card Header</h3>
    </div>
    <div class="p-4">
        <p class="text-ctp-subtext1">Card content goes here.</p>
    </div>
    <div class="px-4 py-3 border-t border-ctp-overlay0 bg-ctp-mantle">
        <span class="text-ctp-subtext0 text-sm">Card footer</span>
    </div>
</div>
```

#### Form Inputs

```html
<div class="space-y-2">
    <label for="email" class="block text-sm font-medium text-ctp-text">
        Email
    </label>
    <input
        type="email"
        id="email"
        class="
            w-full px-3 py-2 rounded-md
            bg-ctp-surface0 text-ctp-text
            border border-ctp-overlay0
            placeholder:text-ctp-overlay2
            focus:outline-none focus:ring-2 focus:ring-ctp-lavender focus:border-ctp-lavender
            disabled:opacity-50 disabled:bg-ctp-mantle
        "
        placeholder="you@example.com"
    >
    <p class="text-sm text-ctp-subtext0">We'll never share your email.</p>
</div>

<!-- Error state -->
<input
    type="email"
    class="
        w-full px-3 py-2 rounded-md
        bg-ctp-surface0 text-ctp-text
        border-2 border-ctp-red
        focus:outline-none focus:ring-2 focus:ring-ctp-red
    "
    aria-invalid="true"
>
<p class="text-sm text-ctp-red">Please enter a valid email.</p>
```

#### Status Badges

```html
<!-- Issue status badges -->
<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-overlay1/20 text-ctp-subtext1">
    To Do
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-blue/20 text-ctp-blue">
    In Progress
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-green/20 text-ctp-green">
    Done
</span>

<!-- Priority badges -->
<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-red/20 text-ctp-red">
    Critical
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-peach/20 text-ctp-peach">
    High
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-yellow/20 text-ctp-yellow">
    Medium
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full bg-ctp-blue/20 text-ctp-blue">
    Low
</span>
```

#### Issue Type Icons

```html
<!-- Task -->
<span class="inline-flex items-center justify-center w-5 h-5 rounded bg-ctp-blue/20">
    <svg class="w-3 h-3 text-ctp-blue" fill="currentColor" viewBox="0 0 20 20">
        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
        <path fill-rule="evenodd" d="M4 5a2 2 0 012-2h8a2 2 0 012 2v10a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
    </svg>
</span>

<!-- Bug -->
<span class="inline-flex items-center justify-center w-5 h-5 rounded bg-ctp-red/20">
    <svg class="w-3 h-3 text-ctp-red" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M6.56 1.14a.5.5 0 01.7.08l.86 1.03a5.48 5.48 0 013.76 0l.86-1.03a.5.5 0 01.78.62l-.7.84a5.5 5.5 0 012.1 3.07l1.08-.15a.5.5 0 01.14.99l-1.12.16a5.5 5.5 0 010 2.5l1.12.16a.5.5 0 01-.14.99l-1.07-.15a5.5 5.5 0 01-2.11 3.07l.7.84a.5.5 0 01-.78.62l-.86-1.03a5.48 5.48 0 01-3.76 0l-.86 1.03a.5.5 0 01-.78-.62l.7-.84a5.5 5.5 0 01-2.1-3.07l-1.08.15a.5.5 0 01-.14-.99l1.12-.16a5.5 5.5 0 010-2.5l-1.12-.16a.5.5 0 01.14-.99l1.07.15a5.5 5.5 0 012.11-3.07l-.7-.84a.5.5 0 01.08-.7zM10 6a4 4 0 100 8 4 4 0 000-8z" clip-rule="evenodd"/>
    </svg>
</span>

<!-- Story -->
<span class="inline-flex items-center justify-center w-5 h-5 rounded bg-ctp-green/20">
    <svg class="w-3 h-3 text-ctp-green" fill="currentColor" viewBox="0 0 20 20">
        <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/>
    </svg>
</span>

<!-- Epic -->
<span class="inline-flex items-center justify-center w-5 h-5 rounded bg-ctp-mauve/20">
    <svg class="w-3 h-3 text-ctp-mauve" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/>
    </svg>
</span>
```

---

## Accessibility

### Color Contrast

All text must meet WCAG 2.1 AA contrast requirements:

| Text Type | Minimum Ratio | Catppuccin Compliance |
|-----------|---------------|----------------------|
| Normal text | 4.5:1 | ✅ `text` on `base` passes in all themes |
| Large text (18px+) | 3:1 | ✅ All text colors pass |
| UI components | 3:1 | ✅ All interactive states pass |

### Focus Indicators

All interactive elements must have visible focus indicators:

```css
/* Focus ring using lavender */
:focus-visible {
  outline: 2px solid var(--ctp-lavender);
  outline-offset: 2px;
}
```

### Motion Preferences

Respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Extending Themes

### Adding Custom Themes

To add a custom theme while maintaining Catppuccin base:

1. Create a new CSS file in `static/css/themes/`:

```css
/* static/css/themes/custom-brand.css */

[data-theme="custom-brand"] {
  /* Override specific colors */
  --ctp-mauve: #your-brand-purple;
  --ctp-blue: #your-brand-blue;

  /* Keep other Catppuccin colors or override as needed */
}
```

2. Register the theme in configuration:

```python
# config
class ThemeName(str, Enum):
    LATTE = "latte"
    FRAPPE = "frappe"
    MACCHIATO = "macchiato"
    MOCHA = "mocha"
    CUSTOM_BRAND = "custom-brand"  # Add custom theme
```

3. Add to available themes in config:

```yaml
theme:
  available_themes:
    - frappe
    - custom-brand
```

### White-Labeling Considerations

For enterprise white-labeling (P4.6):

1. Custom themes can override the primary accent color
2. Logo colors should be independent of theme
3. Email templates should use inline styles derived from theme
4. PDF exports should respect theme or use print-friendly version

---

## Testing Themes

### Visual Regression Testing

Use Percy or Chromatic for visual regression:

```python
# tests/e2e/test_themes.py

import pytest
from playwright.sync_api import Page


@pytest.mark.parametrize("theme", ["latte", "frappe", "macchiato", "mocha"])
def test_theme_renders_correctly(page: Page, theme: str, percy):
    """Visual regression test for each theme."""
    page.goto(f"/?theme={theme}")
    page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")

    # Wait for theme to apply
    page.wait_for_timeout(100)

    percy.snapshot(f"Homepage - {theme}")


def test_theme_switching(page: Page):
    """Test that theme switching works without page reload."""
    page.goto("/")

    # Default should be frappe
    assert page.evaluate("document.documentElement.dataset.theme") == "frappe"

    # Switch to latte
    page.click("[data-testid='theme-switcher']")
    page.click("[data-testid='theme-latte']")

    assert page.evaluate("document.documentElement.dataset.theme") == "latte"
    assert page.evaluate("localStorage.getItem('liftoff-theme')") == "latte"
```

### Contrast Testing

```python
# tests/unit/test_theme_contrast.py

from wcag_contrast_ratio import rgb, passes_AA, passes_AAA


FRAPPE_COLORS = {
    "text": (198, 208, 245),
    "base": (48, 52, 70),
    "subtext1": (181, 191, 226),
    "surface0": (65, 69, 89),
}


def test_text_on_base_passes_aa():
    """Primary text on background must pass AA."""
    ratio = rgb(FRAPPE_COLORS["text"], FRAPPE_COLORS["base"])
    assert passes_AA(ratio, large=False)


def test_subtext_on_surface_passes_aa():
    """Secondary text on surface must pass AA."""
    ratio = rgb(FRAPPE_COLORS["subtext1"], FRAPPE_COLORS["surface0"])
    assert passes_AA(ratio, large=False)
```

---

*Document Version: 1.0*
*Last Updated: January 2026*
