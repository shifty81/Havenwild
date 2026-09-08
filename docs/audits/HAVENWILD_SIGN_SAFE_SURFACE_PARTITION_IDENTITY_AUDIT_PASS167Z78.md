# Havenwild Sign-Safe Surface Partition Identity Audit — Pass 167Z78

## Observed failure

- Build gates through strict Clippy: passed.
- All prior crate tests: passed.
- `haven_world`: 174 passed, 1 failed.
- Failure: `continuous_surface::tests::surface_partition_identity_is_recognized_without_loading_target_scene`.
- Rejected identity: `surface_x_n1_y_4`.

## Audit conclusion

The runtime generator emits canonical `p#`/`n#` tokens, but the continuous-surface bridge intentionally tests historical unsigned-positive compatibility. The previous `parse_signed_token` helper rejected the plain `4` token.

## Applied repair

`parse_generated_chunk_scene_id` now uses the same `parse_surface_grid_token` function as PCG partition IDs. This accepts canonical positive, canonical negative, and historical unsigned-positive tokens without accepting hyphen-damaged or unrelated scene IDs. The obsolete duplicate parser was removed.

## Non-goals

No source artwork, terrain atlas, hydrology, marine/freshwater logic, save content, PCG shapes, or rendering paths changed.
