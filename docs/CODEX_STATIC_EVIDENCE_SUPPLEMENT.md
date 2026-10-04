# Static evidence supplement after Codex

The Codex reports were intentionally based on a reduced hard-input pack. The archived v4.1 target dump contains the full ColorOS 17 SystemUI DEX set, so several `NEEDS_RAW_BYTECODE` volume-helper gaps can be narrowed without another device extraction.

## Volume material/blur helper definitions now confirmed

Full class definitions exist in current SystemUI `classes9.dex` for:

- `VolumeMaterialCapability`
- `VolumePlatformBlurSession`
- `VolumeSurfaceFactory`
- `VolumeCornerSpec`
- `OplusVolumeShapeGeometry`
- `OplusVolumeShapeGeometryResolver`

This is stronger than the earlier string/reference-only evidence.

### Capability ownership

`VolumeMaterialCapability` explicitly carries:

- `baseEffectOk`
- `blurDisabled`
- `isDefaultTheme`
- `lightPackageEnabled`
- `motionPlatform`
- `paintBackend`
- `platformBlurEnabled`
- `spotLightEnabled`

and exposes static resolver methods for platform blur, motion platform, blur disable, spotlight and final capability resolution.

Therefore a future MD3E volume patch must not force a single blur backend or solid surface. Native capability selection remains the owner.

### Blur lifecycle ownership

`VolumePlatformBlurSession` owns engine/session lifecycle methods including:

- `prepareEngine`
- `ensureForSlider`
- `startAttachedObservers`
- `onBeforeShowAnimate`
- `onBeforeHideAnimate`
- `invalidatePanel`
- `stopCapturePipeline`
- `clearResources`

This confirms that blur is a stateful runtime session, not a radius/color resource that can safely be replaced by a global RRO.

### Shape ownership

`VolumeCornerSpec` stores native radius/weight state and exposes platform/smooth-weight accessors.

`OplusVolumeShapeGeometry` stores:

- corner radius
- corner weight
- smooth-corner flag
- internal shape rect

and provides material-bounds comparison.

`VolumeSurfaceFactory` owns background/content/solid-placeholder creation.

### Dialog chain

The full DEX also confirms:

`OplusVolumeDialogImpl -> OplusVolumeDialogView -> VolumePlatformBlurSession / material helpers`

with `OplusVolumeDialogView` holding both `platformBlurSession` and `blurHostHelper`.

## What remains unresolved

This closes the **helper-bytecode existence/structure** part of the Codex request, but not the runtime-DI gate.

Still required before a shipping hook:

- active runtime instance / DI selection;
- current capability values on the device;
- exact panel/row/slider semantic color consumers;
- lifecycle validation during show/hide, expanded/collapsed and single-app volume.

Machine-readable evidence is in:

`compat/coloros17/volume_material_helpers.tsv`
