# Runtime evidence matrix after Codex hard analysis

The static architecture is established. The remaining blockers are runtime- or XML-specific, not permission to guess.

| Gate | Static result | Remaining evidence | Collector coverage |
|---|---|---|---|
| Settings grouped cards | native continuous HEAD/MIDDLE/TAIL/FULL model proven | exact Activity/Fragment/adapter/key/view/layout tuple for any segmented candidate | package/version/activity/overlay/resource baseline; XML/runtime component trace still separate |
| mCardBackgroundColor error | field exists in analyzed Settings superclass | failing process, actual classloader, APK hash, complete stack | APK hashes + filtered logcat |
| UXDesign Monet ownership | UXDesign produces candidates/state; SystemUI creates Android FRRO | user-change/reboot ownership trace; COUI XML consumption | theme JSON + UX color XML snapshots + overlay state |
| QS | QSIconViewProxy/Lottie owner exists | actual active tile/view/state class and loader | package provenance + logcat; Java instance trace still separate |
| Media | plugin section implementation proven | actual root/layout instance and host/plugin binding | package provenance + logcat; XML/runtime binding still separate |
| Volume | OplusVolumeDialogImpl chain proven | active DI choice and capability/session classes | package provenance + logcat; helper bytecode/runtime trace still separate |
| Notification | multiple state/color owners proven | active card-type/blur/colorized path | package provenance + logcat; component trace still separate |

The one-shot shell collector is:

`scripts/ColorOS17_MD3E_RuntimeEvidence_v1.sh`

It is read-only and does not mutate the device to manufacture evidence.
