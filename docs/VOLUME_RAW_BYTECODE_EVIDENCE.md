# ColorOS 17 OPlus volume raw-bytecode evidence

Source: the user's PJZ110 ColorOS 17 `SystemUI.apk` from the frozen audit snapshot.

This document records class/method/field/call metadata derived from DEX. No
vendor method bodies are committed.

## 1. Static provider path now proven

The current SystemUI DEX defines:

`com.oplus.systemui.volume.dagger.VolumeModuleExImpl$Companion.provideVolumeDialog(...)`

Return type:

`com.android.systemui.plugins.VolumeDialog`

Its code item begins by allocating:

`com.oplus.systemui.volume.OplusVolumeDialogImpl`

and proceeds to create/bind its OPlus volume repositories/abilities, including
repository/controller bindings and registration with DumpManager.

Representative direct references include:

- `OplusVolumeDialogImpl`
- `OplusVolumeDialogImpl$H`
- `OplusVolumeRepository`
- `SuperVolumeRepository`
- `RingModeRepository`
- `MultiMediaRepository`
- `AudioDataRepository`
- `SafetyWarningRepository`
- `VibrateAbility`
- `IconAbility`
- `VolumeSupplyExportApi.setOplusVolumeDialogImpl(...)`

This closes the earlier static ambiguity about whether the OPlus implementation
family is merely present or actually constructed by an OPlus volume provider.

**Static decision:** AOSP `VolumeDialogImpl` is not the correct primary target
for this ColorOS 17 migration.

Confidence: HIGH.

Runtime confirmation of which provider/component instance is active on the
device remains required.

## 2. Platform-blur lifecycle is explicit

`VolumePlatformBlurSession` has state for:

- context;
- host;
- capture pipeline runnable;
- layout listener;
- engine-acquired state;
- early resource-clear state.

Its methods include:

- `prepareEngine()`
- `startAttachedObservers(View)`
- `ensureForSlider(View)`
- `onBeforeShowAnimate()`
- `onBeforeHideAnimate()`
- `pauseCaptureForTerminalHide(View)`
- `stopCapturePipeline(View)`
- `onDetached(View)`
- `clearResources(boolean)`

This is lifecycle/capture ownership, not a drawable-radius-only effect.

Confidence: HIGH.

## 3. Blur host coordinates real panel/bar/accessory state

`VolumePlatformBlurHostHelper` carries:

- a `VolumePlatformBlurSession`;
- panel/bar background caches;
- capture generation and material generation;
- capture intent/frozen state;
- side-accessory blur state;
- pending capture-region synchronization.

Representative methods include:

- `createPanelBackgroundIfNeeded(View)`
- `assignVolumeBarBackground(...)`
- `bindSideAccessoryPlatformBlur(...)`
- `ensurePanelRowsPlatformBlur(boolean)`
- `syncPlatformBlurCaptureRegion...`
- `scheduleBlurScreenshotCapture()`
- `requestMissingScreenshotCapture(...)`
- `refreshBlurDependentIconTints()`
- handoff/freeze/unfreeze helpers.

This reinforces the native-first rule: panel, row and accessory blur cannot be
safely replaced by one global color or one `blur_radius` resource.

Confidence: HIGH.

## 4. Material capability is an explicit decision object

`VolumeMaterialCapability` tracks:

- default-theme state;
- blur-disabled state;
- light-package state;
- motion-platform state;
- platform-blur-enabled state;
- spotlight-enabled state;
- base-effect state;
- selected paint backend.

It exposes:

- `resolve(Context, boolean)`
- `resolveBlurDisabled(Context)`
- `resolveMotionPlatform(Context)`
- `resolvePlatformBlurEnabled(Context)`
- `getUsesPlatformPaint()`
- `getUsesSolidPaint()`
- `getUsesViewRootPaint()`

Therefore the current volume surface is selected through a capability decision,
not solely through static XML.

Confidence: HIGH.

## 5. Surface/shape construction is component-specific

`VolumeSurfaceFactory.CreateRequest` binds:

- surface kind;
- material capability;
- context;
- host;
- ViewRoot host;
- `VolumeCornerSpec`;
- panel-bottom amount.

`VolumeSurfaceFactory` can create background/content/solid placeholder
surfaces.

`VolumeCornerSpec` stores:

- corner radius;
- optional radius weight.

Its companion exposes separate builders for:

- bar;
- bar ViewRoot;
- progress;
- panel;
- settings button;
- side accessory.

`OplusVolumeShapeGeometry` separately stores:

- shape rect;
- corner radius;
- corner weight;
- smooth-corner flag.

This confirms that **one universal volume radius is structurally wrong**.

Confidence: HIGH.

## 6. Updated release gate

The original Codex report requested additional raw bytecode for the volume
provider/capability/session/factory/shape family. The full user-supplied
SystemUI APK closes that static gap sufficiently for architecture decisions.

The remaining gate is runtime:

- confirm the active provider/component instance on the target device;
- capture actual capability backend for the current theme/blur state;
- verify side/panel/row mode transitions;
- bind any future semantic augmentation to the live OPlus instance.

Accordingly the public policy moves Volume from:

`NEEDS_RAW_BYTECODE + NEEDS_RUNTIME_TRACE`

to:

`NEEDS_RUNTIME_TRACE`

No volume visual mutation is enabled by this change.
