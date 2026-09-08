# Pass 163O Repair Audit

- Native editor helper symbols are publicly available in `render_helpers.rs` and now explicitly imported.
- Registered script commands no longer use PowerShell's automatic `$args` variable.
- The launcher forwards the resolved repository root to nested scripts.
- No terrain authority or runtime behavior was changed.
