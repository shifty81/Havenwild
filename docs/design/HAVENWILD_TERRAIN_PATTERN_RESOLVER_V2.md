# Havenwild Terrain Pattern Resolver V2

## Signature

A request contains center plus N, NE, E, SE, S, SW, W, NW terrain peers. Each peer is a terrain ID, empty, or wildcard. Matching honors the terrain set's mode.

## Candidate selection

1. restrict candidates to the requested terrain set and center terrain;
2. reject candidates whose required peers conflict;
3. score exact peers above wildcard peers;
4. prefer verified authored candidates;
5. choose deterministic weighted alternatives using world seed and cell coordinate;
6. emit a structured unsupported-pattern record when no candidate matches.

## Shared use

PCG and F3 editing submit the same `TerrainPatternRequest`. The caller may specify `connect`, `path`, or `manual` intent, but it may not bypass candidate feasibility.

## Prototype completion metric

For Grass, Sand, Road, Stone Path, Shallow Water, and Deep Water:

- exact pattern coverage: 100% for allowed prototype scenarios;
- fallback selections: 0;
- invalid PCG placements committed: 0;
- editor and PCG candidate IDs agree for the same neighborhood.
