# Settings native Expressive multi-screen A/B gate

Codex static analysis established that Settings/SettingsLib already owns a native Expressive component path, gated by `SettingsThemeHelper.isExpressiveTheme(context)`. The current build also exposes `is_expressive_design_enabled`, but static evidence is not enough to promote that gate into the shipping module.

The one-shot probe `scripts/ColorOS17_SettingsExpressive_MultiScreenAB_v1.sh` tests six Settings surfaces with the gate OFF and ON: Settings home, Display, Sound, Security, Privacy and About device.

It restarts **Settings only**, captures screenshots and sanitized UIAutomator hierarchies, restores the original property, then reopens Settings. It does not mutate the Monet/theme JSON, OverlayManager state, SystemUI, or the shipping module.

## Promotion criterion

The native gate may become the preferred Settings MD3E path only if the intended native grouped/Expressive component changes are visible, OPlus homepage rows retain correct two-tone/tint ownership, About Device remains on its component-specific native layout, no page shows the legacy isolated-mini-card failure, the restored capture returns to the original mode, and no crash/resource error appears.

Until this A/B evidence exists, `settings_segmented_whitelist.tsv` stays empty and the shipping module does not force the native gate.
