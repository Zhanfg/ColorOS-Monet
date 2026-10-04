# Report contract

Codex should commit four reports under `codex/hard-analysis/reports/`.

For every report:

1. **Observed facts**
   - exact class/method/field/resource names;
   - source file / DEX where known;
   - confidence: high / medium / low.

2. **Runtime flow**
   - concise call/data-flow diagram;
   - identify owner, producer and consumer of state/resources.

3. **ColorOS 16 → 17 deltas**
   - old assumption;
   - ColorOS 17 replacement;
   - evidence.

4. **Implication for v0.2.0**
   - what to keep native;
   - what MD3E may augment;
   - what old hook/resource must be removed.

5. **Patch contract**
   - exact allowed hook/resource scope;
   - guard conditions;
   - fallback behavior when symbol missing;
   - no package-wide wildcard unless justified.

6. **Unknowns**
   - use `NEEDS_RAW_BYTECODE`, `NEEDS_RUNTIME_TRACE`, or `NEEDS_RESOURCE_XML`;
   - never fill an evidence gap with a guess.

## Final synthesis

After the four reports, create:

`codex/hard-analysis/reports/00_ARCHITECTURE_SYNTHESIS.md`

It must define one coherent stack:

```text
ColorOS 17 native component structure
        ↓
UXDesign / native Monet palette
        ↓
small semantic MD3E resource layer
        ↓
component-scoped COE hooks
```

and explicitly reject any design that requires global COUI round-corner/divider/card replacement.
