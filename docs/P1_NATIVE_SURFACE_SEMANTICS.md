# P1: preserve ColorOS 17 translucent surface semantics

The old overlay replaces many native COUI neutral surfaces and state layers with opaque Material dynamic colors.

That is visually destructive on ColorOS 17 because several native values deliberately carry alpha for blur/translucency, for example:

- card background in dark mode: #1affffff
- volume panel background: #64888888
- volume COUI background: #33000000
- QS active indicator background: #1affffff

P1 restores the native COUI structural surfaces, labels and press/state colors while leaving accent and Material semantic color roles available for MD3E.

This gives the project a native-first split:

- ColorOS owns physical/translucent surface composition.
- Monet/MD3E owns accent and semantic role coloration.
- Component-scoped hooks may opt into stronger expressive treatment later.
