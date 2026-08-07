# Backend matrix

## Why one backend is insufficient

Resource replacement and runtime behavior are separate failure planes. A target
may accept a color override while still requiring code-level behavior for card
composition, gesture handling, animation, or state synchronization.

| Capability | Fabricated overlay | Runtime behavior bridge | Current state |
|---|---:|---:|---|
| Dynamic color roles | Yes | Optional | Implemented, device validation required |
| Dimensions and booleans | Yes | Optional | Implemented, device validation required |
| Independent drawables | Yes | Optional | Implemented, device validation required |
| Layout restructuring | No | Yes | Planned, not claimed complete |
| Gesture interception | No | Yes | Planned, not claimed complete |
| Stateful animation | No | Yes | Planned, not claimed complete |
| Media/lyrics integration | No | Yes | Out of current release scope |
| Compose runtime theming | Usually no | Yes | Planned, target-version dependent |

## Packaging rule

Target adaptations are distributed as `.cmonet` component packages. The project
will not create one Overlay APK or one hook APK per target.

A future behavior bridge may be a single project-owned loader shared by all
components. Component packages may reference only audited operator IDs and
version gates; arbitrary executable payloads are not accepted by the component
installer.

## Safety gates

Behavior operators require all of the following before activation:

- exact target package and version/fingerprint match;
- explicit supported firmware range;
- process-level crash guard and automatic disable;
- deterministic rollback;
- operator allow-list in the signed core runtime;
- device-side test evidence.
