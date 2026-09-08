# Havenwild Bash Build Entrypoint Pass 54C

## Purpose

Remove PowerShell execution policy from the normal Havenwild build path and make
Git Bash the canonical Windows build environment.

## Changes

- `tools/build/Build.sh` is now the authoritative root build orchestrator.
- Every Bash command writes a timestamped log under `logs/`.
- Step boundaries report `START`, `OK`, or the final failing exit code.
- Added `./tools/build/Build.sh doctor` to show the detected Bash, Cargo, Rust, Python, and
  Node executables before a full build.
- Added explicit executable-existence checks before packaging the client/editor.
- Added `./tools/build/Build.sh clean`.
- `tools/build/Build.cmd` now finds Git Bash and invokes `tools/build/Build.sh` directly.
- `tools/build/Build.cmd` no longer invokes `tools/build/Build.ps1`, so unsigned-script execution policy
  cannot block the normal build.
- Added Pass 69 regression validation.

## Correct commands from the current PowerShell prompt

When the prompt is already:

```text
PS C:\Users\Shifty\Desktop\havenw>
```

stay in that directory. Do not run `cd .\havenw` again.

Run Git Bash directly:

```powershell
& "C:\Program Files\Git\bin\bash.exe" ./tools/build/Build.sh doctor
& "C:\Program Files\Git\bin\bash.exe" ./tools/build/Build.sh check
& "C:\Program Files\Git\bin\bash.exe" ./tools/build/Build.sh apps
```

Or use the Bash-routing command launcher:

```powershell
.\tools/build/Build.cmd doctor
.\tools/build/Build.cmd check
.\tools/build/Build.cmd apps
```

Inside a Git Bash window opened at the repository root:

```bash
./tools/build/Build.sh doctor
./tools/build/Build.sh check
./tools/build/Build.sh apps
```

## Outputs

```text
Build/HavenwildClient/HavenwildClient.exe
Build/HavenwildEditor/HavenwildEditor.exe
logs/havenwild-<command>-<timestamp>.log
```

## Environment override

If Git for Windows is installed outside a standard location, set:

```cmd
set HAVENWILD_BASH=C:\path\to\Git\bin\bash.exe
```

Then use `tools/build/Build.cmd` normally.
