#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub enum PieMode { Edit, Play, Pause, Step, Stop }

#[derive(Debug,Clone,PartialEq,Eq)]
pub struct AuthoredChange { pub identity:String, pub field:String, pub before:String, pub after:String }

#[derive(Debug,Clone)]
pub struct PieSession {
    pub mode: PieMode,
    pub baseline_revision: u64,
    pub authored_changes: Vec<AuthoredChange>,
}
impl PieSession {
    pub fn new(revision:u64)->Self{Self{mode:PieMode::Edit,baseline_revision:revision,authored_changes:vec![]}}
    pub fn play(&mut self){self.mode=PieMode::Play;}
    pub fn pause(&mut self){if self.mode==PieMode::Play{self.mode=PieMode::Pause;}}
    pub fn step(&mut self)->bool{if self.mode==PieMode::Pause{self.mode=PieMode::Step;true}else{false}}
    pub fn finish_step(&mut self){if self.mode==PieMode::Step{self.mode=PieMode::Pause;}}
    pub fn stop(&mut self){self.mode=PieMode::Stop;}
    pub fn keepable_changes(&self)->&[AuthoredChange]{&self.authored_changes}
}
#[cfg(test)]
mod tests{
 use super::*;
 #[test] fn lifecycle_is_deterministic(){let mut p=PieSession::new(7);p.play();p.pause();assert!(p.step());p.finish_step();assert_eq!(p.mode,PieMode::Pause);p.stop();assert_eq!(p.mode,PieMode::Stop);}
}
