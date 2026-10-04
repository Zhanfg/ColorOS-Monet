# ColorOS 17 SystemUI resource-XML evidence

Source: the user's PJZ110 ColorOS 17 `SystemUI.apk` from the frozen audit snapshot.

This file records **derived structure and resolved resource names/values only**.
Vendor XML, drawable payloads and APK bytes are not committed.

## 1. Volume is an OPlus-native component family

### Dialog layout

`res/layout/oplus_volume_dialog.xml` resolves to a ConstraintLayout containing,
among other native OPlus components:

- `com.oplus.systemui.volume.view.OplusVolumeSettingsButton`
- a RecyclerView for volume rows;
- OPlus side-accessory buttons;
- native SystemUI volume artwork/resources.

The dialog text uses:

`color/oplus_volume_plane_text_color = #ffffffff`

Representative panel dimensions include:

- settings button: 52dp × 52dp;
- settings icon: 48dp × 48dp;
- vertical RecyclerView height: 224dp.

### Row / slider layout

`res/layout/vertical_volume_row.xml` directly instantiates:

`com.oplus.systemui.volume.OplusVolumeSeekBar`

and supplies native COUI vertical-seekbar attributes:

- background color → `oplus_volume_coui_background = #33000000`
- progress color → `oplus_volume_bar_progress_background = #ffffffff`
- background radius → `volume_vertical_row_radius_os17 = 23dp`
- radius-weight → `volume_vertical_row_radius_weight_os17 = 0`
- deformation → `true`
- showThumb → `false`
- elevation → `volume_elevation = 8dp`
- background-enlarge scale → `0.16`
- radius-enlarge scale → `0.27`
- row/seekbar width token → 46dp

This is direct XML corroboration of the Codex bytecode result: volume geometry,
deformation, slider behavior and visual-state ownership are already native OPlus
responsibilities.

**Decision:** v0.2.0 must not replace the volume slider/card geometry globally.
Any MD3E work is limited to a verified semantic role at the exact OPlus
component owner.

Confidence: HIGH.

## 2. Volume background resource is a fallback/surface input, not the blur engine

`res/drawable/volume_dialog_background.xml` is a simple shape:

- radius → `volume_dialog_background_corner_radius = 30dp`
- solid → `materialColorSurface`

The same APK also defines:

- `volume_dialog_background_square_corner_radius = 12dp`
- `volume_dialog_background_surface_blur_radius = 23dp`
- `oplus_volume_panel_background = #64888888`
- `oplus_volume_panel_background_default = #ff333333`

The Codex bytecode report separately proves that actual volume rendering may use
VolumeBlurManager / ViewBlurProxy / platform or motion blur capability.

Therefore these XML colors/dimensions are **inputs/fallbacks**, not proof that
changing one resource owns the live blur pipeline.

Confidence: HIGH.

## 3. Notifications have separate surface, state and focus layers

`res/drawable/notification_material_bg.xml` is a layer-list with three
distinct layers:

1. base surface:
   `materialColorSurfaceContainerHigh`
   → Android system dynamic surface-container-high role;
2. notification state overlay:
   `notification_state_color_default`;
3. focus outline:
   id `notification_focus_overlay`,
   width `notification_focus_stroke_width = 3dp`,
   color `notification_focus_overlay_color`.

`notification_state_color_default.xml` is itself a state selector based on
`materialColorOnSurface` with different alpha/state handling.

`notification_focus_overlay_color.xml` is another selector:
focused state uses `materialColorSecondary`; default is transparent.

Separately, `res/drawable/notification_bg.xml` switches between:

- `notification_bg_normal_pressed`
- `notification_bg_normal`

using `state_pressed`.

This is direct resource evidence that notification base surface, press state and
focus outline are not one global “notification card color”.

**Decision:** never flatten notification background/state/focus into one
semantic RRO or one global CardHook.

Confidence: HIGH.

## 4. QS has multiple native tile geometries and state resources

The current SystemUI APK contains separate layouts for:

- `oplus_qs_tile_1x1`
- `oplus_qs_tile_2x1`
- `oplus_qs_tile_2x2`
- `oplus_qs_tile_three_stage`

These layouts have different root/container geometry and share native state
propagation using `duplicateParentState`. They include a dedicated icon
container and native background ImageView rather than one universal card
layout.

Static QS fallback/background drawables also have explicit state geometry:

- `status_bar_qs_tile_bg_active`: 11dp radius;
- `status_bar_qs_tile_bg_inactive`: 11dp radius;
- equivalent highlight-tile active/inactive backgrounds also use 11dp.

The corresponding colors are:

- `status_bar_qs_tile_bg_color_active = #ff1875f5`
- `status_bar_qs_tile_bg_color_inactive = #ffffffff`
  (night resolves to native COUI pressed-card color).

The brightness-slider background resource is a separate 186×414 vector with
60-unit rounded ends and layered alpha, fed by
`status_bar_qs_brightness_slider_bg_color`.

These static resources are **not** authorization to override the runtime QS
state pipeline. Codex already proved native repositories/interactors,
TileIconColorState, QSIconViewProxy and Lottie/state owners.

**Decision:** preserve all native tile size/state/shape/Lottie ownership.
Potential MD3E augmentation must bind to one proven tile/control consumer and
reuse its live state.

Confidence: HIGH for XML; runtime owner still requires trace.

## 5. What the XML closes

The following static uncertainties are now closed:

- Volume row really uses `OplusVolumeSeekBar`.
- ColorOS 17 volume dimensions are explicitly OS17-specific in resources.
- Notification base/state/focus are separate drawable/color layers.
- QS 1×1 / 2×1 / 2×2 / three-stage layouts are distinct native structures.
- QS and volume geometry cannot safely be inferred from one shared global
  radius token.

## 6. What remains blocked

Still required before enabling SystemUI mutations:

- QS active runtime classloader, tile mode and state-flow trace;
- Notification CardType / colorized / heads-up / low-gaussian active branch;
- SystemUIPlugin `media_card_section` XML/root + active binder/recycle trace;
- Volume current DI/capability/session/helper definitions + active instance;
- Clock active instance and DarkIconDispatcher contrast trace.

Resource XML evidence narrows the contracts; it does not replace runtime proof.
