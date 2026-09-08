from pathlib import Path
from validation.native import run_legacy_group

def validate(entry,root:Path):
    return run_legacy_group(validator_id=entry['id'],name=entry['name'],domain=entry['domain'],phase=entry['phase'],root=root,scripts=[
      'tools/automation/validation/checks/worldgen/Validate-HavenwildOpenWorldPreset.py','tools/automation/validation/checks/worldgen/Validate-WrappedWorldCoordinateFoundationV139.py','tools/automation/validation/checks/worldgen/Validate-ArchipelagoWorldSkeletonV140.py','tools/automation/validation/checks/terrain/Validate-TerrainWorldSemanticRegistryV142.py','tools/automation/validation/checks/worldgen/Validate-WorldGenerationPipelineOwnershipV143.py','tools/automation/validation/checks/worldgen/Validate-ChunkPersistenceNormalizationV144.py'])
