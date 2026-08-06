# Clean-room policy

The following content is prohibited from source control and release source archives:

- Target application APK/XAPK files.
- APKs copied from another theming module.
- Extracted proprietary images, vectors, fonts, bytecode, native libraries, or translated resource files.
- Private signing keys, tokens, passwords, cookies, and API credentials.

Allowed compatibility data:

- Package names.
- Resource identifiers.
- Version numbers and hashes supplied for compatibility testing.
- Independently authored semantic mappings and artwork.
- References to public Android framework resources.

A new feature derived from a third-party module's binary payload must not be merged. It must be independently reimplemented from target behavior, public platform documentation, or user-provided target-package analysis.
