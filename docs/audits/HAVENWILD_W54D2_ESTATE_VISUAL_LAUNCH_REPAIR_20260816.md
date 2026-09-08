# Havenwild W54D2 — Estate Visual Launch Repair

The first Windows option-54 screenshot showed the W54B Estate-test badge over `Willowmere Outskirts — Continuous Open World Biome Slice`. This proved the launch mode was set but the intended Estate scene authority had not converged.

W54D2 introduces a dedicated six-scene Estate visual-test pack with `farmstead` as the mandatory default. The runtime rejects a launch if the Estate is not active, if the normal Willowmere open-world scene remains loaded, or if the authored Estate starter-cottage BuildingInstance is missing. This prevents a normal/open-world fallback from masquerading as the Estate test.

Normal persistent-world content rebase remains on the broader Home Island authority pack; only the isolated visual-test path uses the minimal pack.

The W53D validator no longer blocks option 58 solely because local runtime cliff helper names differ from the reference names. Cliff height remains visually uncertified until the corrected Estate launch is inspected.
