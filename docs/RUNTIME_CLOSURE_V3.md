# Runtime closure v3

This is the single device-side evidence pass intended to follow the completed Codex hard analysis.

Script: `scripts/ColorOS17_MD3E_RuntimeClosure_v3.sh`

It combines the remaining Settings native-Expressive A/B, narrow Settings/SystemUI XML, SystemUIPlugin media XML, package/runtime provenance and targeted COE/SystemUI logs in one reversible run.

The script temporarily toggles the non-persistent `is_expressive_design_enabled` property and recreates only `com.android.settings`. It restores the original property before exit and from an interrupt trap.

It does not reboot, restart SystemUI, modify theme JSON, mutate OverlayManager, change LSPosed scope or persist a system property.

A/B screenshots are included because layout/geometry is the evidence target. UIAutomator XML has visible text/content-desc/hint stripped. Notification/media contents are not dumped.

Output is written to Download and auto-split into 8 MiB parts when needed.

This is an evidence collector, not a shipping UI patch.
