# Havenwild W55R8I — Disconnected Gateway Acceptance

## Scope
- Replaces the undersized 8x3 structural gateway test fixture with two inset disconnected Level-1 components.
- Gives each component enough room for the production six-cell directional ramp corridor.
- Asserts that each disconnected component receives a gateway by component membership, rather than by brittle hard-coded edge columns.
- Production ramp selection logic is unchanged.

## Validation
1. `cargo test -p haven_world structural_landform_generation::tests::each_disconnected_raised_component_receives_a_south_gateway -- --nocapture`
2. `cargo test -p haven_world --lib`
3. Control Center `2. Build all`
4. Control Center `10. Run tests`

If all are green, close W55R8 and proceed to W55R9.
