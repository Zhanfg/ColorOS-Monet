# COE native-first P0 patch

The ColorOS 17 baseline keeps COE's unrelated hooks but disables the two package-wide widget entry points that currently force the legacy segmented-card/list treatment across unrelated screens:

- `one.dot.couiexpressive.hooks.widget.CardHook#handleLoadPackage`
- `one.dot.couiexpressive.hooks.widget.ListHook#handleLoadPackage`

The patcher rewrites only those two DEX code items to `return-void`; it does not remove the classes, preferences, SystemUI hooks, Monet hooks, typography hooks, or other COE functionality.

This is deliberately a P0 compatibility measure. Component-scoped expressive cards will be reintroduced later with explicit screen/component eligibility instead of package-wide behavior.

The repository contains only the patcher. It does not contain or redistribute the third-party COE APK.
