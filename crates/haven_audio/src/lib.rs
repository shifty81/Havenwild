//! Havenwild-owned audio authoring/runtime contracts.
//!
//! W62 activates Hound for deterministic WAV preview export. FunDSP, Kira,
//! CPAL, RustySynth, MIDI and realtime-ring-buffer adapters remain behind this
//! contract and can be enabled after the first green dependency gate.

use haven_identity::HavenId;
use serde::{Deserialize, Serialize};
use std::f32::consts::TAU;
use std::path::Path;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum InstrumentKind {
    Sine,
    Square,
    Triangle,
    Noise,
    Pluck,
}

impl InstrumentKind {
    pub const ALL: [Self; 5] = [Self::Sine, Self::Square, Self::Triangle, Self::Noise, Self::Pluck];

    pub fn label(self) -> &'static str {
        match self {
            Self::Sine => "Sine Synth",
            Self::Square => "Square / Pulse",
            Self::Triangle => "Triangle Synth",
            Self::Noise => "Noise / Percussion",
            Self::Pluck => "Simple Pluck",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AudioNodeKind {
    Oscillator,
    Noise,
    Envelope,
    Filter,
    Gain,
    Pan,
    Mixer,
    Delay,
    Lfo,
    MidiNote,
    Instrument,
    Output,
}

impl AudioNodeKind {
    pub fn label(self) -> &'static str {
        match self {
            Self::Oscillator => "Oscillator",
            Self::Noise => "Noise",
            Self::Envelope => "Envelope",
            Self::Filter => "Filter",
            Self::Gain => "Gain",
            Self::Pan => "Pan",
            Self::Mixer => "Mixer",
            Self::Delay => "Delay",
            Self::Lfo => "LFO",
            Self::MidiNote => "MIDI Note",
            Self::Instrument => "Instrument",
            Self::Output => "Output",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AudioNode {
    pub id: HavenId,
    pub kind: AudioNodeKind,
    pub label: String,
    pub position: [f32; 2],
}

impl AudioNode {
    pub fn new(kind: AudioNodeKind, position: [f32; 2]) -> Self {
        Self {
            id: HavenId::new("audio_node"),
            label: kind.label().to_string(),
            kind,
            position,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AudioConnection {
    pub from_node: HavenId,
    pub to_node: HavenId,
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MidiNote {
    pub note: u8,
    pub velocity: u8,
    pub start_seconds: f32,
    pub duration_seconds: f32,
}

impl MidiNote {
    pub fn frequency_hz(self) -> f32 {
        440.0 * 2.0_f32.powf((self.note as f32 - 69.0) / 12.0)
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SoundDocument {
    pub schema: String,
    pub id: HavenId,
    pub display_name: String,
    pub instrument: InstrumentKind,
    pub nodes: Vec<AudioNode>,
    pub connections: Vec<AudioConnection>,
    pub notes: Vec<MidiNote>,
    pub duration_seconds: f32,
}

impl Default for SoundDocument {
    fn default() -> Self {
        let instrument = AudioNode::new(AudioNodeKind::Instrument, [80.0, 100.0]);
        let envelope = AudioNode::new(AudioNodeKind::Envelope, [290.0, 100.0]);
        let gain = AudioNode::new(AudioNodeKind::Gain, [500.0, 100.0]);
        let output = AudioNode::new(AudioNodeKind::Output, [710.0, 100.0]);
        let connections = vec![
            AudioConnection { from_node: instrument.id.clone(), to_node: envelope.id.clone() },
            AudioConnection { from_node: envelope.id.clone(), to_node: gain.id.clone() },
            AudioConnection { from_node: gain.id.clone(), to_node: output.id.clone() },
        ];
        Self {
            schema: "havenwild.sound_document.v1".to_string(),
            id: HavenId::new("sound_document"),
            display_name: "New Procedural Sound".to_string(),
            instrument: InstrumentKind::Sine,
            nodes: vec![instrument, envelope, gain, output],
            connections,
            notes: vec![MidiNote { note: 60, velocity: 112, start_seconds: 0.0, duration_seconds: 0.35 }],
            duration_seconds: 0.6,
        }
    }
}

impl SoundDocument {
    pub fn save_to_path(&self, path: &Path) -> Result<(), String> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        let text = serde_json::to_string_pretty(self).map_err(|error| error.to_string())?;
        std::fs::write(path, format!("{text}\n")).map_err(|error| error.to_string())
    }

    pub fn validate(&self) -> Vec<String> {
        let mut issues = Vec::new();
        if !self.nodes.iter().any(|node| node.kind == AudioNodeKind::Output) {
            issues.push("Audio graph has no Output node".to_string());
        }
        if self.duration_seconds <= 0.0 {
            issues.push("Sound duration must be greater than zero".to_string());
        }
        for connection in &self.connections {
            if !self.nodes.iter().any(|node| node.id == connection.from_node) {
                issues.push(format!("Connection source {} is missing", connection.from_node));
            }
            if !self.nodes.iter().any(|node| node.id == connection.to_node) {
                issues.push(format!("Connection target {} is missing", connection.to_node));
            }
        }
        issues
    }

    pub fn render_preview_wav(&self, path: &Path) -> Result<(), String> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        let sample_rate = 44_100_u32;
        let spec = hound::WavSpec {
            channels: 1,
            sample_rate,
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        };
        let mut writer = hound::WavWriter::create(path, spec).map_err(|error| error.to_string())?;
        let sample_count = (self.duration_seconds.max(0.05) * sample_rate as f32).ceil() as usize;
        let mut noise_state = 0x1234_5678_u32;
        for sample_index in 0..sample_count {
            let time = sample_index as f32 / sample_rate as f32;
            let mut value = 0.0_f32;
            for note in &self.notes {
                if time < note.start_seconds || time >= note.start_seconds + note.duration_seconds {
                    continue;
                }
                let local = time - note.start_seconds;
                let phase = local * note.frequency_hz();
                let envelope = envelope(local, note.duration_seconds);
                let velocity = note.velocity as f32 / 127.0;
                value += oscillator(self.instrument, phase, local, &mut noise_state) * envelope * velocity * 0.28;
            }
            let sample = (value.clamp(-1.0, 1.0) * i16::MAX as f32) as i16;
            writer.write_sample(sample).map_err(|error| error.to_string())?;
        }
        writer.finalize().map_err(|error| error.to_string())
    }
}

fn envelope(time: f32, duration: f32) -> f32 {
    let attack = 0.02_f32.min(duration * 0.25);
    let release = 0.08_f32.min(duration * 0.35);
    let attack_gain = if attack > 0.0 { (time / attack).clamp(0.0, 1.0) } else { 1.0 };
    let release_start = (duration - release).max(0.0);
    let release_gain = if time > release_start && release > 0.0 {
        ((duration - time) / release).clamp(0.0, 1.0)
    } else {
        1.0
    };
    attack_gain * release_gain
}

fn oscillator(kind: InstrumentKind, phase: f32, local_time: f32, noise_state: &mut u32) -> f32 {
    let fractional = phase.fract();
    match kind {
        InstrumentKind::Sine => (phase * TAU).sin(),
        InstrumentKind::Square => if fractional < 0.5 { 1.0 } else { -1.0 },
        InstrumentKind::Triangle => 1.0 - 4.0 * (fractional - 0.5).abs(),
        InstrumentKind::Noise => {
            *noise_state = noise_state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
            ((*noise_state >> 8) as f32 / 16_777_215.0) * 2.0 - 1.0
        }
        InstrumentKind::Pluck => {
            let harmonic = (phase * TAU).sin() * 0.72 + (phase * TAU * 2.0).sin() * 0.28;
            harmonic * (-6.0 * local_time).exp()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn starter_graph_is_valid() {
        assert!(SoundDocument::default().validate().is_empty());
    }

    #[test]
    fn middle_c_is_in_expected_range() {
        let note = MidiNote { note: 60, velocity: 100, start_seconds: 0.0, duration_seconds: 1.0 };
        assert!((note.frequency_hz() - 261.63).abs() < 0.2);
    }
}
