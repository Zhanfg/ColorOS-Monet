# Material Symbols upstream verification

The upstream verifier intentionally does **not** clone the full
`google/material-design-icons` repository.

The repository contains thousands of symbol directories and a full sparse
checkout was still unnecessarily expensive for every mapping change.

Instead CI now:

1. pins the exact upstream commit in `upstream.lock`;
2. pins the exact `symbols/android` Git tree SHA;
3. reads the 4,150 symbol directories through the authenticated GitHub Git Trees API;
4. fetches only the 57 (or later) symbol subtrees actually referenced by the curated ColorOS mapping;
5. verifies the requested Android VectorDrawable filename exists for each shipping candidate.

This keeps the provenance exact while avoiding a multi-megabyte/large-tree
checkout on every run.
