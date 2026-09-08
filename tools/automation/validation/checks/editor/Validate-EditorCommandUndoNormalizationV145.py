#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
contract=json.loads((ROOT/'content/editor/commands/editor_command_contract_v1.json').read_text())
assert contract['schema']=='havenwild.editor.command-contract.v1'
assert contract['policy']['singleMutationPath'] is True
required=set(contract['requiredMetadata'])
assert required=={'affectedBounds','dirtyChunks','validationRequests','permissionScope','persistenceIntent','requiresAuthoritativeHost'}
source=(ROOT/'crates/haven_authoring/src/command_bus.rs').read_text()
for token in ['CommandExecutionMetadata','CommandBounds','DirtyChunkKey','CommandPermissionScope','CommandPersistenceIntent','with_execution_metadata','NormalizeRegion','GenerateShore','RegenerateChunk','CommitPcgPreview']:
    assert token in source, token
manifest=json.loads((ROOT/'content/validation/validation_manifest_v1.json').read_text())
assert any(t['id']=='validate-editorcommandundonormalizationv145' and t['lifecycle']=='active' for t in manifest['tasks'])
print('Pass 145 editor command and undo normalization validated')
