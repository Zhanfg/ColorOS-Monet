# Native foundation is migration-only

The legacy-resource classifier established that hundreds of old overrides should simply return to ColorOS 17 ownership.

The clean v0.2.0 module therefore **does not package the native-foundation correction RROs by default**.

That layer remains available as a migration/debug artifact for experiments that still combine the old v0.1.4 binary overlays with the new architecture.

The clean shipping path is simpler:

```text
ColorOS 17 native resources
        ↓
ColorOS UXDesign / native Monet
        ↓
small MD3E semantic accent RROs
        ↓
component-scoped hooks (when explicitly implemented)
```

There is no reason to overlay a native value back onto ColorOS when the legacy override is no longer present.

This removes an entire precedence layer and makes the final design system easier to reason about, faster to mount, and less fragile across ColorOS updates.
