//! Small Havenwild-owned ECS foundation.
//!
//! This crate deliberately provides only the runtime primitives Havenwild needs:
//! stable in-process entity IDs, typed component storage, spawn/despawn, and
//! direct typed access. Gameplay domains continue to own their component data.

use std::any::{Any, TypeId};
use std::collections::{HashMap, HashSet};
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct EntityId(u64);

impl EntityId {
    pub const fn from_raw(raw: u64) -> Self {
        Self(raw)
    }

    pub const fn raw(self) -> u64 {
        self.0
    }
}

impl fmt::Display for EntityId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "entity:{}", self.0)
    }
}

trait ErasedStorage {
    fn remove_entity(&mut self, entity: EntityId);
    fn as_any(&self) -> &dyn Any;
    fn as_any_mut(&mut self) -> &mut dyn Any;
}

struct ComponentStorage<T> {
    values: HashMap<EntityId, T>,
}

impl<T> Default for ComponentStorage<T> {
    fn default() -> Self {
        Self {
            values: HashMap::new(),
        }
    }
}

impl<T: 'static> ErasedStorage for ComponentStorage<T> {
    fn remove_entity(&mut self, entity: EntityId) {
        self.values.remove(&entity);
    }

    fn as_any(&self) -> &dyn Any {
        self
    }

    fn as_any_mut(&mut self) -> &mut dyn Any {
        self
    }
}

#[derive(Default)]
pub struct EntityWorld {
    next_id: u64,
    alive: HashSet<EntityId>,
    storages: HashMap<TypeId, Box<dyn ErasedStorage>>,
}

impl EntityWorld {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn spawn(&mut self) -> EntityId {
        self.next_id = self.next_id.saturating_add(1).max(1);
        let entity = EntityId::from_raw(self.next_id);
        self.alive.insert(entity);
        entity
    }

    pub fn contains(&self, entity: EntityId) -> bool {
        self.alive.contains(&entity)
    }

    pub fn len(&self) -> usize {
        self.alive.len()
    }

    pub fn is_empty(&self) -> bool {
        self.alive.is_empty()
    }

    pub fn despawn(&mut self, entity: EntityId) -> bool {
        if !self.alive.remove(&entity) {
            return false;
        }
        for storage in self.storages.values_mut() {
            storage.remove_entity(entity);
        }
        true
    }

    pub fn insert<T: 'static>(&mut self, entity: EntityId, component: T) -> Result<Option<T>, String> {
        if !self.contains(entity) {
            return Err(format!("cannot insert component for non-live {entity}"));
        }
        let type_id = TypeId::of::<T>();
        let storage = self
            .storages
            .entry(type_id)
            .or_insert_with(|| Box::new(ComponentStorage::<T>::default()));
        let typed = storage
            .as_any_mut()
            .downcast_mut::<ComponentStorage<T>>()
            .expect("component TypeId must match its typed storage");
        Ok(typed.values.insert(entity, component))
    }

    pub fn get<T: 'static>(&self, entity: EntityId) -> Option<&T> {
        self.storages
            .get(&TypeId::of::<T>())?
            .as_any()
            .downcast_ref::<ComponentStorage<T>>()?
            .values
            .get(&entity)
    }

    pub fn get_mut<T: 'static>(&mut self, entity: EntityId) -> Option<&mut T> {
        self.storages
            .get_mut(&TypeId::of::<T>())?
            .as_any_mut()
            .downcast_mut::<ComponentStorage<T>>()?
            .values
            .get_mut(&entity)
    }

    pub fn remove<T: 'static>(&mut self, entity: EntityId) -> Option<T> {
        self.storages
            .get_mut(&TypeId::of::<T>())?
            .as_any_mut()
            .downcast_mut::<ComponentStorage<T>>()?
            .values
            .remove(&entity)
    }

    pub fn entities_with<T: 'static>(&self) -> Vec<EntityId> {
        let Some(storage) = self.storages.get(&TypeId::of::<T>()) else {
            return Vec::new();
        };
        let Some(typed) = storage.as_any().downcast_ref::<ComponentStorage<T>>() else {
            return Vec::new();
        };
        let mut entities = typed.values.keys().copied().collect::<Vec<_>>();
        entities.sort_unstable();
        entities
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Clone, Debug, PartialEq, Eq)]
    struct Name(&'static str);

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    struct Profession(&'static str);

    #[test]
    fn typed_components_can_compose_different_runtime_entities() {
        let mut world = EntityWorld::new();
        let player = world.spawn();
        let miner = world.spawn();

        world.insert(player, Name("player")).unwrap();
        world.insert(miner, Name("erin")).unwrap();
        world.insert(miner, Profession("miner")).unwrap();

        assert_eq!(world.get::<Name>(player), Some(&Name("player")));
        assert_eq!(world.get::<Profession>(player), None);
        assert_eq!(world.get::<Profession>(miner), Some(&Profession("miner")));
        assert_eq!(world.entities_with::<Name>(), vec![player, miner]);
    }

    #[test]
    fn despawn_removes_all_typed_components() {
        let mut world = EntityWorld::new();
        let entity = world.spawn();
        world.insert(entity, Name("temporary")).unwrap();
        assert!(world.despawn(entity));
        assert!(!world.contains(entity));
        assert!(world.get::<Name>(entity).is_none());
    }
}
