# Runtime closure v4

This is the single no-argument device pass after the completed Codex structural analysis.

It supersedes the earlier v3 collector and the separate multi-screen Settings A/B script for the next evidence round.

## What it closes in one run

- hashes current Settings/SystemUI/SystemUIPlugin/UXDesign/COE packages;
- records current theme JSON and blur state;
- extracts the narrow Settings grouped/Expressive XML set;
- extracts the known SystemUIPlugin media XML set;
- performs OFF/ON A/B for the native Settings Expressive gate across:
  - Settings home
  - Display
  - Sound
  - Security
  - Privacy
  - About device
- captures screenshots plus sanitized UIAutomator hierarchy;
- restores the original property and captures the restored homepage;
- captures observational SystemUI window/layer/media-session evidence;
- captures targeted COE/SystemUI exceptions and hook logs;
- automatically splits output into 8 MiB parts when necessary.

## Safety boundary

The script:

- does not reboot;
- restarts **Settings only**;
- does not restart SystemUI;
- does not change theme JSON;
- does not mutate OverlayManager;
- does not change LSPosed scope;
- does not persist the temporary Expressive property;
- restores the original property on normal exit and interrupt.

This is an evidence collector, not a shipping patch.
