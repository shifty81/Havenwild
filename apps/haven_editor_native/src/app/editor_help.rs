use super::render_helpers::*;
use super::tool_registry::{self, ToolGroup};
use super::*;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum HelpPage {
    Welcome,
    GettingStarted,
    ProjectHome,
    Shortcuts,
    Canvas,
    DocumentTabs,
    ToolRail,
    LayerRail,
    Inspector,
    RightDock,
    UndoRedo,
    Validation,
    SettingsActivity,
    AssetBrowser,
    AssetStatus,
    AssetPromotion,
    BatchPromotion,
    WhereUsed,
    Licensing,
    WorldStudio,
    EntireWorldCanvas,
    WorldLod,
    WorldGeneration,
    RegenerationScopes,
    AuthoredOverrides,
    TerrainMaterials,
    ElevationCliffs,
    WaterHydrology,
    RoadsPaths,
    Vegetation,
    Resources,
    Structures,
    WorldNpcSpawns,
    WorldCollision,
    WorldPixelMode,
    Transitions,
    TransitionRepair,
    WorldRoutes,
    SceneStudio,
    SceneBrowser,
    SceneLayers,
    FurnitureProps,
    SceneNpcEditing,
    TriggersInteractions,
    SceneCollision,
    LightingFx,
    SoundEmitters,
    SceneLogic,
    PixelAuthoring,
    PixelDrawingTools,
    PixelSelectionTransform,
    PixelLayers,
    ColorPalette,
    PixelPublishing,
    AnimationStudio,
    FramesCels,
    TimelinePlayback,
    OnionSkin,
    AnchorsSockets,
    HitboxesHurtboxes,
    AnimationEvents,
    WorldObjectAnimation,
    CharacterStudio,
    CharacterCreate,
    WardrobeGear,
    EquipmentSlots,
    CharacterLayers,
    CharacterOcclusion,
    AnimationCoverage,
    NpcGenerator,
    NpcProfiles,
    ProfileInheritance,
    PopulationGeneration,
    LogicStudio,
    SoundStudio,
    PlayTesting,
    SaveRecovery,
    Troubleshooting,
}

#[derive(Clone, Copy)]
struct HelpArticle {
    page: HelpPage,
    title: &'static str,
    category: &'static str,
    keywords: &'static str,
    summary: &'static str,
    workflow: &'static str,
    notes: &'static str,
}

const HELP_ARTICLES: [HelpArticle; 78] = [
    HelpArticle { page: HelpPage::Welcome, title: "Help Center Index", category: "Getting Started", keywords: "help wiki index search f1 manual", summary: "The searchable Havenwild Editor manual and index. Every meaningful Studio, layer, tool, panel, workflow and production warning should resolve here.", workflow: "Search for a task or browse the category index. Use F1 from the current editor context to jump to the most relevant article.", notes: "Missing contextual documentation is treated as editor validation debt." },
    HelpArticle { page: HelpPage::GettingStarted, title: "Getting Started", category: "Getting Started", keywords: "first steps development world workflow", summary: "The normal Havenwild workflow begins with the persistent Development World and uses focused studios over shared project authorities.", workflow: "Open World Studio, frame the Development World, choose a semantic layer and compatible tool, edit, save, then open a Scene or Play From Here to test.", notes: "Opening a document never silently arms a destructive tool." },
    HelpArticle { page: HelpPage::ProjectHome, title: "Project Home & Project State", category: "Getting Started", keywords: "project home status health recent documents", summary: "Project Home summarizes the active project, recent documents, validation/build health and entry points into authoring.", workflow: "Confirm the correct project and current health, then open the Development World or a recent resource.", notes: "Project Home is a navigation/status surface, not a second editor." },
    HelpArticle { page: HelpPage::Shortcuts, title: "Keyboard Shortcuts", category: "Editor", keywords: "keyboard hotkeys controls", summary: "Global navigation and editing shortcuts are generated from the same command/tool authorities used by the UI.", workflow: "Use Ctrl+S/F5 to save, Ctrl+Z/Ctrl+Y for Undo/Redo, Space-drag to pan, mouse wheel to zoom and Escape to return to non-destructive selection.", notes: "Unavailable shortcuts fail closed for the current Studio/layer." },
    HelpArticle { page: HelpPage::Canvas, title: "Canvas Workspace", category: "Editor", keywords: "canvas infinite workspace zoom pan", summary: "All studios use the shared CanvasWorkspace shell with Tool Rail, Layers, central document canvas, Right Dock and status surfaces.", workflow: "Pan/zoom, choose the edit layer, choose an allowed tool and author directly in the current document.", notes: "Studio-specific content plugs into one workspace contract." },
    HelpArticle { page: HelpPage::DocumentTabs, title: "Document Tabs & Lifecycle", category: "Editor", keywords: "tabs close dirty save document", summary: "Document tabs represent resources governed by the universal dirty/save/close lifecycle.", workflow: "Switch tabs freely. Close clean documents immediately; dirty documents require Save, Don't Save or Cancel.", notes: "The same authority governs tab X, Ctrl+W, Close All, studio switching and shutdown." },
    HelpArticle { page: HelpPage::ToolRail, title: "Tool Rail", category: "Editor", keywords: "tools rail select paint place erase context", summary: "The Tool Rail exposes only operations applicable to the current Studio and selected semantic layer.", workflow: "Choose a semantic layer first, then select an available tool. Disabled or hidden operations are intentionally incompatible with the current target.", notes: "Selecting a layer does not automatically arm a mutating tool." },
    HelpArticle { page: HelpPage::LayerRail, title: "Layers Rail", category: "Editor", keywords: "layers semantic edit target visibility lock", summary: "The selected Layer defines the primary editable authority for the canvas. Tool Rail, Assets, Inspector, hit testing and Help follow it.", workflow: "Select the content authority you intend to edit, then choose a compatible tool and asset if needed.", notes: "Visibility is presentation; Lock prevents edits; Generated layers route to dedicated authoring." },
    HelpArticle { page: HelpPage::Inspector, title: "Inspector", category: "Editor", keywords: "inspector properties selection metadata", summary: "Inspector displays editable properties and diagnostics for the current semantic selection.", workflow: "Select a layer or object, review its authoritative properties, make supported edits and validate.", notes: "Inspector should not duplicate dedicated Studio workflows." },
    HelpArticle { page: HelpPage::RightDock, title: "Right Dock", category: "Editor", keywords: "right dock assets inspector scenes validation", summary: "The Right Dock hosts contextual views such as Assets, Inspector, Scenes and validation without creating competing authorities.", workflow: "Select a semantic layer or object; use the relevant dock tab for supporting information and actions.", notes: "Dock panels follow global selection." },
    HelpArticle { page: HelpPage::UndoRedo, title: "Undo / Redo & Transactions", category: "Editor", keywords: "undo redo transaction brush scatter regenerate", summary: "Authoring operations are transactional so one logical action can be undone safely, including cross-layer generated consequences.", workflow: "Perform an edit, use Ctrl+Z to undo and Ctrl+Y to redo. Large operations should appear as one meaningful transaction.", notes: "Failed cross-layer operations must roll back atomically rather than leave stale derived data." },
    HelpArticle { page: HelpPage::Validation, title: "Validation & Problems", category: "Editor", keywords: "validation problems warnings errors diagnostics", summary: "Validation reports ownership, binding, animation, terrain, reference, collision, licensing and document-state problems.", workflow: "Open the reported problem, follow its owning authority/help link, repair the source, validate again and retest.", notes: "Warnings should be explainable and actionable." },
    HelpArticle { page: HelpPage::SettingsActivity, title: "Settings & Activity", category: "Editor", keywords: "settings activity jobs logs progress", summary: "Settings owns user/editor configuration while Activity reports long-running operations, imports and validation progress.", workflow: "Adjust configuration in Settings; use Activity to inspect non-blocking job status and results.", notes: "Heavy indexing/generation must not freeze the UI." },
    HelpArticle { page: HelpPage::AssetBrowser, title: "Unified Asset Browser", category: "Assets", keywords: "assets browser lpc oga thumbnails search filter", summary: "The project Asset Browser exposes production-ready assets plus governed LPC/OGA source references through semantic categories and search.", workflow: "Select a semantic layer, search/filter the catalog, inspect a card, and place only production-ready assets with an explicit Place/Paint tool.", notes: "Selecting an asset is never the same as placing it." },
    HelpArticle { page: HelpPage::AssetStatus, title: "Asset Readiness States", category: "Assets", keywords: "ready partial needs binding source status", summary: "Asset cards expose where content sits in the intake pipeline: source, cleared, classified, approved, bound, partial or production ready.", workflow: "Inspect the card status before use. Route Needs Binding/Partial assets through promotion or repair.", notes: "The browser should expose useful source art without pretending it is gameplay-ready." },
    HelpArticle { page: HelpPage::AssetPromotion, title: "Promoting LPC / Source Assets", category: "Assets", keywords: "needs binding finish setup promote collision footprint", summary: "Promotion turns a reviewed source reference into a Havenwild binding with semantics, footprint/collision, interaction/animation and provenance.", workflow: "Inspect source, confirm semantic type/license, configure required binding data, validate, then promote.", notes: "Upstream source files stay read-only and are never silently moved into repository ownership." },
    HelpArticle { page: HelpPage::BatchPromotion, title: "Batch Asset Promotion", category: "Assets", keywords: "batch promote family lpc classify automate", summary: "Compatible LPC families should be promoted in batches using shared detection and rules, with exceptions routed to review.", workflow: "Select a compatible family, preview detected semantics/metadata, validate the batch, promote passing members and review exceptions.", notes: "Manual one-by-one setup is the repair path, not the normal path for tens of thousands of assets." },
    HelpArticle { page: HelpPage::WhereUsed, title: "Where Used & Asset Dependencies", category: "Assets", keywords: "where used references dependency replace deprecate", summary: "Every promoted asset can report scenes, characters, recipes, profiles and other project authorities that reference it.", workflow: "Open Where Used before replacing, deleting or deprecating an asset; review dependent resources and migrate safely.", notes: "Stable AssetId references are preferred over path/name coupling." },
    HelpArticle { page: HelpPage::Licensing, title: "LPC / OpenGameArt Licensing", category: "Assets", keywords: "license cc0 oga-by cc-by cc-by-sa gpl attribution", summary: "Havenwild records per-asset provenance and keeps third-party artwork obligations separate from proprietary code/editor licensing.", workflow: "Prefer CC0 then OGA-BY; validate CC-BY; explicitly approve CC-BY-SA; block GPL-only/NC/ND-for-derivative/unknown under current production policy.", notes: "Release outputs generate credits and notices from verified provenance." },
    HelpArticle { page: HelpPage::WorldStudio, title: "World Studio", category: "World Studio", keywords: "world editor persistent archipelago", summary: "World Studio displays and edits the actual persistent Havenwild Development World rather than a disposable preview representation.", workflow: "Frame the complete world, zoom to the desired scale, choose a semantic layer and edit the authoritative world.", notes: "Streaming/storage partitions are not separate worlds." },
    HelpArticle { page: HelpPage::EntireWorldCanvas, title: "Entire-World Canvas", category: "World Studio", keywords: "entire world archipelago overview complete world", summary: "The complete finite archipelago is visible as one World document using the finite production macro-geography authority rather than legacy Scene-rectangle silhouettes.", workflow: "Use Open Complete World to frame every landmass. Pan/zoom the real archipelago overview, then click a landmass to enter its native tile-edit view; use Open Complete World to return.", notes: "The overview samples authoritative finite-world geography; legacy Scene rectangles are authored anchor regions inside those huge landmasses, not island silhouettes. Destructive edits stay native-tile accurate after landmass focus." },
    HelpArticle { page: HelpPage::WorldLod, title: "World LOD & Edit Scale", category: "World Studio", keywords: "lod zoom edit scale macro region chunk tile pixel", summary: "World editing changes meaning by scale: macro world operations at far zoom, regional authoring closer in, detailed terrain/object editing near tile scale and raster work at pixel scale.", workflow: "Zoom to a scale appropriate for the edit type; incompatible fine-detail tools remain unavailable when too far out.", notes: "LOD must never alter authoritative world identity." },
    HelpArticle { page: HelpPage::WorldGeneration, title: "Generate Havenwild", category: "World Studio", keywords: "worldgen seed archipelago mountains rivers willowmere", summary: "The production generator composes the finite 3-15-landmass Havenwild archipelago from deterministic macro geography through hydrology, structural levels and presentation.", workflow: "Choose seed/settings, generate the actual world, review it, then accept as Development World.", notes: "Ocean is required on all four outer boundaries and Willowmere is protected as the authored capital core." },
    HelpArticle { page: HelpPage::RegenerationScopes, title: "World Regeneration Scopes", category: "World Studio", keywords: "regenerate world island region hydrology vegetation resources", summary: "Regeneration can target the entire world or a subsystem/area without destroying unrelated authored work.", workflow: "Choose Entire World, Landmass, Region, Hydrology, Vegetation, Resources or Settlements, review affected authored overrides, then regenerate.", notes: "Ambiguous/conflicting authored overrides route to review rather than being deleted." },
    HelpArticle { page: HelpPage::AuthoredOverrides, title: "Generated Base & Authored Overrides", category: "World Studio", keywords: "authored override generated base regenerate preserve", summary: "Generated world data and deliberate editor-authored changes are tracked separately so deterministic regeneration can preserve reviewed work.", workflow: "Edit the generated world normally; authored changes become explicit overrides. During regeneration, review conflicts and reapply compatible overrides.", notes: "Protected authored authorities such as Willowmere cannot be silently replaced." },
    HelpArticle { page: HelpPage::TerrainMaterials, title: "Terrain Materials", category: "World Studio", keywords: "grass dirt mud sand stone snow ice semantic paint", summary: "Terrain authoring paints semantic materials instead of individual edge/corner tile IDs.", workflow: "Select Terrain Materials, choose a material and paint. Havenwild resolves exact supported visual transitions automatically.", notes: "Unsupported tuples fail closed and route to Transition Repair." },
    HelpArticle { page: HelpPage::ElevationCliffs, title: "Elevation, Cliffs & Ramps", category: "World Studio", keywords: "elevation cliffs structural levels ramps stairs", summary: "Elevation is structural authority; cliffs/ramp faces are derived from structural boundaries rather than treated as ground materials.", workflow: "Select World Structure, edit elevation/ramps at an appropriate scale, then inspect generated cliff faces/collision.", notes: "Water crossing a real structural drop requires a waterfall." },
    HelpArticle { page: HelpPage::WaterHydrology, title: "Water, Rivers & Hydrology", category: "World Studio", keywords: "water rivers lakes ocean drainage waterfalls swim coast", summary: "Freshwater generation and editing obey downhill drainage, coast and structural-drop rules.", workflow: "Select Water, inspect or edit rivers/lakes/coast; validate outflow, waterfalls and traversal boundaries.", notes: "Freshwater may not terminate arbitrarily on land or climb uphill." },
    HelpArticle { page: HelpPage::RoadsPaths, title: "Roads & Paths", category: "World Studio", keywords: "roads paths routes surface paint", summary: "Road/path surfaces are a dedicated semantic layer connected to world routing and terrain transition presentation.", workflow: "Select Roads & Paths, author routes/surfaces, then validate terrain crossings and destination connectivity.", notes: "Route logic and visual surface remain linked but distinct." },
    HelpArticle { page: HelpPage::Vegetation, title: "Vegetation", category: "World Studio", keywords: "trees bushes flowers plants mushrooms clutter", summary: "Vegetation owns trees, bushes, flowers, plants and ground clutter independently from terrain materials.", workflow: "Select Vegetation, choose a production-ready asset or density/scatter tool and author the region.", notes: "Vegetation regeneration should not overwrite unrelated terrain/structures." },
    HelpArticle { page: HelpPage::Resources, title: "Resources & Harvestables", category: "World Studio", keywords: "rocks ore forage mining trees harvest", summary: "Resources owns mineable/harvestable world nodes and their gameplay bindings.", workflow: "Select Resources, place or generate resource families, configure harvest definitions and validate tool/drop interactions.", notes: "Visual source art alone does not imply harvestability." },
    HelpArticle { page: HelpPage::Structures, title: "Structures & Buildings", category: "World Studio", keywords: "structures buildings bridges docks walls roofs doors", summary: "Structures owns buildings, bridges, docks and structural props while their interiors/scenes remain stable linked authorities.", workflow: "Select Structures, place/edit production-ready structures and use the Scene Browser to open linked interiors.", notes: "Structural visual, collision and scene references must remain consistent." },
    HelpArticle { page: HelpPage::WorldNpcSpawns, title: "NPC & Spawn Layer", category: "World Studio", keywords: "npc spawn population settlement generation", summary: "World NPC/Spawn authoring controls population anchors, encounter/spawn regions and settlement population inputs.", workflow: "Select NPC/Spawn, place authored anchors or configure population rules, then validate profile availability and world references.", notes: "Generated NPC identity remains stable after creation." },
    HelpArticle { page: HelpPage::WorldCollision, title: "World Collision & Traversal", category: "World Studio", keywords: "collision walk wade swim blocked shoreline", summary: "Collision/traversal data defines where actors walk, wade, swim or are blocked and must match visible semantic boundaries.", workflow: "Select Collision, inspect the traversal overlay, edit supported masks/shapes and test shoreline/cliff behavior.", notes: "Do not infer shoreline collision from texture alpha." },
    HelpArticle { page: HelpPage::WorldPixelMode, title: "World Pixel Mode", category: "World Studio", keywords: "world pixel raster pencil exact artwork", summary: "World Pixel Mode uses the same RasterAuthoringCore as Pixel Studio while editing the selected world-backed raster authority in context.", workflow: "Zoom close enough, select an editable raster-backed layer, choose Pixel and author with the shared pixel tools.", notes: "Generated layers such as Derived Transitions route to their authoring resource instead of accepting destructive paint." },
    HelpArticle { page: HelpPage::Transitions, title: "Terrain Transitions", category: "World Studio", keywords: "autotile junction shoreline transition derived", summary: "Derived Transitions are generated from semantic terrain relationships and exact supported authored combinations.", workflow: "Paint semantic materials normally and inspect the resulting derived transitions.", notes: "Direct painting of generated transition output is blocked." },
    HelpArticle { page: HelpPage::TransitionRepair, title: "Repair Unsupported Transitions", category: "World Studio", keywords: "repair transition tuple pixel publish candidate", summary: "Unsupported material combinations open a dedicated layered Pixel authoring workflow rather than substituting proxy artwork.", workflow: "Select the warning, choose Repair Transition, author the exact tuple, preview in world context, publish the candidate and revalidate.", notes: "Tuple Inspector is diagnostic; normal terrain painting should not require raw tile knowledge." },
    HelpArticle { page: HelpPage::WorldRoutes, title: "World Routes & Navigation", category: "World Studio", keywords: "routes open complete world locate scene travel", summary: "World Routes provides world-level navigation and relationships without becoming a separate world authority.", workflow: "Use Open Complete World to frame all landmasses, select routes/scenes and locate authoritative content.", notes: "Routes should reference stable world/scene IDs rather than fragile display names." },
    HelpArticle { page: HelpPage::SceneStudio, title: "Scene Studio", category: "Scene Studio", keywords: "scene editor close authoring region interior cave", summary: "Scene Studio provides close authoring for stable world regions, interiors, buildings, caves and other scene authorities.", workflow: "Open a Scene from World/Scene Browser, choose a semantic layer, edit, save and return to World or Play From Here.", notes: "World-located and off-world interior scenes are both explicit." },
    HelpArticle { page: HelpPage::SceneBrowser, title: "Scene Browser", category: "Scene Studio", keywords: "scene bank browser locate world duplicate validate references", summary: "Scene Browser indexes all authoritative world scenes, interiors, buildings, caves/dungeons and generated/special scenes.", workflow: "Search/select a Scene, Open in Game Canvas, Locate in World when assigned, Duplicate, or Validate References.", notes: "It is an index over Scene authorities, not a parallel Scene Bank source of truth." },
    HelpArticle { page: HelpPage::SceneLayers, title: "Scene Layers", category: "Scene Studio", keywords: "scene layers terrain furniture props npc triggers", summary: "Scene Layers constrain editing to Terrain, Structures, Furniture, Props, NPCs, Triggers, Interactions, Collision, Lighting/FX, Sound or Logic.", workflow: "Select the intended Scene layer before choosing tools/assets.", notes: "Clicks on objects from another layer should offer a safe quick-switch rather than mutate them." },
    HelpArticle { page: HelpPage::FurnitureProps, title: "Furniture & Props", category: "Scene Studio", keywords: "furniture props tables chairs beds storage decor", summary: "Furniture and Props are separate scene-authoring contexts so object placement cannot accidentally edit terrain/structures.", workflow: "Select Furniture or Props, choose an asset and explicitly Place/Move/Delete it.", notes: "Gameplay behaviors such as storage/sitting require their own binding metadata." },
    HelpArticle { page: HelpPage::SceneNpcEditing, title: "Scene NPC Editing", category: "Scene Studio", keywords: "npc characters place edit facing interaction", summary: "Characters/NPCs layer owns authored NPC placement and scene-specific character properties.", workflow: "Select NPCs, place or select an NPC Instance, edit position/facing/scene bindings and validate its profile/identity references.", notes: "NPC visuals still resolve through shared CharacterRecipe/CharacterCompositor." },
    HelpArticle { page: HelpPage::TriggersInteractions, title: "Triggers & Interactions", category: "Scene Studio", keywords: "trigger interaction door talk harvest use regions", summary: "Triggers/Interactions bind gameplay behavior to stable scene/world entities and regions.", workflow: "Select the relevant semantic layer, create/select a trigger or interaction, bind it to stable targets and validate.", notes: "Visual objects and logic bindings remain linked but structurally separate." },
    HelpArticle { page: HelpPage::SceneCollision, title: "Scene Collision", category: "Scene Studio", keywords: "scene collision polygon mask blocking", summary: "Scene Collision provides local collision/mask authoring for interiors and authored spaces.", workflow: "Select Collision, use supported mask/shape tools, validate and Play the Scene.", notes: "Collision edits should not repaint visual artwork." },
    HelpArticle { page: HelpPage::LightingFx, title: "Lighting & FX", category: "Scene Studio", keywords: "lighting effects particles scene fx", summary: "Lighting/FX owns scene-local visual effects and light presentation.", workflow: "Select Lighting/FX, place/configure effect bindings and preview them in scene context.", notes: "The source animation/effect resource may be authored in Animation/Pixel Studio." },
    HelpArticle { page: HelpPage::SoundEmitters, title: "Sound Emitters", category: "Scene Studio", keywords: "sound emitters audio world scene spatial", summary: "Sound Emitters place/bind published Sound Studio resources in world/scene space.", workflow: "Select Sound Emitters, place/select an emitter, assign a published sound and configure spatial/event behavior.", notes: "Sound Studio owns the sound resource; Scene owns its placement/binding." },
    HelpArticle { page: HelpPage::SceneLogic, title: "Scene Logic", category: "Scene Studio", keywords: "scene logic nodes channels bindings", summary: "Scene Logic links local scene entities/regions to Logic Studio behavior without storing visual and behavior data as one blob.", workflow: "Open the layer Logic channel or Logic Studio, bind stable scene IDs, validate and test.", notes: "Broken references must be reported explicitly." },
    HelpArticle { page: HelpPage::PixelAuthoring, title: "Pixel Studio", category: "Pixel Studio", keywords: "pixel raster draw tiles sprite artwork", summary: "Pixel Studio owns direct raster authoring and supplies the shared RasterAuthoringCore used by compatible World/Scene modes.", workflow: "Open/create a raster document, select a layer and tool, edit, validate and publish/save.", notes: "World Pixel mode should behave consistently with Pixel Studio." },
    HelpArticle { page: HelpPage::PixelDrawingTools, title: "Pixel Drawing Tools", category: "Pixel Studio", keywords: "pencil eraser fill picker line rectangle ellipse", summary: "Pixel drawing tools provide direct RGBA editing with shared brush/color behavior.", workflow: "Choose Pencil/Eraser/Fill/Picker/Shape, adjust brush settings and edit the selected raster layer.", notes: "Tools must respect selection/layer bounds and Undo transactions." },
    HelpArticle { page: HelpPage::PixelSelectionTransform, title: "Pixel Selection & Transform", category: "Pixel Studio", keywords: "selection move copy paste rotate mirror transform", summary: "Selections isolate raster regions for move/copy/paste/rotate/mirror operations.", workflow: "Create a selection, transform or clipboard-edit it, commit or cancel and use Undo when needed.", notes: "Transform should be non-destructive until committed where practical." },
    HelpArticle { page: HelpPage::PixelLayers, title: "Pixel Layers", category: "Pixel Studio", keywords: "pixel layers visibility opacity nested logic", summary: "Pixel layers represent authored raster composition with semantic names and visibility/lock controls.", workflow: "Select the raster layer you intend to edit; manage visibility/order where allowed and preserve semantic names.", notes: "Generated/default layers use meaningful names rather than Layer 1/2/3." },
    HelpArticle { page: HelpPage::ColorPalette, title: "Color & Palette", category: "Pixel Studio", keywords: "color palette foreground background fg bg swatch", summary: "The shared raster palette owns foreground/background colors and project/pixel color selection.", workflow: "Left-click selects foreground; right-click selects background where supported. Use + to add/edit colors.", notes: "World Pixel uses the same color authority." },
    HelpArticle { page: HelpPage::PixelPublishing, title: "Publish Raster Assets", category: "Pixel Studio", keywords: "publish asset derived save source variant", summary: "Publishing converts an authored raster document into a governed project asset/derived source while preserving provenance and source linkage.", workflow: "Validate the raster, choose its semantic target, publish and inspect all dependent previews/usages.", notes: "Publishing should not flatten away editable source data." },
    HelpArticle { page: HelpPage::AnimationStudio, title: "Animation Studio", category: "Animation Studio", keywords: "animation clips frames events sockets hitboxes", summary: "Animation Studio uses the shared raster core plus clip/timeline/gameplay metadata authoring.", workflow: "Open an animation resource, edit frames/cels, timing and metadata, preview and publish.", notes: "Characters and world objects share the animation resource architecture but may use different clip schemas." },
    HelpArticle { page: HelpPage::FramesCels, title: "Frames & Cels", category: "Animation Studio", keywords: "frames cels animation raster", summary: "Frames/cels define the visual sequence while preserving layered/source relationships where applicable.", workflow: "Add/select frames, edit their cels with shared raster tools and keep alignment consistent.", notes: "Character equipment coverage may reference separate LPC action sheets rather than hand-authored cels." },
    HelpArticle { page: HelpPage::TimelinePlayback, title: "Timeline & Playback", category: "Animation Studio", keywords: "timeline playback fps loop tags", summary: "Timeline controls frame timing, playback, looping and clip ranges.", workflow: "Play/pause, scrub, adjust timings and test at game-relevant playback speed.", notes: "Preview timing should match runtime timing authority." },
    HelpArticle { page: HelpPage::OnionSkin, title: "Onion Skin", category: "Animation Studio", keywords: "onion skin previous next frame", summary: "Onion skin overlays neighboring frames to aid motion/alignment authoring.", workflow: "Enable onion skin, choose previous/next visibility and edit the current frame.", notes: "It is a preview aid and does not change exported pixels." },
    HelpArticle { page: HelpPage::AnchorsSockets, title: "Anchors & Sockets", category: "Animation Studio", keywords: "anchor socket attachment hand tool foot shadow", summary: "Anchors/sockets provide stable attachment points for tools, effects and other runtime presentation.", workflow: "Select the relevant metadata layer, place/adjust anchors per frame/clip and validate required sockets.", notes: "Tool held/contact presentation depends on correct anchors." },
    HelpArticle { page: HelpPage::HitboxesHurtboxes, title: "Hitboxes & Hurtboxes", category: "Animation Studio", keywords: "hitbox hurtbox combat collision frame", summary: "Hitboxes/hurtboxes describe gameplay contact regions synchronized to animation frames.", workflow: "Author shapes on the appropriate metadata layers, mark active frames and validate runtime expectations.", notes: "Visual pixels and gameplay collision metadata remain separate." },
    HelpArticle { page: HelpPage::AnimationEvents, title: "Animation Events", category: "Animation Studio", keywords: "events tool contact footstep projectile release sound", summary: "Frame events synchronize gameplay/audio/FX with animation such as ToolContact, Footstep, ProjectileRelease and impacts.", workflow: "Place events on exact frames, configure payload/bindings and validate required events for gameplay actions.", notes: "An animation can have visual coverage yet still be gameplay-incomplete if required events are absent." },
    HelpArticle { page: HelpPage::WorldObjectAnimation, title: "World Object Animation", category: "Animation Studio", keywords: "tree fall ore crack door object resource animation", summary: "Animation Studio also authors non-character clips such as tree hit/fall, ore crack/break, doors and environmental objects.", workflow: "Open the world-object animation, author frames/events/collision-release cues and bind it through the object definition.", notes: "Do not build a character-only animation pipeline." },
    HelpArticle { page: HelpPage::CharacterStudio, title: "Character Studio", category: "Character Studio", keywords: "character creator lpc ulpc preview", summary: "Character Studio is the project-facing editor over the same exact CharacterRecipe, equipment authority and compositor used by player/NPC runtime.", workflow: "Use Create for inherent appearance, Wardrobe & Gear for equipment, Layers for resolved composition and NPC Generator for constrained profiles.", notes: "Editor-only parallel character composition is prohibited." },
    HelpArticle { page: HelpPage::CharacterCreate, title: "Create Appearance", category: "Character Studio", keywords: "body species skin face eyes hair create", summary: "Create controls inherent/persistent character appearance such as species/body/skin/head/face/eyes/hair and special anatomy.", workflow: "Choose a category, visually select a compatible option and inspect the resolved preview/layers.", notes: "Equipment should not destroy appearance selections." },
    HelpArticle { page: HelpPage::WardrobeGear, title: "Wardrobe & Gear", category: "Character Studio", keywords: "wardrobe gear clothing armor weapons tools thumbnails", summary: "Wardrobe & Gear is the visual inventory of wearable/equippable character content shared conceptually with the game equipment authority.", workflow: "Choose an equipment category/slot, browse compatible thumbnails, equip/select an item and inspect coverage/conflicts.", notes: "The game UI is simpler but uses the same equipment authority." },
    HelpArticle { page: HelpPage::EquipmentSlots, title: "Equipment Slots", category: "Character Studio", keywords: "head neck torso hands legs feet back main offhand slots", summary: "Equipment Slots answers what is equipped and what can go into each semantic gameplay slot.", workflow: "Switch Character Layers to Equipment Slots, select a slot and let Wardrobe filter to compatible candidates.", notes: "Tool Belt remains a separate gameplay inventory authority." },
    HelpArticle { page: HelpPage::CharacterLayers, title: "Character Layers", category: "Character Studio", keywords: "layers composition recipe zpos missing run", summary: "Character Layers show the resolved visual composition and current-action coverage for the actual CharacterRecipe.", workflow: "Use Composition for rendered semantic parts or Equipment Slots for gameplay slot state; select rows to synchronize Browser/Preview.", notes: "Raw LPC technical slices are expandable advanced detail; ULPC z-order remains authoritative." },
    HelpArticle { page: HelpPage::CharacterOcclusion, title: "Equipment Occlusion & Conflicts", category: "Character Studio", keywords: "helmet hair ears cape backpack two handed shield occlusion", summary: "Shared presentation rules hide conflicting visual layers while preserving the underlying recipe, e.g. helmets suppress hair/ears and two-handed weapons conflict with offhand items.", workflow: "Equip the item, inspect Character Layers for ⊘/conflict notes, and verify removing it restores the preserved appearance.", notes: "Prefer explicit compatible authored variants before generic semantic occlusion." },
    HelpArticle { page: HelpPage::AnimationCoverage, title: "Character Animation Coverage", category: "Character Studio", keywords: "idle walk run sit missing garment coverage full core partial broken", summary: "Each wearable/equipment family is classified against required actions/directions so source gaps are distinguished from Havenwild resolver defects.", workflow: "Select an action/direction and inspect ✓/⚠ rows. Use coverage reports to classify Full/Core/Partial/Broken and repair mappings or missing art appropriately.", notes: "Never silently pretend a missing-action garment was unequipped." },
    HelpArticle { page: HelpPage::NpcGenerator, title: "NPC Generator", category: "Character Studio", keywords: "npc generate profile farmer guard miner bandit", summary: "NPC Generator creates deterministic CharacterRecipes from constrained profiles instead of choosing randomly from the whole LPC catalog.", workflow: "Choose a profile, generate, inspect restrictions/warnings, regenerate selected dimensions or save the resulting NPC Instance/Preset.", notes: "Generated identity/seed remains stable once committed." },
    HelpArticle { page: HelpPage::NpcProfiles, title: "NPC Profiles, Presets & Instances", category: "Character Studio", keywords: "profile preset instance profession faction", summary: "Profile = procedural generation rules; Preset = authored reusable character; Instance = the persistent person in a world.", workflow: "Edit/select a Profile for generation constraints, use Presets for intentional authored characters and persist Instances in world simulation.", notes: "Species, profession, faction and hostility remain independent concepts." },
    HelpArticle { page: HelpPage::ProfileInheritance, title: "NPC Profile Inheritance", category: "Character Studio", keywords: "profile inheritance parent overrides rules precedence", summary: "Profiles inherit shared rule families so specialized roles do not duplicate every species/apparel/equipment constraint.", workflow: "Resolve parent profile, apply child overrides/merges, validate cycles and inspect the effective rules before generation.", notes: "Hard biological/equipment constraints outrank cosmetic weights." },
    HelpArticle { page: HelpPage::PopulationGeneration, title: "NPC Population Generation", category: "Character Studio", keywords: "population settlement counts households professions minimum maximum", summary: "Population planning applies settlement-level minima/maxima/weights, workplaces/homes and profile availability before generating persistent NPCs.", workflow: "Choose settlement/population target, calculate profile allocations, validate required homes/workplaces and generate stable NPC Instances.", notes: "Population rules prevent nonsensical distributions such as dozens of blacksmiths with no farmers." },
    HelpArticle { page: HelpPage::LogicStudio, title: "Logic Studio", category: "Logic Studio", keywords: "logic behavior nodes connections bindings cards", summary: "Logic Studio authors reusable/project behavior through nodes/cards and explicit stable bindings.", workflow: "Place/select nodes, connect compatible ports, bind stable project authorities, validate and test.", notes: "Semantic visual layers can expose nested Logic channels without merging visual and logic storage." },
    HelpArticle { page: HelpPage::SoundStudio, title: "Sound Studio", category: "Sound Studio", keywords: "sound audio midi nodes timeline instruments", summary: "Sound Studio authors audio graphs, procedural/MIDI-style sounds, instruments/effects and event/timeline bindings.", workflow: "Build/connect nodes, preview, publish, then bind resources to world emitters, animation events, UI or gameplay actions.", notes: "Sound Emitters own placement; Sound Studio owns the sound resource." },
    HelpArticle { page: HelpPage::PlayTesting, title: "Play From Here & Runtime Testing", category: "Workflow", keywords: "play runtime client scene test", summary: "Play From Here launches the game client into the selected authoritative Scene/location for immediate gameplay verification.", workflow: "Save, select the target Scene/location, Play From Here, verify runtime behavior, then repair the same source authority in editor.", notes: "Editor/runtime should never maintain competing copies of world or character state." },
    HelpArticle { page: HelpPage::SaveRecovery, title: "Save, Close & Recovery", category: "Workflow", keywords: "save dont save cancel dirty autosave recovery", summary: "Every canvas document uses universal dirty-state tracking, Save/Don't Save/Cancel and autosave/crash recovery.", workflow: "Ctrl+S saves; Ctrl+W closes active document; Save As handles untitled documents; recovery restores recoverable unsaved state.", notes: "No Studio may implement a separate close/save workflow." },
    HelpArticle { page: HelpPage::Troubleshooting, title: "Troubleshooting & Validation", category: "Troubleshooting", keywords: "error warning needs binding missing run transition collision references", summary: "Validation messages route back to their owning authority such as asset binding, character coverage, transition, world reference or collision.", workflow: "Read the exact warning, open its contextual Help, repair the owning source, validate again and retest the same acceptance case.", notes: "Warnings must be specific enough to distinguish source gaps from resolver/editor defects." },
];

impl HelpPage {
    const ALL: [Self; 78] = [
        Self::Welcome, Self::GettingStarted, Self::ProjectHome, Self::Shortcuts, Self::Canvas,
        Self::DocumentTabs, Self::ToolRail, Self::LayerRail, Self::Inspector, Self::RightDock,
        Self::UndoRedo, Self::Validation, Self::SettingsActivity, Self::AssetBrowser, Self::AssetStatus,
        Self::AssetPromotion, Self::BatchPromotion, Self::WhereUsed, Self::Licensing, Self::WorldStudio,
        Self::EntireWorldCanvas, Self::WorldLod, Self::WorldGeneration, Self::RegenerationScopes, Self::AuthoredOverrides,
        Self::TerrainMaterials, Self::ElevationCliffs, Self::WaterHydrology, Self::RoadsPaths, Self::Vegetation,
        Self::Resources, Self::Structures, Self::WorldNpcSpawns, Self::WorldCollision, Self::WorldPixelMode,
        Self::Transitions, Self::TransitionRepair, Self::WorldRoutes, Self::SceneStudio, Self::SceneBrowser,
        Self::SceneLayers, Self::FurnitureProps, Self::SceneNpcEditing, Self::TriggersInteractions, Self::SceneCollision,
        Self::LightingFx, Self::SoundEmitters, Self::SceneLogic, Self::PixelAuthoring, Self::PixelDrawingTools,
        Self::PixelSelectionTransform, Self::PixelLayers, Self::ColorPalette, Self::PixelPublishing, Self::AnimationStudio,
        Self::FramesCels, Self::TimelinePlayback, Self::OnionSkin, Self::AnchorsSockets, Self::HitboxesHurtboxes,
        Self::AnimationEvents, Self::WorldObjectAnimation, Self::CharacterStudio, Self::CharacterCreate, Self::WardrobeGear,
        Self::EquipmentSlots, Self::CharacterLayers, Self::CharacterOcclusion, Self::AnimationCoverage, Self::NpcGenerator,
        Self::NpcProfiles, Self::ProfileInheritance, Self::PopulationGeneration, Self::LogicStudio, Self::SoundStudio,
        Self::PlayTesting, Self::SaveRecovery, Self::Troubleshooting,
    ];

    fn article(self) -> &'static HelpArticle {
        HELP_ARTICLES.iter().find(|article| article.page == self).expect("HelpPage must have an article")
    }

    fn label(self) -> &'static str { self.article().title }

    fn matches(self, query: &str) -> bool {
        let query = query.trim().to_ascii_lowercase();
        if query.is_empty() { return true; }
        let article = self.article();
        [article.title, article.category, article.keywords, article.summary, article.workflow, article.notes]
            .into_iter()
            .any(|text| text.to_ascii_lowercase().contains(&query))
    }
}

#[derive(Clone, Debug)]
pub(crate) struct HelpCenterState {
    pub open: bool,
    pub page: HelpPage,
    pub query: String,
    pub nav_offset: usize,
}

impl Default for HelpCenterState {
    fn default() -> Self {
        Self { open: false, page: HelpPage::Welcome, query: String::new(), nav_offset: 0 }
    }
}

const HELP_VISIBLE_ROWS: usize = 14;

impl EditorApp {
    pub(crate) fn open_help_center(&mut self, page: HelpPage) {
        self.help_center.open = true;
        self.help_center.page = page;
    }

    pub(crate) fn contextual_help_page(&self) -> HelpPage {
        use super::canvas_layers::CanvasLayerKind as L;
        if let Some(layer) = self.active_canvas_layer_kind() {
            match layer {
                L::Terrain => return HelpPage::TerrainMaterials,
                L::Water | L::WaterSwim => return HelpPage::WaterHydrology,
                L::RoadsPaths | L::Navigation => return HelpPage::RoadsPaths,
                L::StructuralLevels => return HelpPage::ElevationCliffs,
                L::TerrainTransitions => return HelpPage::TransitionRepair,
                L::Vegetation => return HelpPage::Vegetation,
                L::Resources => return HelpPage::Resources,
                L::Structures | L::Buildings => return HelpPage::Structures,
                L::Furniture | L::Props | L::Objects => return if self.viewport_mode == EditorViewportMode::SceneMap { HelpPage::FurnitureProps } else { HelpPage::Structures },
                L::Characters => return HelpPage::SceneNpcEditing,
                L::SpawnPopulation => return HelpPage::WorldNpcSpawns,
                L::Triggers | L::Interaction => return HelpPage::TriggersInteractions,
                L::Lighting | L::Effects => return HelpPage::LightingFx,
                L::SoundEmitters => return HelpPage::SoundEmitters,
                L::AuthoredPixels | L::PixelLayer => return HelpPage::WorldPixelMode,
                L::CharacterParts | L::Occlusion => return HelpPage::CharacterLayers,
                L::Collision => return if self.viewport_mode == EditorViewportMode::SceneMap { HelpPage::SceneCollision } else { HelpPage::WorldCollision },
                L::LogicNodes | L::LogicConnections | L::LogicBindings | L::Zones | L::Links => return HelpPage::LogicStudio,
                L::SoundNodes | L::SoundConnections | L::SoundTimeline => return HelpPage::SoundStudio,
                L::AnimationFrames => return HelpPage::FramesCels,
                L::AnimationAnchors | L::AnimationFootAnchor | L::AnimationShadowAnchor | L::AnimationSockets => return HelpPage::AnchorsSockets,
                L::AnimationHitboxes | L::AnimationHurtboxes => return HelpPage::HitboxesHurtboxes,
                L::AnimationEvents => return HelpPage::AnimationEvents,
                _ => {}
            }
        }
        match self.viewport_mode {
            EditorViewportMode::SceneRectangles | EditorViewportMode::RegionGraph => HelpPage::WorldStudio,
            EditorViewportMode::SceneMap | EditorViewportMode::SceneBank => HelpPage::SceneStudio,
            EditorViewportMode::PixelStudio => HelpPage::PixelAuthoring,
            EditorViewportMode::AnimationStudio => HelpPage::AnimationStudio,
            EditorViewportMode::CharacterStudio if self.character_studio.mode == super::character_studio::CharacterStudioMode::Npc => HelpPage::NpcGenerator,
            EditorViewportMode::CharacterStudio => HelpPage::CharacterStudio,
            EditorViewportMode::LogicStudio => HelpPage::LogicStudio,
            EditorViewportMode::SoundStudio => HelpPage::SoundStudio,
        }
    }

    fn filtered_help_pages(&self) -> Vec<HelpPage> {
        HelpPage::ALL.into_iter().filter(|page| page.matches(&self.help_center.query)).collect()
    }

    pub(crate) fn draw_help_center(&self) {
        if !self.help_center.open { return; }
        let w = screen_width();
        let h = screen_height();
        draw_rectangle(0.0, 0.0, w, h, Color::new(0.0, 0.0, 0.0, 0.46));
        let panel = Rect::new((w - 1040.0).max(16.0) * 0.5, (h - 700.0).max(16.0) * 0.5, 1040.0_f32.min(w - 32.0), 700.0_f32.min(h - 32.0));
        draw_rectangle(panel.x, panel.y, panel.w, panel.h, editor_theme::colors::PANEL_BG);
        draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 1.0, editor_theme::colors::BORDER_STRONG);
        draw_editor_text("Havenwild Editor Help / Wiki", panel.x + 18.0, panel.y + 30.0, 20.0, editor_theme::colors::TEXT_PRIMARY);
        draw_editor_widget(help_close_rect(panel), "Close", false);

        let nav = Rect::new(panel.x + 12.0, panel.y + 48.0, 250.0, panel.h - 60.0);
        draw_rectangle(nav.x, nav.y, nav.w, nav.h, editor_theme::colors::PANEL_HEADER);
        draw_editor_text("Search", nav.x + 10.0, nav.y + 20.0, 12.0, editor_theme::colors::TEXT_SECONDARY);
        let search = help_search_rect(nav);
        draw_help_search_input(search, &self.help_center.query, self.text_focus == EditorTextFocus::HelpSearch);
        if !self.help_center.query.is_empty() { draw_editor_widget(help_search_clear_rect(search), "x", false); }

        let pages = self.filtered_help_pages();
        let start = self.help_center.nav_offset.min(pages.len().saturating_sub(HELP_VISIBLE_ROWS));
        for (row_index, page) in pages.iter().skip(start).take(HELP_VISIBLE_ROWS).enumerate() {
            let row = help_nav_row(nav, row_index);
            let article = page.article();
            let label = if article.category == "Getting Started" || article.category == "Editor" {
                article.title.to_string()
            } else {
                format!("{} · {}", article.category, article.title)
            };
            draw_editor_widget_tone(row, &label, self.help_center.page == *page, if self.help_center.page == *page { WidgetTone::Primary } else { WidgetTone::Quiet });
        }
        draw_editor_widget_tone(help_nav_prev_rect(nav), "^", false, if start > 0 { WidgetTone::Quiet } else { WidgetTone::Disabled });
        draw_editor_widget_tone(help_nav_next_rect(nav), "v", false, if start + HELP_VISIBLE_ROWS < pages.len() { WidgetTone::Quiet } else { WidgetTone::Disabled });
        draw_wrapped(&format!("{} matching article{} • F1 opens Help", pages.len(), if pages.len() == 1 { "" } else { "s" }), nav.x + 10.0, nav.y + nav.h - 18.0, nav.w - 62.0, 11.5, editor_theme::colors::TEXT_SECONDARY);

        let content = Rect::new(nav.x + nav.w + 18.0, nav.y, panel.x + panel.w - (nav.x + nav.w + 30.0), nav.h);
        if self.help_center.page == HelpPage::Welcome {
            self.draw_help_index(content);
        } else if self.help_center.page == HelpPage::Shortcuts {
            self.draw_shortcuts_help(content);
        } else {
            draw_help_article(content, self.help_center.page.article());
        }
    }

    fn draw_help_index(&self, rect: Rect) {
        let article = HelpPage::Welcome.article();
        draw_help_article_header(rect, article);
        let mut categories: Vec<(&'static str, usize)> = Vec::new();
        for help in HELP_ARTICLES.iter() {
            if let Some((_, count)) = categories.iter_mut().find(|(category, _)| *category == help.category) {
                *count += 1;
            } else {
                categories.push((help.category, 1));
            }
        }
        let mut y = rect.y + 150.0;
        draw_editor_text("Manual Index", rect.x, y, 16.0, editor_theme::colors::TEXT_PRIMARY);
        y += 26.0;
        for (category, count) in categories {
            if y > rect.y + rect.h - 116.0 { break; }
            draw_editor_text(category, rect.x, y, 13.0, editor_theme::colors::TEXT_PRIMARY);
            draw_editor_text(&format!("{count} article{}", if count == 1 { "" } else { "s" }), rect.x + 270.0, y, 12.0, editor_theme::colors::TEXT_SECONDARY);
            y += 21.0;
        }
        draw_editor_text("Common workflows", rect.x, rect.y + rect.h - 86.0, 14.0, editor_theme::colors::TEXT_PRIMARY);
        draw_wrapped("Generate a world • Edit terrain • Repair a transition • Promote LPC assets • Dress/equip a character • Diagnose missing Run artwork • Generate NPCs • Edit a Scene • Play From Here", rect.x, rect.y + rect.h - 62.0, rect.w, 12.0, editor_theme::colors::TEXT_SECONDARY);
    }

    fn draw_shortcuts_help(&self, rect: Rect) {
        let article = HelpPage::Shortcuts.article();
        draw_help_article_header(rect, article);
        let globals = [
            ("F1", "Help Center"), ("Ctrl+S / F5", "Save All"), ("Ctrl+Z / Ctrl+Y", "Undo / Redo"),
            ("Space + drag", "Pan canvas"), ("Mouse wheel", "Zoom canvas"), ("Esc", "Return to non-destructive Select / Inspect"),
            ("Ctrl+J", "Toggle bottom panels"), ("Ctrl+Shift+I", "Toggle inspector"),
            ("Ctrl+W", "Close active document"), ("Ctrl+Shift+T", "Reopen last closed document"),
            ("Alt+1..9", "Select visible canvas layer by row"),
            ("Shift-modified keys", "Reserved for the active Studio/workspace; the universal Tool Rail consumes plain keys"),
        ];
        let mut y = rect.y + 112.0;
        for (key, action) in globals {
            draw_editor_text(key, rect.x, y, 13.0, editor_theme::colors::ACCENT);
            draw_editor_text(action, rect.x + 145.0, y, 13.0, editor_theme::colors::TEXT_PRIMARY);
            y += 22.0;
        }
        y += 6.0;
        draw_editor_text(&format!("Current canvas: {}", self.viewport_mode.label()), rect.x, y, 15.0, editor_theme::colors::TEXT_PRIMARY);
        y += 24.0;
        let layer = self.active_canvas_layer_kind();
        for group in ToolGroup::ALL {
            if y > rect.y + rect.h - 32.0 { break; }
            if !tool_registry::group_has_applicable_tool(self.viewport_mode, layer, group) { continue; }
            draw_editor_text(group.label(), rect.x, y, 12.5, editor_theme::colors::TEXT_SECONDARY);
            y += 18.0;
            for tool in group.tools().iter().copied().filter(|tool| tool_registry::tool_is_applicable(self.viewport_mode, layer, *tool)) {
                if y > rect.y + rect.h - 20.0 { break; }
                let descriptor = tool_registry::descriptor(tool);
                draw_editor_text(descriptor.shortcut, rect.x + 14.0, y, 11.5, editor_theme::colors::ACCENT);
                draw_editor_text(tool.label(), rect.x + 132.0, y, 11.5, editor_theme::colors::TEXT_PRIMARY);
                y += 18.0;
            }
            y += 3.0;
        }
    }

    pub(crate) fn handle_help_center_click(&mut self, point: Vec2) -> bool {
        if !self.help_center.open { return false; }
        let w = screen_width();
        let h = screen_height();
        let panel = Rect::new((w - 1040.0).max(16.0) * 0.5, (h - 700.0).max(16.0) * 0.5, 1040.0_f32.min(w - 32.0), 700.0_f32.min(h - 32.0));
        if help_close_rect(panel).contains(point) || !panel.contains(point) {
            self.help_center.open = false;
            if self.text_focus == EditorTextFocus::HelpSearch { self.text_focus = EditorTextFocus::None; }
            return true;
        }
        let nav = Rect::new(panel.x + 12.0, panel.y + 48.0, 250.0, panel.h - 60.0);
        let search = help_search_rect(nav);
        if search.contains(point) {
            if help_search_clear_rect(search).contains(point) && !self.help_center.query.is_empty() {
                self.help_center.query.clear();
                self.help_center.nav_offset = 0;
            } else {
                self.text_focus = EditorTextFocus::HelpSearch;
            }
            return true;
        }
        let pages = self.filtered_help_pages();
        let max_offset = pages.len().saturating_sub(HELP_VISIBLE_ROWS);
        if help_nav_prev_rect(nav).contains(point) {
            self.help_center.nav_offset = self.help_center.nav_offset.saturating_sub(HELP_VISIBLE_ROWS.min(4));
            return true;
        }
        if help_nav_next_rect(nav).contains(point) {
            self.help_center.nav_offset = (self.help_center.nav_offset + HELP_VISIBLE_ROWS.min(4)).min(max_offset);
            return true;
        }
        let start = self.help_center.nav_offset.min(max_offset);
        for (row_index, page) in pages.iter().skip(start).take(HELP_VISIBLE_ROWS).enumerate() {
            if help_nav_row(nav, row_index).contains(point) {
                self.help_center.page = *page;
                self.text_focus = EditorTextFocus::None;
                return true;
            }
        }
        true
    }
}


fn draw_help_search_input(rect: Rect, query: &str, focused: bool) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, editor_theme::colors::CONTROL_BG);
    draw_rectangle_lines(
        rect.x, rect.y, rect.w, rect.h,
        if focused { 1.5 } else { 1.0 },
        if focused { editor_theme::colors::ACCENT } else { editor_theme::colors::BORDER_STRONG },
    );
    let text = if query.is_empty() { "Search tools, workflows, errors..." } else { query };
    draw_scissored_text(
        text, rect.x + 8.0, rect.y + 18.0, rect.w - 38.0, 12.0,
        if query.is_empty() { editor_theme::colors::TEXT_SECONDARY } else { editor_theme::colors::TEXT_PRIMARY },
    );
}

fn help_close_rect(panel: Rect) -> Rect { Rect::new(panel.x + panel.w - 82.0, panel.y + 8.0, 70.0, 30.0) }
fn help_search_rect(nav: Rect) -> Rect { Rect::new(nav.x + 8.0, nav.y + 28.0, nav.w - 16.0, 28.0) }
fn help_search_clear_rect(search: Rect) -> Rect { Rect::new(search.x + search.w - 27.0, search.y + 2.0, 24.0, search.h - 4.0) }
fn help_nav_row(nav: Rect, index: usize) -> Rect { Rect::new(nav.x + 6.0, nav.y + 64.0 + index as f32 * 34.0, nav.w - 12.0, 29.0) }
fn help_nav_prev_rect(nav: Rect) -> Rect { Rect::new(nav.x + nav.w - 44.0, nav.y + nav.h - 26.0, 18.0, 20.0) }
fn help_nav_next_rect(nav: Rect) -> Rect { Rect::new(nav.x + nav.w - 24.0, nav.y + nav.h - 26.0, 18.0, 20.0) }

fn draw_help_article_header(rect: Rect, article: &HelpArticle) {
    draw_editor_text(article.title, rect.x, rect.y + 26.0, 20.0, editor_theme::colors::TEXT_PRIMARY);
    draw_editor_text(article.category, rect.x, rect.y + 49.0, 12.0, editor_theme::colors::ACCENT);
    draw_wrapped(article.summary, rect.x, rect.y + 72.0, rect.w, 14.0, editor_theme::colors::TEXT_PRIMARY);
}

fn draw_help_article(rect: Rect, article: &HelpArticle) {
    draw_help_article_header(rect, article);
    let workflow_y = rect.y + 172.0;
    draw_editor_text("Workflow", rect.x, workflow_y, 16.0, editor_theme::colors::TEXT_PRIMARY);
    draw_wrapped(article.workflow, rect.x, workflow_y + 26.0, rect.w, 13.5, editor_theme::colors::TEXT_SECONDARY);
    let notes_y = rect.y + 390.0;
    draw_editor_text("Important", rect.x, notes_y, 16.0, editor_theme::colors::TEXT_PRIMARY);
    draw_wrapped(article.notes, rect.x, notes_y + 26.0, rect.w, 13.5, editor_theme::colors::TEXT_SECONDARY);
    draw_scissored_text("Search terms", rect.x, rect.y + rect.h - 42.0, rect.w, 11.0, editor_theme::colors::TEXT_SECONDARY);
    draw_scissored_text(article.keywords, rect.x, rect.y + rect.h - 22.0, rect.w, 11.0, editor_theme::colors::TEXT_SECONDARY);
}
