# Havenwild PCC Branch Workflow 23

The internal PCC should support a stable-main plus experimental-branch workflow.

## Initial command added

```text
Create/switch asset mapper experiment branch
```

Default branch:

```text
experiment/asset-mapper-workspace
```

The script blocks when the working tree is dirty. This prevents mapper/editor experiments from contaminating a clean GREEN checkpoint.

## Future commands

- Show branch status.
- Push current experiment branch.
- Compare experiment branch to main.
- Merge experiment GREEN back to main.
- Abort/reset experiment branch.
- Create branch from latest certified GREEN only.
