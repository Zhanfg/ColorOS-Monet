# ColorOS 17 Native Expressive Bridge

Experimental LSPosed companion for the v0.2.0 native-first architecture.

## What it does

On audited ColorOS 17 packages it enables the Android SettingsLib native
`FeatureFlagsImpl.isExpressiveDesignEnabled` boolean.

For alpha1 the scope is intentionally limited to:

- `com.android.settings`
- `com.android.systemui`

## What it does NOT do

It does not:

- replace COUI global corner tokens;
- hide list dividers;
- turn every preference row into a segmented card;
- patch `COUICardListSelectedItemLayout`;
- emulate blur;
- replace ColorOS icons.

If the feature class/field is absent, it fails closed and leaves the package native.

## Relationship to COE

This bridge is intended to replace the package-wide CardHook/ListHook part of the
old approach with Android 17's native expressive implementation. Other COE
features can be evaluated independently.

Do not enable two different modules that both force preference-card geometry at
the same time during visual validation.
