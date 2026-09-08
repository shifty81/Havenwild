# Generated Asset Provenance — Pass 146D

Pass 146D upgrades generated-output ownership from timestamp-only freshness to content-addressed provenance.

Each tracked output declares a stable generator ID, generator version, source inputs, output schema version, atomic-write requirement, and provenance sidecar path in `content/build/generated_output_registry_v2.json`.

Generation writes primary outputs through `tools/automation/common/atomic_io.py`, which creates a sibling temporary file and commits it with `os.replace` only after the writer succeeds. Interrupted generation removes the temporary file and leaves the previous final output intact.

After the generation stage, `Stamp-GeneratedOutputProvenanceV146D.py` records SHA-256 digests for the output and every source input. `Validate-GeneratedOutputProvenanceV146D.py` rejects missing sidecars, generator-version drift, output corruption, and stale input digests.
