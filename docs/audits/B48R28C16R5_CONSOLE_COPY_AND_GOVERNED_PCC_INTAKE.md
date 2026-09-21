# B48R28C16R5 — Console copying and governed ZIP intake

**Cumulative patch:** C16R4 plus R5. Core **U5-derived**; U8/U9 are other standalone release lines and are not imported or falsely relabeled here.

## Corrected

- Copy All copies all console widget text, not just selection. Copy Full Log copies the complete per-operation UTF-8 transcript (limit 16 MiB for GUI safety, beyond which use the log file). Clear does not delete evidence.
- Original GUI explicitly blocked `transport-zip` and generic `forgepy.py` only supports `.patch`; removing the button's condition alone is unsafe.
- Recognized Havenwild ZIPs now receive read-only manifest preview; selected ZIP must be the only pending recognized root transport. GUI delegates apply to existing `HavenwildPccHost.ps1 -Command updates.apply-pending`, which calls original PCC preflight, transactional root intake, ledger, source-change/restart lifecycle.
- No direct ZIP extraction, additional patch engine, certificate forgery, force-push or automatic commit.
- Dashboard retains Full Gate and guarded Commit + Push GREEN; original ElizaWy source/scene/artwork unchanged.

## Exact workflow

Drop **one** latest cumulative ZIP in Havenwild root, reopen ForgePY GUI and select Patches > Refresh > select ZIP > Validate > Apply via Havenwild PCC > confirm. After successful completion close/relaunch ForgePY GUI because its code may have updated, run **PCC Full Gate**, then Commit + Push only if GREEN. Never apply predecessor ZIPs alongside this cumulative ZIP. If GUI remains on the old binary/code, use existing HavenwildTools.cmd root intake to bootstrap the patch first.

## Verification boundaries

Python syntax, targeted unittest, package verify/self-test, and checksum/ZIP checks are executable here. PowerShell and Windows GUI operation remain untested here. Full gate GREEN and actual U8/U9 migrations are not claimed.
