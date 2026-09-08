use serde::{Deserialize, Serialize};

pub const ENVIRONMENT_SYSTEM_SCHEMA: &str = "havenwild.environment_system.v0_1";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EnvironmentKind {
    Outdoor,
    Interior,
    Cave,
    Underground,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum WeatherKind {
    Clear,
    PartlyCloudy,
    Cloudy,
    LightRain,
    Rain,
    HeavyRain,
    Thunderstorm,
    Fog,
    Wind,
    LightSnow,
    Snow,
    Blizzard,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AtmosphereKind {
    Clear,
    MorningMist,
    CoastalHaze,
    MountainFog,
    SwampMist,
    CaveDust,
    Smoke,
    SnowHaze,
    StormHaze,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TimeOfDayStage {
    pub name: String,
    /// Minute of day, 0..1439.
    pub minute: u16,
    pub ambient_percent: u8,
    pub shadow_percent: u8,
    pub tint_rgba: [u8; 4],
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct TimeOfDayProfile {
    pub stable_id: String,
    pub stages: Vec<TimeOfDayStage>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct LightEmitterProfile {
    pub stable_id: String,
    pub radius_tiles: f32,
    pub intensity_percent: u8,
    pub tint_rgba: [u8; 4],
    pub soft_falloff: bool,
    pub casts_shadows: bool,
    pub night_only: bool,
    pub flicker_profile: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct AtmosphereProfile {
    pub stable_id: String,
    pub kind: AtmosphereKind,
    pub density_percent: u8,
    pub tint_rgba: [u8; 4],
    pub soft_edge_tiles: u8,
    pub low_lying: bool,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct WeatherProfile {
    pub stable_id: String,
    pub kind: WeatherKind,
    pub precipitation_percent: u8,
    pub cloud_cover_percent: u8,
    pub wind_percent: u8,
    pub ambient_light_modifier_percent: i8,
    pub atmosphere_profile: Option<String>,
    pub ambience_sound: Option<String>,
    pub lightning_enabled: bool,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EnvironmentProfile {
    pub schema: String,
    pub stable_id: String,
    pub kind: EnvironmentKind,
    pub time_of_day: Option<String>,
    pub base_ambient_percent: u8,
    pub weather_enabled: bool,
    pub inherited_outdoor_weather: bool,
    pub default_atmosphere: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct EnvironmentVolume {
    pub stable_id: String,
    pub profile_id: String,
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub blend_tiles: u8,
}

impl EnvironmentProfile {
    pub fn validate(&self) -> Result<(), String> {
        if self.schema != ENVIRONMENT_SYSTEM_SCHEMA {
            return Err(format!("unsupported environment schema {}", self.schema));
        }
        if self.stable_id.trim().is_empty() {
            return Err("environment stable_id is empty".to_string());
        }
        if self.base_ambient_percent > 100 {
            return Err("base ambient must be 0..100".to_string());
        }
        if self.kind == EnvironmentKind::Cave && self.inherited_outdoor_weather {
            return Err("cave environment cannot inherit outdoor precipitation".to_string());
        }
        Ok(())
    }
}

impl TimeOfDayProfile {
    pub fn validate(&self) -> Result<(), String> {
        if self.stages.is_empty() {
            return Err("time-of-day profile requires at least one stage".to_string());
        }
        let mut last = None;
        for stage in &self.stages {
            if stage.minute >= 1440 { return Err("time-of-day stage minute must be < 1440".to_string()); }
            if stage.ambient_percent > 100 || stage.shadow_percent > 100 {
                return Err("time-of-day percentages must be 0..100".to_string());
            }
            if last.is_some_and(|value| stage.minute <= value) {
                return Err("time-of-day stages must be strictly ordered".to_string());
            }
            last = Some(stage.minute);
        }
        Ok(())
    }
}

impl WeatherProfile {
    pub fn validate(&self) -> Result<(), String> {
        if self.stable_id.trim().is_empty() { return Err("weather stable_id is empty".to_string()); }
        if self.precipitation_percent > 100 || self.cloud_cover_percent > 100 || self.wind_percent > 100 {
            return Err("weather percentages must be 0..100".to_string());
        }
        Ok(())
    }
}

impl AtmosphereProfile {
    pub fn validate(&self) -> Result<(), String> {
        if self.stable_id.trim().is_empty() { return Err("atmosphere stable_id is empty".to_string()); }
        if self.density_percent > 100 { return Err("atmosphere density must be 0..100".to_string()); }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cave_profiles_reject_outdoor_weather_inheritance() {
        let profile = EnvironmentProfile {
            schema: ENVIRONMENT_SYSTEM_SCHEMA.to_string(),
            stable_id: "environment.cave".to_string(),
            kind: EnvironmentKind::Cave,
            time_of_day: None,
            base_ambient_percent: 5,
            weather_enabled: false,
            inherited_outdoor_weather: true,
            default_atmosphere: Some("atmosphere.cave_dust".to_string()),
        };
        assert!(profile.validate().is_err());
    }

    #[test]
    fn ordered_time_of_day_profile_is_valid() {
        let profile = TimeOfDayProfile {
            stable_id: "time.standard".to_string(),
            stages: vec![
                TimeOfDayStage { name: "Dawn".into(), minute: 360, ambient_percent: 45, shadow_percent: 35, tint_rgba: [220, 180, 150, 255] },
                TimeOfDayStage { name: "Day".into(), minute: 480, ambient_percent: 100, shadow_percent: 65, tint_rgba: [255, 255, 255, 255] },
                TimeOfDayStage { name: "Night".into(), minute: 1260, ambient_percent: 24, shadow_percent: 20, tint_rgba: [110, 130, 175, 255] },
            ],
        };
        assert!(profile.validate().is_ok());
    }
}
