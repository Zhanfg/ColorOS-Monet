# Runtime evidence pass after Codex static analysis

The Codex reports are complete, but they explicitly keep several runtime gates open.

This collector closes the highest-value gaps without changing device state.

## Collects

- current ColorOS theme JSON and theme-related settings;
- current `/data/oplus/uxres/uxcolor` XML/text files, timestamps and hashes;
- exact package paths, versions and APK SHA-256 values for Settings, SystemUI, Launcher, UXDesign, SystemUIPlugin and COE;
- OverlayManager and relevant idmap state;
- current Settings activity/window information;
- a sanitized UIAutomator tree for the currently visible screen (text/content-desc removed);
- filtered COE/LSPosed exceptions including `mCardBackgroundColor`;
- filtered SystemUI component-class logs;
- SurfaceFlinger layer names relevant to Settings/SystemUI.

## Privacy boundary

The script does not dump notification contents, media-session metadata, screenshots, contacts, messages or app-private databases.

The UI hierarchy has user-visible text and content descriptions stripped before packaging.

## Does not do

- no theme-style writes;
- no overlay enable/disable;
- no app/SystemUI restart;
- no LSPosed scope changes;
- no injected runtime hooks.

If classloader or actual object-class evidence is still missing after this pass, the next step is a narrow diagnostic hook, not a broad UI hook.
