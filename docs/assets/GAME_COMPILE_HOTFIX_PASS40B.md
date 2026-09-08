# Game Compile Hotfix — Pass 40B

Fixes compile errors reported after World Paint Layer Composition Pass 40.

## Fixes

- Borrow selected donor-reference rows in the Assets tab instead of moving records out of the vector.
- Add command-kind coverage for the newer Paint, Transitions, and Assets editor tabs.
- Remove an unused transition-tile detail import from the game root import list.

## Notes

The remaining `haven_tools` ambiguous glob re-export warning is non-blocking and should be cleaned in a later tools-crate API pass.
