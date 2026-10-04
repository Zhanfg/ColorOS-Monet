# Codex integration gate

The shipping v0.2.0 branch may continue with simple resource-policy and packaging work while hard structural analysis runs.

The following implementation areas are frozen until the corresponding Codex reports exist:

- Settings grouped/segmented card hooks;
- UXDesign theme-style mutation or palette-generation hooks;
- SystemUI QS/media/notification/volume/clock hooks;
- COE CardHook/ListHook/MonetColorSpec2025Hook/QsLottieHook retargeting.

Allowed meanwhile:

- semantic color allowlist maintenance;
- packaging and update safety;
- read-only diagnostics;
- CI policy linting;
- removal of legacy/global/generic-artwork paths.

This prevents speculative code from outrunning structural evidence.
