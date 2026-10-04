# Settings native Expressive A/B runtime probe

Static analysis is now strong enough to justify one narrow device experiment.

## What is already proven

On the current ColorOS 17 Settings build:

- `OplusSettingsHomepageActivity` does not override the Android 17
  `ExpressiveDesignEnabledProvider` path.
- `OplusTopLevelSettings` subclasses AOSP `TopLevelSettings`.
- it does not override `onCreateAdapter()`;
- `useOplusStyle()` returns true;
- `getPreferenceScreenResId()` continues to use
  `xml/top_level_settings_oplus`;
- the inherited SettingsLib Expressive adapter/group path remains available.

Therefore the most useful next evidence is an A/B test of the native
`is_expressive_design_enabled` debug override itself, not another custom
CardHook/ListHook.

## Probe

`experiments/ColorOS17_SettingsExpressive_ABProbe_v1.sh`

The script performs:

1. save the original non-persistent property;
2. run Settings with the property false and capture screenshot/UI hierarchy;
3. run Settings with the property true and capture screenshot/UI hierarchy;
4. capture focused Settings logs;
5. restore the original property and recreate Settings again.

It restarts **only** `com.android.settings`, because the native gate is read at
Activity/fragment creation. It does not reboot the phone, restart SystemUI,
change Monet/theme JSON, alter overlays or persist the property.

## Decision gate

If A/B proves a coherent native Expressive Settings implementation, v0.2.0
should prefer enabling that path through a Settings-process-scoped hook/guard
rather than implementing a parallel card/list renderer.

A shipping mechanism is still a separate decision. The debug system property is
an experiment control, not the final ownership model.
