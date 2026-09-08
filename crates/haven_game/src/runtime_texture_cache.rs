use std::collections::HashMap;
use std::path::{Path, PathBuf};

use haven_assets::{
    asset_pack::{AssetCategory, StableAssetRef},
    runtime_asset_cache::{ResolvedAssetSource, RuntimeAssetSession},
    semantic_asset_resolution::AssetResolutionContext,
};
use haven_render::load_nearest_texture;
use macroquad::prelude::Texture2D;

#[derive(Clone, Debug)]
pub(crate) struct LegacyTextureFallback {
    pub semantic_id: String,
    pub fallback_path: PathBuf,
}

#[derive(Default)]
pub(crate) struct StableTextureCache {
    by_asset: HashMap<StableAssetRef, Texture2D>,
    by_source_path: HashMap<PathBuf, Texture2D>,
    fallbacks: Vec<LegacyTextureFallback>,
}

impl StableTextureCache {
    pub(crate) async fn load_semantic(
        &mut self,
        session: Option<&RuntimeAssetSession>,
        semantic_id: &str,
        category: AssetCategory,
        fallback_path: impl AsRef<Path>,
    ) -> Option<Texture2D> {
        if let Some(source) = session.and_then(|session| {
            session.resolve_source(semantic_id, category, AssetResolutionContext::default())
        }) {
            return self.load_stable_source(source).await;
        }

        let fallback_path = fallback_path.as_ref().to_path_buf();
        println!(
            "No stable provider for {semantic_id}; using legacy path {}",
            fallback_path.display()
        );
        self.fallbacks.push(LegacyTextureFallback {
            semantic_id: semantic_id.to_string(),
            fallback_path: fallback_path.clone(),
        });
        self.load_path(&fallback_path).await
    }

    pub(crate) async fn load_path(&mut self, path: impl AsRef<Path>) -> Option<Texture2D> {
        let path = normalize_cache_path(path.as_ref());
        if let Some(texture) = self.by_source_path.get(&path) {
            return Some(texture.clone());
        }
        let path_text = path.to_string_lossy().into_owned();
        let texture = load_nearest_texture(&path_text).await?;
        self.by_source_path.insert(path, texture.clone());
        Some(texture)
    }

    pub(crate) async fn load_stable_ref(
        &mut self,
        session: Option<&RuntimeAssetSession>,
        stable_ref: &StableAssetRef,
    ) -> Option<Texture2D> {
        let source = session?.source_for_ref(stable_ref)?;
        self.load_stable_source(source).await
    }

    async fn load_stable_source(&mut self, source: &ResolvedAssetSource) -> Option<Texture2D> {
        if let Some(texture) = self.by_asset.get(&source.stable_ref) {
            return Some(texture.clone());
        }

        let path = normalize_cache_path(&source.source_path);
        let texture = if let Some(texture) = self.by_source_path.get(&path) {
            texture.clone()
        } else {
            let path_text = path.to_string_lossy().into_owned();
            let loaded = load_nearest_texture(&path_text).await?;
            self.by_source_path.insert(path, loaded.clone());
            loaded
        };
        self.by_asset
            .insert(source.stable_ref.clone(), texture.clone());
        Some(texture)
    }

    pub(crate) fn resolved_ref(
        &self,
        session: Option<&RuntimeAssetSession>,
        semantic_id: &str,
        category: AssetCategory,
    ) -> Option<StableAssetRef> {
        session
            .and_then(|session| {
                session.resolve_source(semantic_id, category, AssetResolutionContext::default())
            })
            .map(|source| source.stable_ref.clone())
    }

    pub(crate) fn stable_binding_count(&self) -> usize {
        self.by_asset.len()
    }

    pub(crate) fn loaded_source_count(&self) -> usize {
        self.by_source_path.len()
    }

    pub(crate) fn legacy_fallbacks(&self) -> &[LegacyTextureFallback] {
        &self.fallbacks
    }
}

fn normalize_cache_path(path: &Path) -> PathBuf {
    std::fs::canonicalize(path).unwrap_or_else(|_| path.to_path_buf())
}
