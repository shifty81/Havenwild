use haven_save::{CharacterAppearance, CharacterAppearanceLayer, PortableAssetRef};

use crate::character_creator_catalog::{is_compatible, production_asset, CreatorOptionKind};

pub(crate) const SKIN_PALETTES: &[(&str, [u8; 4])] = &[
    ("porcelain", [244, 210, 184, 255]),
    ("warm", [218, 164, 120, 255]),
    ("golden", [196, 137, 92, 255]),
    ("copper", [174, 112, 76, 255]),
    ("umber", [135, 85, 61, 255]),
    ("deep", [104, 66, 52, 255]),
];
pub(crate) const SHIRT_PALETTES: &[(&str, [u8; 4])] = &[
    ("linen", [224, 218, 190, 255]),
    ("forest", [67, 117, 82, 255]),
    ("ocean", [65, 105, 146, 255]),
    ("berry", [137, 70, 104, 255]),
    ("rust", [154, 82, 51, 255]),
    ("violet", [101, 78, 139, 255]),
];
pub(crate) const BOTTOM_PALETTES: &[(&str, [u8; 4])] = &[
    ("charcoal", [58, 62, 69, 255]),
    ("denim", [63, 83, 116, 255]),
    ("earth", [104, 78, 57, 255]),
    ("moss", [72, 94, 63, 255]),
    ("wine", [111, 55, 67, 255]),
    ("sand", [151, 128, 94, 255]),
];
pub(crate) const HAIR_PALETTES: &[(&str, [u8; 4])] = &[
    ("brown", [95, 55, 38, 255]),
    ("black", [38, 34, 35, 255]),
    ("blonde", [205, 172, 94, 255]),
    ("red", [145, 63, 42, 255]),
    ("silver", [171, 176, 181, 255]),
    ("auburn", [113, 52, 31, 255]),
];
pub(crate) const EYE_PALETTES: &[(&str, [u8; 4])] = &[
    ("brown", [83, 58, 42, 255]),
    ("blue", [71, 123, 157, 255]),
    ("green", [72, 126, 91, 255]),
    ("gray", [126, 136, 145, 255]),
    ("hazel", [128, 103, 57, 255]),
];
pub(crate) const FOOTWEAR_PALETTES: &[(&str, [u8; 4])] = &[
    ("brown", [91, 60, 39, 255]),
    ("black", [39, 41, 45, 255]),
    ("tan", [142, 103, 67, 255]),
    ("red", [119, 55, 49, 255]),
];

macro_rules! cycle_enum {
    ($name:ident { $($variant:ident => ($label:expr, $id:expr)),+ $(,)? }) => {
        #[derive(Clone, Copy, Debug, PartialEq, Eq)] pub(crate) enum $name { $($variant),+ }
        impl $name {
            pub(crate) const ALL: &'static [Self] = &[$(Self::$variant),+];
            pub(crate) fn label(self) -> &'static str { match self { $(Self::$variant => $label),+ } }
            pub(crate) fn variant(self) -> &'static str { match self { $(Self::$variant => $id),+ } }
            pub(crate) fn cycle(self, delta: isize) -> Self {
                let index = Self::ALL.iter().position(|item| *item == self).unwrap_or(0);
                Self::ALL[cycle(index, Self::ALL.len(), delta)]
            }
            fn from_variant(value: Option<&str>) -> Self {
                Self::ALL.iter().copied().find(|item| Some(item.variant()) == value).unwrap_or(Self::ALL[0])
            }
        }
    };
}

cycle_enum!(BodyKind { Male => ("Male", "male_neutral"), Female => ("Female", "female_neutral") });
cycle_enum!(HairKind {
    MediumPage => ("Medium 01 - Page", "hair_medium_01_page"),
    MediumCurly => ("Medium 02 - Curly", "hair_medium_02_curly"),
    MediumIdol => ("Medium 03 - Idol", "hair_medium_03_idol"),
    MediumBangsBun => ("Medium 04 - Bangs & Bun", "hair_medium_04_bangs_bun"),
    MediumCornrows => ("Medium 05 - Cornrows", "hair_medium_05_cornrows"),
    MediumDreadlocks => ("Medium 06 - Dreadlocks", "hair_medium_06_dreadlocks"),
    MediumBobSidePart => ("Medium 07 - Bob, Side Part", "hair_medium_07_bob_side_part"),
    MediumBobBangs => ("Medium 08 - Bob, Bangs", "hair_medium_08_bob_bangs"),
    MediumTwists => ("Medium 09 - Twists", "hair_medium_09_twists"),
    MediumTwistsFade => ("Medium 10 - Twists, Fade", "hair_medium_10_twists_fade"),
    ShortBuzzcut => ("Short 01 - Buzzcut", "hair_short_01_buzzcut"),
    ShortParted => ("Short 02 - Parted", "hair_short_02_parted"),
    ShortCurly => ("Short 03 - Curly", "hair_short_03_curly"),
    ShortCowlick => ("Short 04 - Cowlick", "hair_short_04_cowlick"),
    ShortNatural => ("Short 05 - Natural", "hair_short_05_natural"),
    ShortBalding => ("Short 06 - Balding", "hair_short_06_balding"),
    ShortFlatTop => ("Short 07 - Flat Top", "hair_short_07_flat_top"),
    ShortFlatTopFade => ("Short 08 - Flat Top, Fade", "hair_short_08_flat_top_fade")
});
cycle_enum!(EyebrowKind {
    Thin => ("Eyebrows 01 - Thin Eyebrows", "eyebrows_01_thin"),
    Thick => ("Eyebrows 02 - Thick Eyebrows", "eyebrows_02_thick")
});
cycle_enum!(TorsoKind {
    Tee => ("T-shirt", "starter_tshirt"),
    Tunic => ("Tunic", "starter_tunic"),
    Vest => ("Vest", "starter_vest")
});
cycle_enum!(LegKind {
    Pants => ("Pants", "starter_pants"),
    Shorts => ("Shorts", "starter_shorts"),
    Skirt => ("Skirt", "starter_skirt")
});
cycle_enum!(FootwearKind {
    Boots => ("Boots", "starter_boots"), Shoes => ("Shoes", "starter_shoes"),
    Sandals => ("Sandals", "starter_sandals"), Barefoot => ("Barefoot", "none")
});
cycle_enum!(HeadwearKind {
    None => ("None", "none"), Hat => ("Simple hat", "headwear_hat")
});
cycle_enum!(FacialHairKind {
    None => ("None", "none"),
    WalrusMustache => ("Facial Hair 01 - Walrus Mustache", "facial_hair_01_walrus_mustache"),
    ChevronMustache => ("Facial Hair 02 - Chevron Mustache", "facial_hair_02_chevron_mustache"),
    HandlebarMustache => ("Facial Hair 03 - Handlebar Mustache", "facial_hair_03_handlebar_mustache"),
    LampshadeMustache => ("Facial Hair 04 - Lampshade Mustache", "facial_hair_04_lampshade_mustache"),
    HorseshoeMustache => ("Facial Hair 05 - Horseshoe Mustache", "facial_hair_05_horseshoe_mustache"),
    TrimmedBeard => ("Facial Hair 06 - Trimmed Beard", "facial_hair_06_trimmed_beard"),
    MediumBeard => ("Facial Hair 07 - Medium Beard", "facial_hair_07_medium_beard")
});
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PreviewFacing {
    North,
    West,
    South,
    East,
}

impl PreviewFacing {
    pub(crate) const ALL: &'static [Self] = &[Self::North, Self::West, Self::South, Self::East];

    pub(crate) fn variant(self) -> &'static str {
        match self {
            Self::North => "north",
            Self::West => "west",
            Self::South => "south",
            Self::East => "east",
        }
    }

    pub(crate) fn cycle(self, delta: isize) -> Self {
        let index = Self::ALL.iter().position(|item| *item == self).unwrap_or(0);
        Self::ALL[cycle(index, Self::ALL.len(), delta)]
    }
}

#[derive(Clone, Debug)]
pub(crate) struct StarterCreatorSelection {
    pub(crate) body: BodyKind,
    pub(crate) hair: HairKind,
    pub(crate) eyebrows: EyebrowKind,
    pub(crate) torso: TorsoKind,
    pub(crate) legs: LegKind,
    pub(crate) footwear: FootwearKind,
    pub(crate) headwear: HeadwearKind,
    pub(crate) facial_hair: FacialHairKind,
    pub(crate) preview_facing: PreviewFacing,
    pub(crate) preview_walking: bool,
    pub(crate) skin_index: usize,
    pub(crate) eye_index: usize,
    pub(crate) shirt_index: usize,
    pub(crate) bottom_index: usize,
    pub(crate) footwear_index: usize,
    pub(crate) hair_index: usize,
}

impl Default for StarterCreatorSelection {
    fn default() -> Self {
        Self {
            body: BodyKind::Male,
            hair: HairKind::ShortParted,
            eyebrows: EyebrowKind::Thin,
            torso: TorsoKind::Tee,
            legs: LegKind::Pants,
            footwear: FootwearKind::Boots,
            headwear: HeadwearKind::None,
            facial_hair: FacialHairKind::None,
            preview_facing: PreviewFacing::South,
            preview_walking: false,
            skin_index: 1,
            eye_index: 0,
            shirt_index: 1,
            bottom_index: 0,
            footwear_index: 0,
            hair_index: 0,
        }
    }
}

impl StarterCreatorSelection {
    pub(crate) fn from_appearance(appearance: &CharacterAppearance) -> Self {
        let mut value = Self {
            body: BodyKind::from_variant(variant(appearance, "body/base")),
            hair: HairKind::from_variant(variant(appearance, "hair")),
            eyebrows: EyebrowKind::from_variant(variant(appearance, "face/eyebrows")),
            torso: TorsoKind::from_variant(variant(appearance, "clothing/torso")),
            legs: LegKind::from_variant(variant(appearance, "clothing/legs")),
            footwear: FootwearKind::from_variant(variant(appearance, "clothing/feet")),
            headwear: HeadwearKind::from_variant(variant(appearance, "headwear")),
            facial_hair: FacialHairKind::from_variant(variant(appearance, "face/facial_hair")),
            skin_index: palette_index(appearance, "body/base", SKIN_PALETTES),
            eye_index: palette_index(appearance, "face/eyes", EYE_PALETTES),
            shirt_index: palette_index(appearance, "clothing/torso", SHIRT_PALETTES),
            bottom_index: palette_index(appearance, "clothing/legs", BOTTOM_PALETTES),
            footwear_index: palette_index(appearance, "clothing/feet", FOOTWEAR_PALETTES),
            hair_index: palette_index(appearance, "hair", HAIR_PALETTES),
            ..Self::default()
        };
        value.normalize_compatibility();
        value
    }

    pub(crate) fn appearance(&self) -> CharacterAppearance {
        let mut layers = vec![
            layer(
                "body/base",
                "character",
                "neutral_base_body",
                self.body.variant(),
                SKIN_PALETTES[self.skin_index],
            ),
            layer(
                "face/eyes",
                "character",
                "starter_eyes",
                "eyes",
                EYE_PALETTES[self.eye_index],
            ),
            layer(
                "face/eyebrows",
                "character",
                "starter_eyebrows",
                self.eyebrows.variant(),
                HAIR_PALETTES[self.hair_index],
            ),
            layer(
                "clothing/torso",
                "clothing",
                "starter_top",
                self.torso.variant(),
                SHIRT_PALETTES[self.shirt_index],
            ),
            layer(
                "clothing/legs",
                "clothing",
                "starter_bottom",
                self.legs.variant(),
                BOTTOM_PALETTES[self.bottom_index],
            ),
            layer(
                "hair",
                "character",
                "starter_hair",
                self.hair.variant(),
                HAIR_PALETTES[self.hair_index],
            ),
        ];
        if self.footwear != FootwearKind::Barefoot {
            layers.push(layer(
                "clothing/feet",
                "clothing",
                "starter_footwear",
                self.footwear.variant(),
                FOOTWEAR_PALETTES[self.footwear_index],
            ));
        }
        if self.facial_hair != FacialHairKind::None {
            layers.push(layer(
                "face/facial_hair",
                "character",
                "starter_facial_hair",
                self.facial_hair.variant(),
                HAIR_PALETTES[self.hair_index],
            ));
        }
        if self.headwear != HeadwearKind::None {
            layers.push(layer(
                "headwear",
                "clothing",
                "starter_headwear",
                self.headwear.variant(),
                ("default", [255, 255, 255, 255]),
            ));
        }
        CharacterAppearance {
            body_profile: "lpc.standard.64x64.modular".to_string(),
            animation_profile: "lpc.four_direction.walk".to_string(),
            portrait_profile: "lpc.generated".to_string(),
            layers,
        }
    }

    pub(crate) fn normalize_compatibility(&mut self) {
        let body = self.body.variant();
        let headwear = self.headwear.variant();
        if !is_compatible(CreatorOptionKind::Legs, self.legs.variant(), body, headwear) {
            self.legs = LegKind::Pants;
        }
        // Keep the selected hairstyle in the saved appearance. Headwear metadata decides
        // whether the hair layer is visible so removing a hood restores the same style.
        if !is_compatible(
            CreatorOptionKind::FacialHair,
            self.facial_hair.variant(),
            body,
            headwear,
        ) {
            self.facial_hair = FacialHairKind::None;
        }
    }

    pub(crate) fn compatibility_notes(&self) -> Vec<&'static str> {
        let mut notes = Vec::new();
        if self.body == BodyKind::Female {
            notes.push("Facial hair is unavailable for this body preset");
        }
        notes
    }

    pub(crate) fn cycle_skin(&mut self, d: isize) {
        self.skin_index = cycle(self.skin_index, SKIN_PALETTES.len(), d);
    }
    pub(crate) fn cycle_eyes(&mut self, d: isize) {
        self.eye_index = cycle(self.eye_index, EYE_PALETTES.len(), d);
    }
    pub(crate) fn cycle_shirt(&mut self, d: isize) {
        self.shirt_index = cycle(self.shirt_index, SHIRT_PALETTES.len(), d);
    }
    pub(crate) fn cycle_bottom(&mut self, d: isize) {
        self.bottom_index = cycle(self.bottom_index, BOTTOM_PALETTES.len(), d);
    }
    pub(crate) fn cycle_footwear(&mut self, d: isize) {
        self.footwear_index = cycle(self.footwear_index, FOOTWEAR_PALETTES.len(), d);
    }
    pub(crate) fn cycle_hair_color(&mut self, d: isize) {
        self.hair_index = cycle(self.hair_index, HAIR_PALETTES.len(), d);
    }
}

pub(crate) fn migrate_legacy_appearance(
    appearance: &CharacterAppearance,
) -> Option<CharacterAppearance> {
    let legacy_profile = appearance.body_profile == "lpc.standard"
        || appearance.body_profile == "lpc.standard.64x64.modular"
        || appearance.layers.iter().any(|layer| {
            layer.asset.asset_id == "neutral_base_body" && layer.asset.variant_id.is_none()
        });
    if !legacy_profile {
        return None;
    }
    let migrated = StarterCreatorSelection::from_appearance(appearance).appearance();
    (migrated != *appearance).then_some(migrated)
}

pub(crate) fn appearance_diagnostics(appearance: &CharacterAppearance) -> Vec<String> {
    let required = [
        (CreatorOptionKind::Body, "body/base"),
        (CreatorOptionKind::Torso, "clothing/torso"),
        (CreatorOptionKind::Legs, "clothing/legs"),
        (CreatorOptionKind::Hair, "hair"),
    ];
    let mut diagnostics = Vec::new();
    for (kind, slot) in required {
        let variant = variant(appearance, slot).unwrap_or("missing");
        let state = production_asset(kind, variant).map_or("unresolved", |_| "resolved");
        diagnostics.push(format!("{slot}: {state}"));
    }
    if let Some(feet) = variant(appearance, "clothing/feet") {
        let state = production_asset(CreatorOptionKind::Footwear, feet)
            .map_or("unresolved", |_| "resolved");
        diagnostics.push(format!("clothing/feet: {state}"));
    }
    diagnostics
}

fn cycle(index: usize, len: usize, delta: isize) -> usize {
    ((index as isize + delta).rem_euclid(len as isize)) as usize
}
fn variant<'a>(appearance: &'a CharacterAppearance, slot: &str) -> Option<&'a str> {
    appearance
        .layers
        .iter()
        .find(|layer| layer.slot == slot && layer.enabled)
        .and_then(|layer| layer.asset.variant_id.as_deref())
}
fn palette_index(
    appearance: &CharacterAppearance,
    slot: &str,
    values: &[(&str, [u8; 4])],
) -> usize {
    appearance
        .layers
        .iter()
        .find(|layer| layer.slot == slot)
        .and_then(|layer| layer.palette_id.as_deref())
        .and_then(|id| values.iter().position(|value| value.0 == id))
        .unwrap_or(0)
}
fn layer(
    slot: &str,
    category: &str,
    asset_id: &str,
    variant: &str,
    palette: (&str, [u8; 4]),
) -> CharacterAppearanceLayer {
    CharacterAppearanceLayer {
        slot: slot.to_string(),
        asset: PortableAssetRef {
            pack_id: "havenwild_starter_character".to_string(),
            category: category.to_string(),
            asset_id: asset_id.to_string(),
            source_id: "havenwild_authored".to_string(),
            variant_id: Some(variant.to_string()),
        },
        palette_id: Some(palette.0.to_string()),
        tint_rgba: Some(palette.1),
        enabled: true,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn expanded_creator_round_trips_variants() {
        let selection = StarterCreatorSelection {
            body: BodyKind::Female,
            hair: HairKind::MediumCurly,
            torso: TorsoKind::Tunic,
            legs: LegKind::Skirt,
            footwear: FootwearKind::Sandals,
            headwear: HeadwearKind::Hat,
            ..Default::default()
        };
        let restored = StarterCreatorSelection::from_appearance(&selection.appearance());
        assert_eq!(restored.hair, HairKind::MediumCurly);
        assert_eq!(restored.torso, TorsoKind::Tunic);
        assert_eq!(restored.legs, LegKind::Skirt);
    }
    #[test]
    fn compatibility_removes_facial_hair_from_female_body() {
        let mut selection = StarterCreatorSelection {
            body: BodyKind::Female,
            facial_hair: FacialHairKind::TrimmedBeard,
            ..Default::default()
        };
        selection.normalize_compatibility();
        assert_eq!(selection.facial_hair, FacialHairKind::None);
    }
    #[test]
    fn palette_cycles_wrap() {
        let mut selection = StarterCreatorSelection {
            skin_index: 0,
            ..Default::default()
        };
        selection.cycle_skin(-1);
        assert_eq!(selection.skin_index, SKIN_PALETTES.len() - 1);
    }
    #[test]
    fn legacy_profile_migrates_to_current_modular_contract() {
        let mut appearance = StarterCreatorSelection::default().appearance();
        appearance.body_profile = "lpc.standard".to_string();
        let migrated =
            migrate_legacy_appearance(&appearance).expect("legacy appearance should migrate");
        assert_eq!(migrated.body_profile, "lpc.standard.64x64.modular");
    }
    #[test]
    fn diagnostics_resolve_default_production_layers() {
        let diagnostics = appearance_diagnostics(&StarterCreatorSelection::default().appearance());
        assert!(diagnostics.iter().all(|line| line.ends_with("resolved")));
    }
}
