#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CreatorOptionKind {
    Body,
    Hair,
    Eyebrows,
    Torso,
    Legs,
    Footwear,
    Headwear,
    FacialHair,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct CreatorOptionMetadata {
    pub(crate) kind: CreatorOptionKind,
    pub(crate) variant: &'static str,
    pub(crate) production_asset: &'static str,
    pub(crate) starter_available: bool,
    pub(crate) allowed_bodies: &'static [&'static str],
    pub(crate) incompatible_headwear: &'static [&'static str],
}

const BOTH_BODIES: &[&str] = &["male_neutral", "female_neutral"];
const MALE_ONLY: &[&str] = &["male_neutral"];
const NO_HEADWEAR_LIMIT: &[&str] = &[];
const HOOD_BLOCKED: &[&str] = &["headwear_hood"];

pub(crate) const CREATOR_OPTIONS: &[CreatorOptionMetadata] = &[
    option(
        CreatorOptionKind::Body,
        "male_neutral",
        "body_male",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Body,
        "female_neutral",
        "body_female",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_01_page",
        "hair_medium_01_page",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_02_curly",
        "hair_medium_02_curly",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_03_idol",
        "hair_medium_03_idol",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_04_bangs_bun",
        "hair_medium_04_bangs_bun",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_05_cornrows",
        "hair_medium_05_cornrows",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_06_dreadlocks",
        "hair_medium_06_dreadlocks",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_07_bob_side_part",
        "hair_medium_07_bob_side_part",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_08_bob_bangs",
        "hair_medium_08_bob_bangs",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_09_twists",
        "hair_medium_09_twists",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_medium_10_twists_fade",
        "hair_medium_10_twists_fade",
        true,
        BOTH_BODIES,
        HOOD_BLOCKED,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_01_buzzcut",
        "hair_short_01_buzzcut",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_02_parted",
        "hair_short_02_parted",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_03_curly",
        "hair_short_03_curly",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_04_cowlick",
        "hair_short_04_cowlick",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_05_natural",
        "hair_short_05_natural",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_06_balding",
        "hair_short_06_balding",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_07_flat_top",
        "hair_short_07_flat_top",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Hair,
        "hair_short_08_flat_top_fade",
        "hair_short_08_flat_top_fade",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Eyebrows,
        "eyebrows_01_thin",
        "eyebrows_01_thin",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Eyebrows,
        "eyebrows_02_thick",
        "eyebrows_02_thick",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Torso,
        "starter_tshirt",
        "torso_tshirt",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Torso,
        "starter_tunic",
        "torso_tunic",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Torso,
        "starter_vest",
        "torso_vest",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Legs,
        "starter_pants",
        "legs_pants",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Legs,
        "starter_skirt",
        "legs_skirt",
        true,
        &["female_neutral"],
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Legs,
        "starter_shorts",
        "legs_shorts",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Footwear,
        "starter_boots",
        "feet_boots",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Footwear,
        "starter_shoes",
        "feet_shoes",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Footwear,
        "starter_sandals",
        "feet_sandals",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Footwear,
        "none",
        "none",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Headwear,
        "none",
        "none",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::Headwear,
        "headwear_hat",
        "headwear_hat",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "none",
        "none",
        true,
        BOTH_BODIES,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_01_walrus_mustache",
        "facial_hair_01_walrus_mustache",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_02_chevron_mustache",
        "facial_hair_02_chevron_mustache",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_03_handlebar_mustache",
        "facial_hair_03_handlebar_mustache",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_04_lampshade_mustache",
        "facial_hair_04_lampshade_mustache",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_05_horseshoe_mustache",
        "facial_hair_05_horseshoe_mustache",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_06_trimmed_beard",
        "facial_hair_06_trimmed_beard",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
    option(
        CreatorOptionKind::FacialHair,
        "facial_hair_07_medium_beard",
        "facial_hair_07_medium_beard",
        true,
        MALE_ONLY,
        NO_HEADWEAR_LIMIT,
    ),
];

const fn option(
    kind: CreatorOptionKind,
    variant: &'static str,
    production_asset: &'static str,
    starter_available: bool,
    allowed_bodies: &'static [&'static str],
    incompatible_headwear: &'static [&'static str],
) -> CreatorOptionMetadata {
    CreatorOptionMetadata {
        kind,
        variant,
        production_asset,
        starter_available,
        allowed_bodies,
        incompatible_headwear,
    }
}

pub(crate) fn is_compatible(
    kind: CreatorOptionKind,
    variant: &str,
    body: &str,
    headwear: &str,
) -> bool {
    CREATOR_OPTIONS
        .iter()
        .find(|entry| entry.kind == kind && entry.variant == variant)
        .is_some_and(|entry| {
            entry.starter_available
                && entry.allowed_bodies.contains(&body)
                && !entry.incompatible_headwear.contains(&headwear)
        })
}

pub(crate) fn production_asset(kind: CreatorOptionKind, variant: &str) -> Option<&'static str> {
    CREATOR_OPTIONS
        .iter()
        .find(|entry| entry.kind == kind && entry.variant == variant)
        .map(|entry| entry.production_asset)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hood_rejects_long_hair_from_metadata() {
        assert!(!is_compatible(
            CreatorOptionKind::Hair,
            "hair_medium_01_page",
            "female_neutral",
            "headwear_hood"
        ));
    }

    #[test]
    fn beard_is_male_only_from_metadata() {
        assert!(is_compatible(
            CreatorOptionKind::FacialHair,
            "facial_hair_06_trimmed_beard",
            "male_neutral",
            "none"
        ));
        assert!(!is_compatible(
            CreatorOptionKind::FacialHair,
            "facial_hair_06_trimmed_beard",
            "female_neutral",
            "none"
        ));
    }
}
