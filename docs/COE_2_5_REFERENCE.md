# COE 2.5 capability reference

## Source boundary

This document records a clean-room capability study of the project-owner-supplied
`COE 2.5.apk`. The APK itself is not committed, redistributed, linked into the
build, or used as a binary dependency.

Observed package metadata:

| Field | Value |
|---|---|
| SHA-256 | `afe7d36bac69127d6962158d04792c48020bf6dd082fad6ca2a2495c5e43b0f7` |
| Package | `one.dot.couiexpressive` |
| Version name | `2.5.0.260802` |
| Version code | `25` |
| Minimum SDK | `35` |
| Target SDK | `36` |
| Module entry | `one.dot.couiexpressive.hooks.HookEntry` |
| Framework | LSPosed/Xposed module with a Jetpack Compose settings UI |

The declared Xposed scope covers:

- Android framework;
- Settings;
- SystemUI;
- OPlus Wireless Settings;
- OPlus Notification Manager;
- ColorOS/OPlus Launcher;
- the module process itself.

No source, bytecode, resource file, icon, font, vector path, layout, preference
key, or implementation-specific method signature from the supplied APK is
copied into ColorOS Monet.

## Capability taxonomy

The supplied reference demonstrates that a complete Expressive adaptation is
not a color-table problem alone. Its observable capability groups are:

### Common widget behavior

- segmented cards and list groups;
- Material-style switches and buttons;
- expandable large toolbars;
- popup and ripple behavior;
- stretch overscroll;
- settings-page search and app-info actions.

### Settings surfaces

- homepage title/search restructuring;
- account-card geometry;
- list spacing, separators, radii, typography, and secondary-text placement;
- special-function cards and Wi-Fi detail controls.

### Launcher surfaces

- dock/search pill;
- themed icon rendering and icon masks;
- folder background and blur mixing;
- recents empty-state, clear button, title, and scrim behavior;
- gesture and transition changes.

### SystemUI surfaces

- notification cards, grouped-notification motion, and ripple feedback;
- classic and separated Quick Settings layouts;
- three-stage tile corners and tile icon animation compatibility;
- vertical/horizontal brightness and volume sliders;
- volume dialog geometry and interaction;
- lock-screen clock, AOD, wallpaper dimming, shortcuts, media progress, and lyrics;
- UDFPS icon, glow, and successful-unlock ripple;
- native-style global actions and edge-back indicators;
- dynamic palette refresh and ColorSpec-style wallpaper extraction.

## Architecture consequence

A fabricated resource overlay can replace compatible resources, but it cannot
reliably implement runtime layout restructuring, gesture interception, view
animation, state-machine changes, media integration, or method-level behavior.
Therefore ColorOS Monet uses a layered component model:

1. **resource layer** — APK-free Fabricated Runtime Resource Overlay for safe
   color, dimension, string, and independently authored drawable replacement;
2. **behavior layer** — a single project-owned runtime bridge for audited,
   version-gated operators; components remain `.cmonet` data packages rather
   than one APK per target;
3. **control layer** — Rust owns package verification, component state,
   compatibility gates, diagnostics, and WebUI-readable metadata.

The behavior layer is not considered complete until it has a working loader,
explicit firmware fingerprints, crash containment, and device-side tests. The
project will not label resource-only coverage as equivalent to the supplied
reference.

## Visual inspiration notice

The owner-provided COE/COUI Expressive screens are used as visual and interaction
inspiration for surface hierarchy, rounded segmented groups, dynamic accents,
and expressive motion. No screenshot, artwork, layout, or implementation is
copied.
