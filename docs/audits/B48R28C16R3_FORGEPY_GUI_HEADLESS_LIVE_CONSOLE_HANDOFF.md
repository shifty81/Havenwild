# Havenwild B48R28C16R3 — ForgePY GUI headless live-console repair

## Source and authority

This is a **cumulative, overwrite-capable Havenwild root-intake ZIP**, based on GitHub `experimental` C4 commit `d9c01b26ec2440f97fc1f6167ee561bc6d43e86e`; it includes all 53 C16R2 predecessor payloads unchanged. Apply **only this ZIP**, not C16R2 again, when C16R2 is already installed. This updates the *bundled Havenwild-local ForgePY distribution*, not the upstream ForgePY/Forge donor repo. `HavenwildTools.cmd` and its project-native PCC remain the update, gate and publication authority. No remote repository was mutated by producing this package.

## Actual defect

`.forgepy/gui/pcc_gui.py` hides only the direct ForgePY subprocess, but `.forgepy/runtime/forgepy.py::stream()` previously launched grandchild `cmd`, PowerShell and build tools with `CREATE_NEW_PROCESS_GROUP` and no `CREATE_NO_WINDOW`. With a `pythonw.exe` GUI host that creates unwanted console windows. The Python backend used default buffering and both pipeline readers iterated lines, delaying output lacking a newline. The previous UI's Logs page also replaced the current workspace rather than remaining visible.

## Corrected implementation

- GUI entrypoint chooses `pyw.exe` / `pythonw.exe` and never automatically starts a console PCC as a fallback. If GUI initialization fails, see `.forgepy/state/logs/gui-startup-error.log` and deliberately run `ForgePY.cmd menu` for an interactive CLI.
- GUI uses the paired `python.exe -u` (when launched under `pythonw.exe`), `PYTHONUNBUFFERED`, `PYTHONUTF8`, UTF-8 stdout/stderr pipe merging, hidden Windows creation flags **and** hidden startup info. Commands have `stdin=DEVNULL` in GUI mode: interactive prompts fail rather than waiting behind a hidden console.
- ForgePY `stream()` propagates the hidden-process contract to grandchild programs, retaining process groups and process-tree cancellation. The runtime and GUI both forward decoded UTF-8 *chunks*, not newline-terminated lines; the runtime flushes immediately and retains child logs and exit codes.
- One resizable, dark, persistent console stays below Dashboard, Build Plan, Operations, Patches, Git, Recovery and Settings. The Logs navigation focuses this console. Worker queues have bounded capacity and GUI event draining is time-sliced.
- Every operation produces a complete `.forgepy/state/logs/gui-*.log` (or in-project configured state directory) independent of the bounded on-screen history and operation-specific logs. Invalid state-directory escapes are rejected. The exit code is included in the transcript; Clear never deletes saved logs.
- ForgePY has a distinct Havenwild integration build/version and updated integrity manifest, runtime lock and provenance. Its `runtime-self-test` now invokes the new stdlib-only, display-free console regression suite. Project installer instructions now refer to the actual `ForgePY-GUI.cmd` and `HavenwildTools.cmd` launchers.

## Scope limits and Windows check

Python suite and package integrity checks can run without Windows or Tk display. **Native Win32 console suppression, full GUI rendering and actual child process-tree cancellation are NOT verified by Linux tests.** An explicitly detached child launched by project-owned `Start-Process`, `start`, or a terminal emulator cannot be reattached to stdout after the fact; adjust those specific project command adapters to invoke inheriting, noninteractive processes. Interactive `pause`, `Read-Host`, and terminal-only TUIs must not be run through the hidden GUI command path.

After PCC applies this patch, close/relaunch any existing ForgePY GUI so it loads the patched Python code. In your original Havenwild folder, run `ForgePY-Verify.cmd`, then `ForgePY-GUI.cmd`. Start a Build or Test in ForgePY, switch Dashboard/Operations while it runs, confirm the lower console stays visible, emits stdout/stderr without extra cmd/PowerShell windows, shows the exit code, and saves `gui-*.log` in its Logs directory. If any console window still opens, capture the operation's exact key and child executable plus the GUI transcript; investigate that adapter's detached process. The existing `HavenwildTools.cmd` is intentionally an interactive console and is not converted into a hidden application.

Run the Havenwild Full Quality Gate **after** applying this source modification, before Commit + Push GREEN. Do not attribute a GREEN status or Windows GUI certification to this authoring-environment package.
