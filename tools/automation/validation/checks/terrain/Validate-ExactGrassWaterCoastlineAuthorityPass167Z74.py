from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
life = (ROOT/'crates/haven_game/src/world_paint_lifecycle.rs').read_text()
start = (ROOT/'crates/haven_game/src/runtime_startup.rs').read_text()
errors=[]
needle='let _ = Self::apply_generated_coastline_cleanup(world, log);'
if needle in life:
    errors.append('paint replay still runs generated coastline cleanup')
if 'Self::migrate_legacy_natural_object_footprints(&mut world)' not in start:
    errors.append('saved-world migration is not using targeted footprint migration')
segment=start[start.find('if saved_generation < CURRENT_CLIENT_GENERATION_VERSION'):start.find('log.event(&status);', start.find('if saved_generation < CURRENT_CLIENT_GENERATION_VERSION'))]
if 'apply_generated_coastline_cleanup' in segment:
    errors.append('saved-world migration still rebuilds coastlines')
if errors:
    raise SystemExit('Z74 validation failed:\n- ' + '\n- '.join(errors))
print('Pass167Z74 exact grass/water coastline authority validated')
