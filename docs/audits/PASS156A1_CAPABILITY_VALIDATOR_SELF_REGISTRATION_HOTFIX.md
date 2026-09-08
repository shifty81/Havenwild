# Pass 156A1 — Capability Validator Self-Registration Hotfix

Pass 156A moved current validation behind named capability suites. Three terrain validators still asserted that `tools/build/Build.sh` or the legacy `tools/automation/validation/validate.py` registry directly named their historical standalone scripts.

Pass 156A1 removes those obsolete self-registration checks from V116 and V121, and removes the direct-validator registration requirement from V122 while retaining V122's meaningful requirement that the mapped LPC terrain atlas generation step exists.

No Rust runtime, terrain topology, water shader, material, save, world generation, editor, or gameplay code changed.
