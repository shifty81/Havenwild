$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Command = if ($args.Count -gt 0) { $args[0].ToLowerInvariant() } else { "all" }
$ExtraArgs = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$LogRoot = Join-Path $Root "logs/builds"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogRoot "havenwild-$Command-$Timestamp.log"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$TranscriptStarted = $false
try {
    Start-Transcript -Path $LogPath -Force | Out-Null
    $TranscriptStarted = $true
    Write-Host "Havenwild build log: $LogPath"
}
catch {
    Write-Warning "Unable to start PowerShell transcript: $($_.Exception.Message)"
}

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "START $Name"
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Host "OK $Name"
}

function Invoke-DevelopmentWorld {
    Require-Command "cargo"
    $DescriptorPath = Join-Path $Root "WORKSPACE/development/active_world.json"
    if (-not (Test-Path $DescriptorPath)) {
        throw "Development-world descriptor is missing: $DescriptorPath"
    }
    $Descriptor = Get-Content -Raw $DescriptorPath | ConvertFrom-Json
    if ($Descriptor.schema -ne "havenwild.development_world.v1") {
        throw "Unsupported development-world descriptor schema: $($Descriptor.schema)"
    }
    if ([string]::IsNullOrWhiteSpace($Descriptor.world_id) -or [string]::IsNullOrWhiteSpace($Descriptor.character_id)) {
        throw "Development-world descriptor requires world_id and character_id"
    }
    $ClientExe = Join-Path $Root "target\debug\haven_game.exe"
    if (-not (Test-Path -LiteralPath $ClientExe -PathType Leaf)) {
        Write-Host "Development client is missing; building haven_game first"
        cargo build -p haven_game
        if ($LASTEXITCODE -ne 0) {
            throw "Development client build failed with exit code $LASTEXITCODE"
        }
    }

    Write-Host "Launching development world $($Descriptor.world_id) with $($Descriptor.character_id)"
    Write-Host "Development client: $ClientExe"
    $Process = Start-Process -FilePath $ClientExe `
        -ArgumentList @("--dev-world", [string]$Descriptor.world_id, "--dev-character", [string]$Descriptor.character_id) `
        -WorkingDirectory $Root `
        -PassThru
    if ($null -eq $Process) {
        throw "Development client did not start"
    }
    Write-Host "Development world launched (PID $($Process.Id)); main menu bypassed"
    Write-Host "Supervising development client until termination so session diagnostics can be finalized"
    $Process.WaitForExit()
    $exitCode = $Process.ExitCode
    Write-Host "Development client terminated (PID $($Process.Id), exit code $exitCode)"
    if ($exitCode -ne 0) {
        throw "Development client exited abnormally with code $exitCode"
    }
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required"
    }
}

function Find-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return "python3" }
    throw "python or python3 is required"
}


function Normalize-WorkspaceLayout {
    $Python = Find-Python
    Invoke-Step "normalize machine-local workspace layout" {
        & $Python (Join-Path $Root "tools/automation/project/Normalize-WorkspaceLayout.py")
    }
}

function Ensure-FrontendMusic {
    $Python = Find-Python
    Invoke-Step "restore/verify attributed frontend music" {
        & $Python (Join-Path $Root "tools/automation/audio/Ensure-FrontendMusicV167Z56.py")
    }
}

function Ensure-LpcDependency {
    $Python = Find-Python
    Invoke-Step "validate/acquire pinned LPC dependency" { & $Python (Join-Path $Root "tools/automation/dependencies/Ensure-LpcDependency.py") }
    Invoke-Step "audit and route complete ElizaWy/LPC repository" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py") --strict
    }
}


function Ensure-UniversalLpcDependency {
    $Python = Find-Python
    $PreviousStrict = $env:HAVENWILD_ULPC_STRICT
    try {
        $env:HAVENWILD_ULPC_STRICT = "1"
        Invoke-Step "validate/acquire complete Universal LPC character repository" {
            & $Python (Join-Path $Root "tools/automation/characters/Ensure-UniversalLpcGenerator.py")
        }
    }
    finally {
        $env:HAVENWILD_ULPC_STRICT = $PreviousStrict
    }
    Invoke-Step "index complete Universal LPC character/equipment repository" {
        & $Python (Join-Path $Root "tools/automation/characters/Build-UniversalLpcCompleteRepositoryIndexV167Z7.py")
    }
    Invoke-Step "validate complete Universal LPC repository summary" {
        & $Python (Join-Path $Root "tools/automation/characters/Validate-UniversalLpcCompleteRepositorySummaryV167Z41.py")
    }
    Invoke-Step "build normalized Universal LPC character metadata catalog" {
        & $Python (Join-Path $Root "tools/automation/characters/Build-UniversalLpcNormalizedCharacterCatalogV1.py")
    }
}

function Sync-OgaLpcPrototypes {
    $Python = Find-Python
    Invoke-Step "sync curated OpenGameArt LPC prototype sources" {
        & $Python (Join-Path $Root "tools/automation/assets/Acquire-OgaLpcGameplayBatchV167S.py") --all --best-effort
    }
}

function Build-LpcProjectFoundation {
    $Python = Find-Python
    Invoke-Step "build combined ElizaWy and Universal LPC project foundation" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-LpcProjectFoundationV167Z40.py") --strict
    }
}

function Build-AssetPromotionCloseout {
    param([switch]$Strict)
    $Python = Find-Python
    $Arguments = @((Join-Path $Root "tools/automation/assets/Build-HavenwildAssetPromotionCloseoutV167Z84.py"))
    if ($Strict) { $Arguments += "--strict" }
    Invoke-Step "build Havenwild asset promotion closeout matrix" {
        & $Python @Arguments
    }
}

function Prepare-UniversalLpcRuntimeAssets {
    $Python = Find-Python
    $RevisionPath = Join-Path $Root "assets/generated/lpc/characters/.generator_revision"
    $RequiredRevision = "167Z109V1-authored-action-alias-and-directional-coverage-v1"
    $InstalledRevision = if (Test-Path $RevisionPath) { (Get-Content -Raw $RevisionPath).Trim() } else { "" }
    if ($env:HAVENWILD_REBUILD_PLAYER_ATLAS -eq "1" -or $InstalledRevision -ne $RequiredRevision) {
        Invoke-Step "build Universal LPC character action caches" {
            & $Python (Join-Path $Root "tools/automation/characters/Build-UniversalLpcPlayerRuntimeCachesV167Z7.py")
        }
    }
    else {
        Write-Host "Universal LPC character caches match $RequiredRevision"
    }
}

function Prepare-ElizaWyRuntimeAssets {
    $Python = Find-Python
    Invoke-Step "build natural-scale ElizaWy tree and object atlas" {
        & $Python (Join-Path $Root "tools/automation/assets/Promote-LpcRuntimeAssets.py") --objects-only
    }
    Invoke-Step "materialize tree-first ElizaWy open-world biome scene" {
        & $Python (Join-Path $Root "tools/automation/worldgen/Build-ClientWorldgenTestSceneV167Z.py")
    }
}

function Test-RustFormat {
    Require-Command "cargo"
    Invoke-Step "cargo fmt --all -- --check" { cargo fmt --all -- --check }
}

function Test-RustCheck {
    Require-Command "cargo"
    Invoke-Step "cargo check --workspace --all-targets" { cargo check --workspace --all-targets }
}

function Test-RustClippy {
    Require-Command "cargo"
    Invoke-Step "cargo clippy --workspace --all-targets -- -D warnings" { cargo clippy --workspace --all-targets -- -D warnings }
}

function Test-RustTests {
    Require-Command "cargo"
    Invoke-Step "cargo test --workspace" { cargo test --workspace }
    $Python = Get-PythonCommand
    Invoke-Step "validate W57K10A-W60 unified authoring authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-UnifiedCanvasAuthoringW60.py")
    }
    Invoke-Step "validate W60B editor UI authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-EditorUiAuthorityW60B.py")
    }
    Invoke-Step "validate W60C canvas UX and asset-browser authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CanvasUxAssetBrowserW60C.py")
    }
    Invoke-Step "validate W60D ruler-safe canvas corner layer dock" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CanvasCornerLayerDockW60D.py")
    }
    Invoke-Step "validate W60E1 shared canvas composition" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-SharedCanvasCompositionW60E1.py")
    }
    Invoke-Step "validate W60E2 collision truth" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CollisionAuthoringW60E2.py")
    }
    Invoke-Step "validate W60E3 CanvasWorkspace authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CanvasWorkspaceAuthorityW60E3.py")
    }
    Invoke-Step "validate W60E3I Building Composite authoring handoff" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-BuildingCompositeAuthoringHandoffW60E3I.py")
    }
    Invoke-Step "validate W60E4 Building Composite runtime publish" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-BuildingCompositeRuntimePublishW60E4.py")
    }
    Invoke-Step "validate W60E5 contextual CanvasWorkspace workflow" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ContextualCanvasWorkflowW60E5.py")
    }
    Invoke-Step "validate W60E6 Pixel interaction and symmetry workflow" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-PixelInteractionSymmetryW60E6.py")
    }
    Invoke-Step "validate W60E7 structural selected-region round trip" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-StructuralCanvasRoundTripW60E7.py")
    }
    Invoke-Step "validate W60E7 Canvas tool capability truth" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CanvasToolCapabilityTruthW60E7.py")
    }
    Invoke-Step "validate W60E8 tool adapter completion" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ToolAdapterCompletionW60E8.py") }
    Invoke-Step "validate W60E9 gameplay layer adapters" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-GameplayLayerAdaptersW60E9.py") }
    Invoke-Step "validate W60E10 pixel selection transforms" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-PixelSelectionTransformsW60E10.py") }
    Invoke-Step "validate W60E11 animation metadata" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-AnimationMetadataW60E11.py") }
    Invoke-Step "validate W60E12 shared inspector/canvas normalization" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-SharedInspectorCanvasW60E12.py") }
    Invoke-Step "validate W60E13 canvas chrome/widget normalization" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CanvasChromeWidgetNormalizationW60E13.py") }
    Invoke-Step "validate W60E14 tool taxonomy/options" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ToolTaxonomyOptionsW60E14.py") }
    Invoke-Step "validate W60E15 pixel viewport alignment" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-PixelViewportAlignmentW60E15.py") }
    Invoke-Step "validate W60E16 project-wide panel mapping" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ProjectPanelMappingW60E16.py") }
    Invoke-Step "validate W60E17 Character Studio foundation" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CharacterStudioFoundationW60E17.py") }
    Invoke-Step "validate W60E18 Logic Node Editor architecture lock" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-LogicNodeEditorContractW60E18.py") }
    Invoke-Step "validate W60E19 Pixel multi-document clipboard/promotion" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-PixelMultiDocumentClipboardW60E19.py") }
    Invoke-Step "validate W60E20 integrated canvas rails" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-IntegratedCanvasRailsW60E20.py") }
    Invoke-Step "validate W60E21 canvas view chrome" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-CanvasViewChromeW60E21.py") }
    Invoke-Step "validate W60E22 editor command routing" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-EditorCommandRoutingW60E22.py") }
    Invoke-Step "validate W60E23 inspector/bottom dock normalization" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-InspectorBottomDockW60E23.py") }
    Invoke-Step "validate W60E24 native widget/palette normalization" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-NativeWidgetPaletteW60E24.py") }
    Invoke-Step "validate W61A Transform2D authority" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-Transform2DAuthorityW61A.py") }
    Invoke-Step "validate W61B anchor/socket authority" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-AnchorSocketAuthorityW61B.py") }
    Invoke-Step "validate W61C selection transform gizmo/clipboard" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-SelectionTransformGizmoW61C.py") }
    Invoke-Step "validate W61D animation hinge metadata" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-AnimationHingeMetadataW61D.py") }
    Invoke-Step "validate W76A-T native editor GUI closure" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-NativeEditorGuiClosureW76.py") }
    Invoke-Step "validate W76U-V GameMaker workspace document lifecycle" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-GameMakerWorkspaceDocumentLifecycleW76UV.py") }
    Invoke-Step "validate W77 exact terrain presentation + transition workbench" { & $Python (Join-Path $Root "tools/automation/validation/checks/terrain/Validate-TerrainPresentationAuthorityAndWorkbenchW77.py") }
    Invoke-Step "validate W78 native editor GUI authority cleanup" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-NativeEditorGuiAuthorityCleanupW78.py") }
    Invoke-Step "validate W79 native editor interaction/document closure" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-NativeEditorInteractionDocumentClosureW79.py") }
    Invoke-Step "validate W80 Tool Rail + Layer Rail production completion" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ToolLayerRailProductionW80.py") }
    Invoke-Step "validate W81 World Terrain Authoring + Global Tooltip Authority" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-WorldTerrainAuthoringW81.py") }
    Invoke-Step "validate W81R30-R44H6 editor UX + real world view closure" { & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-EditorUxRealWorldViewW81R30R44H6.py") }
    Invoke-Step "validate H20 64-bit seed + shoreline + two-tier cliff/ramp closure" { & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-H20WorldSeedCliffShoreClosure.py") }
    Invoke-Step "validate H20 world-completion authority" { & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-H20WorldCompletion.py") }
}

function Normalize-RustSource {
    Require-Command "cargo"
    Invoke-Step "normalize Rust formatting before architecture validation" { cargo fmt --all }
}

function Build-Rust {
    Require-Command "cargo"
    Normalize-RustSource
    Test-RustFormat
    Test-RustCheck
    Test-RustClippy
    Test-RustTests
    Invoke-Step "cargo build --workspace" { cargo build --workspace }
}



function Copy-ApplicationContent {
    param([string]$Destination)
    $Python = Find-Python
    & $Python (Join-Path $Root "tools/automation/release/Stage-ApplicationContent.py") $Destination
    if ($LASTEXITCODE -ne 0) {
        throw "Filtered application-content staging failed with exit code $LASTEXITCODE"
    }
}

function Build-ApplicationBinaries {
    Require-Command "cargo"
    $DistRoot = Join-Path $Root "Build"
    $ClientRoot = Join-Path $DistRoot "HavenwildClient"
    $EditorRoot = Join-Path $DistRoot "HavenwildEditor"
    New-Item -ItemType Directory -Force -Path $ClientRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $EditorRoot | Out-Null

    Invoke-Step "cargo build --release -p haven_game" { cargo build --release -p haven_game }
    Invoke-Step "cargo build --release -p haven_editor_native" { cargo build --release -p haven_editor_native }

    $ClientSource = Join-Path $Root "target/release/haven_game.exe"
    $EditorSource = Join-Path $Root "target/release/haven_editor_native.exe"
    if (-not (Test-Path $ClientSource)) { throw "Client executable was not produced: $ClientSource" }
    if (-not (Test-Path $EditorSource)) { throw "Editor executable was not produced: $EditorSource" }
    Copy-Item -Force $ClientSource (Join-Path $ClientRoot "HavenwildClient.exe")
    Copy-Item -Force $EditorSource (Join-Path $EditorRoot "HavenwildEditor.exe")
    Copy-ApplicationContent $ClientRoot
    Copy-ApplicationContent $EditorRoot
    Write-Host "Client: $(Join-Path $ClientRoot 'HavenwildClient.exe')"
    Write-Host "Editor: $(Join-Path $EditorRoot 'HavenwildEditor.exe')"
}

function Build-ClientBinary {
    Require-Command "cargo"
    $ClientRoot = Join-Path $Root "Build/HavenwildClient"
    New-Item -ItemType Directory -Force -Path $ClientRoot | Out-Null
    Invoke-Step "cargo build --release -p haven_game" { cargo build --release -p haven_game }
    $ClientSource = Join-Path $Root "target/release/haven_game.exe"
    if (-not (Test-Path $ClientSource)) { throw "Client executable was not produced: $ClientSource" }
    Copy-Item -Force $ClientSource (Join-Path $ClientRoot "HavenwildClient.exe")
    Copy-ApplicationContent $ClientRoot
    Write-Host "Client: $(Join-Path $ClientRoot 'HavenwildClient.exe')"
}

function Build-Catalog {
    $Python = Find-Python
    Invoke-Step "generate asset catalog" { & $Python (Join-Path $Root "tools/automation/assets/Generate-AssetCatalog.py") }
}


function Build-AssetTruthInventory {
    $Python = Find-Python
    Invoke-Step "build W41A world asset truth inventory" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py") --root $Root
    }
    Invoke-Step "validate W41A world asset truth inventory" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-PublishedWorldAssetInventoryV1.py")
    }
}


function Validate-PublishedWorldAssetAuthority {
    $Python = Find-Python
    Build-AssetTruthInventory
    Invoke-Step "validate W42 published world asset authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-PublishedWorldAssetAuthorityV1.py")
    }
}


function Build-WorldAssetAcceptance {
    $Python = Find-Python
    Validate-PublishedWorldAssetAuthority
    Invoke-Step "build W43A world asset acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-WorldAssetAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W43A world asset acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-WorldAssetAcceptanceSceneV1.py")
    }
    Invoke-Step "validate W43B complete placeable visual sweep" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-PlaceableVisualSweepV1.py")
    }
    Invoke-Step "validate W43C Estate visual authority closure" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-EstateVisualAuthorityClosureV1.py")
    }
    Invoke-Step "build W43D complete placeable acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-PlaceableVisualAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W43D complete placeable acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-PlaceableVisualAcceptanceSceneV1.py")
    }
}


function Validate-ExactSourcePixelStudioAuthority {
    $Python = Find-Python
    Invoke-Step "validate W44A exact-source Pixel Studio authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/editor/Validate-ExactSourcePixelStudioAuthorityV1.py")
    }
}


function Build-StructureSourceInventory {
    $Python = Find-Python
    Invoke-Step "build W45A LPC structure source inventory" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureSourceInventoryV1.py") --root $Root
    }
    Invoke-Step "validate W45A LPC structure source inventory" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructureSourceInventoryV1.py")
    }
}


function Build-StructureComponentCertification {
    $Python = Find-Python
    Invoke-Step "build W45A/W45B LPC structure source inventory" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureSourceInventoryV1.py") --root $Root
    }
    Invoke-Step "validate W45A/W45B LPC structure source inventory" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructureSourceInventoryV1.py")
    }
    Invoke-Step "build W45B exact structure component runtime cache" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureComponentCertificationV1.py") --root $Root
    }
    Invoke-Step "validate W45B exact structure component authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructureComponentCertificationV1.py")
    }
}


function Build-StructureSurfaceCertification {
    $Python = Find-Python
    Build-StructureComponentCertification
    Invoke-Step "build W45C structure surface runtime cache" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureSurfaceCertificationV1.py") --root $Root
    }
    Invoke-Step "build W45C structure surface acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureSurfaceAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "build W45C machine-local roof/wall-trim review boards when LPC source is mounted" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureRoofTrimReviewV1.py") --root $Root
    }
    Invoke-Step "validate W45C structure surface + building visibility authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructureSurfaceCertificationV1.py")
    }
}


function Build-StructureRoofTrimCertification {
    $Python = Find-Python
    Build-StructureSurfaceCertification
    Invoke-Step "build W45C2 exact wall-border runtime cache" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureRoofTrimCertificationV1.py") --root $Root
    }
    Invoke-Step "build W45C2 roof/trim acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureRoofTrimAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W45C2 roof topology + wall-border authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructureRoofTrimCertificationV1.py")
    }
}

function Build-ExactRoofReviewEvidence {
    $Python = Find-Python
    Ensure-LpcDependency
    Invoke-Step "build W45C3A exact roof evidence bundle" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-ExactRoofReviewEvidenceV1.py") --root $Root --require-all
    }
    Invoke-Step "validate W45C3A exact roof review authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-ExactRoofReviewEvidenceV1.py")
    }
}


function Build-StructureSupportReviewEvidence {
    $Python = Find-Python
    Ensure-LpcDependency
    Invoke-Step "build W45D1 exact bridge/platform/pillar evidence bundle" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureSupportReviewEvidenceV1.py") --root $Root --require-all
    }
    Invoke-Step "validate W45D1 structure support topology + exact review authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructureSupportReviewEvidenceV1.py")
    }
}


function Build-ExactStructureModules {
    $Python = Find-Python
    Ensure-LpcDependency
    Invoke-Step "rebuild W45D2 structure source inventory" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructureSourceInventoryV1.py") --root $Root
    }
    Invoke-Step "build W45D2 exact roof/support acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-ExactStructureModuleAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W45C3B/W45D2 exact roof/support publication" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-ExactStructureModulePublicationV1.py")
    }
}

function Build-BuildingRecipes {
    $Python = Find-Python
    Invoke-Step "build W46A BuildingRecipe acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-BuildingRecipeAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W46A BuildingRecipe authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-BuildingRecipeAuthorityV1.py")
    }
}

function Build-BuildingInstances {
    $Python = Find-Python
    Invoke-Step "rebuild W46A BuildingRecipe acceptance baseline" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-BuildingRecipeAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W46A BuildingRecipe authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-BuildingRecipeAuthorityV1.py")
    }
    Invoke-Step "build W46B native BuildingInstance acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-BuildingInstanceAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W46B BuildingInstance runtime/editor authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-BuildingInstanceAuthorityV1.py")
    }
}

function Build-BuildingPersistence {
    $Python = Find-Python
    Invoke-Step "rebuild W46B native BuildingInstance acceptance baseline" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-BuildingInstanceAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W46B BuildingInstance runtime/editor authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-BuildingInstanceAuthorityV1.py")
    }
    Invoke-Step "build W46C placement/persistence/PCG acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-BuildingPersistenceAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W46C BuildingInstance placement/persistence authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-BuildingInstancePersistenceAuthorityV1.py")
    }
}

function Build-BuildingInteriors {
    $Python = Find-Python
    Build-BuildingPersistence
    Invoke-Step "validate W47 same-world interior grammar authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-BuildingInteriorGrammarV1.py")
    }
}

function Build-ProductionTavern {
    $Python = Find-Python
    Build-BuildingInteriors
    Invoke-Step "build W48 production tavern acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-TavernBuildingAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W48 production tavern BuildingInstance authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-ProductionTavernAuthorityV1.py")
    }
}

function Build-CaveAssets {
    $Python = Find-Python
    Invoke-Step "validate W49 cave asset authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-CaveAssetAuthorityV1.py")
    }
}

function Build-CaveResolver {
    $Python = Find-Python
    Build-CaveAssets
    Invoke-Step "build W50 cave resolver/PCG acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-CaveResolverAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W50 cave resolver/PCG/editor authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-CaveResolverAuthorityV1.py")
    }
}

function Build-StructuralConnectors {
    $Python = Find-Python
    Invoke-Step "build W51 structural connector acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-StructuralConnectorAcceptanceSceneV1.py") --root $Root
    }
    Invoke-Step "validate W51 structural connector authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-StructuralConnectorAuthorityV1.py")
    }
}

function Build-WorldVisualCertification {
    $Python = Find-Python
    Build-CaveResolver
    Build-StructuralConnectors
    Build-ProductionTavern
    Invoke-Step "build W52 world visual certification acceptance scene" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-WorldVisualCertificationAcceptanceV1.py") --root $Root
    }
    Invoke-Step "validate W52 world visual certification" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-WorldVisualCertificationV1.py")
    }
    Invoke-Step "validate W56 scene population + narrow cave-mouth authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-W56ScenePopulationAuthority.py")
    }
    Invoke-Step "build W56F cliff-height/editor-runtime parity fixture" {
        & $Python (Join-Path $Root "tools/automation/worldgen/Build-CliffHeightAcceptanceW53D.py")
    }
    Invoke-Step "validate W56F cliff-height/editor-runtime parity" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py")
    }
    Invoke-Step "validate W56G editor/runtime object identity + anchor parity" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-W56EditorRuntimeObjectParity.py")
    }
    Invoke-Step "validate W56 cave-mouth geometry contract" {
        & $Python (Join-Path $Root "tools/validation/Validate-W56-CaveMouthContract.py")
    }
    Invoke-Step "validate W56 cave round-trip transition safety" {
        & $Python (Join-Path $Root "tools/validation/Validate-W56-CaveRoundTrip.py")
    }
}

function Build-HomeEstateRegeneration {
    $Python = Find-Python
    Build-WorldVisualCertification
    Invoke-Step "regenerate W53 Home Estate" {
        & $Python (Join-Path $Root "tools/automation/worldgen/Build-HomeEstateSceneW53.py")
    }
    Invoke-Step "validate W53 Home Estate regeneration authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-HomeEstateRegenerationW53.py")
    }
    Invoke-Step "validate W53B runtime scene/content convergence" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-RuntimeContentConvergenceW53B.py")
    }
    Invoke-Step "validate W53C Estate structural/runtime visual repair" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-EstateStructuralRuntimeRepairW53C.py")
    }
    Build-CliffHeightGrammar
    Invoke-Step "validate W53E Estate composition authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-EstateCompositionW53E.py")
    }
    Build-BuildingExterior
    Invoke-Step "validate W54B integrated visual checkpoint" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py")
    }
}

function Build-CliffHeightGrammar {
    $Python = Find-Python
    Invoke-Step "build W53D cliff-height acceptance fixture" {
        & $Python (Join-Path $Root "tools/automation/worldgen/Build-CliffHeightAcceptanceW53D.py")
    }
    Invoke-Step "validate W53D cliff-height runtime grammar" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py")
    }
}

function Build-EstateComposition {
    $Python = Find-Python
    Invoke-Step "regenerate W53E Home Estate composition" {
        & $Python (Join-Path $Root "tools/automation/worldgen/Build-HomeEstateSceneW53.py")
    }
    Invoke-Step "validate W53E Estate composition authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-EstateCompositionW53E.py")
    }
}

function Build-BuildingExterior {
    $Python = Find-Python
    Invoke-Step "validate W54A building exterior grammar" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-BuildingExteriorGrammarW54A.py")
    }
}

function Build-BuildingExteriorEvidence {
    $Python = Find-Python
    Invoke-Step "build W54C exact exterior review evidence" {
        & $Python (Join-Path $Root "tools/automation/assets/Build-ExteriorExactReviewEvidenceW54C.py")
    }
    Invoke-Step "validate W54C exact exterior review evidence authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-ExteriorExactReviewEvidenceW54C.py")
    }
}

function Build-BuildingExteriorSelections {
    $Python = Find-Python
    Invoke-Step "validate W54D1 exact exterior source selections" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/assets/Validate-ExteriorExactSelectionsW54D1.py")
    }
}

function Build-VisualCheckpoint {
    $Python = Find-Python
    Invoke-Step "validate W53D cliff-height runtime grammar" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-CliffHeightRuntimeGrammarW53D.py")
    }
    Invoke-Step "validate W53E Estate composition authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-EstateCompositionW53E.py")
    }
    Invoke-Step "validate W54A building exterior grammar" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-BuildingExteriorGrammarW54A.py")
    }
    Invoke-Step "validate W54B integrated visual checkpoint" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-IntegratedVisualCheckpointW54B.py")
    }
    Invoke-Step "validate W54D2 isolated Estate visual launch" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-EstateVisualLaunchW54D2.py")
    }
    Invoke-Step "validate W54E starter cottage program" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-StarterCottageW54E.py")
    }
    Invoke-Step "validate W54F cottage/Estate geometry baseline" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-CottageEstateVisualRepairW54F.py")
    }
    Invoke-Step "validate W54G cottage visibility/cutaway repair" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-CottageVisibilityCutawayW54G.py")
    }
    Invoke-Step "validate W56 scene population + narrow cave-mouth authority" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-W56ScenePopulationAuthority.py")
    }
    Invoke-Step "validate W56G editor/runtime object identity + anchor parity" {
        & $Python (Join-Path $Root "tools/automation/validation/checks/worldgen/Validate-W56EditorRuntimeObjectParity.py")
    }
    Invoke-Step "validate W56 cave-mouth geometry contract" {
        & $Python (Join-Path $Root "tools/validation/Validate-W56-CaveMouthContract.py")
    }
    Invoke-Step "validate W56 cave round-trip transition safety" {
        & $Python (Join-Path $Root "tools/validation/Validate-W56-CaveRoundTrip.py")
    }
}

function Invoke-EstateVisualTest {
    Build-VisualCheckpoint
    Require-Command "cargo"
    Invoke-Step "build W54G Estate visual-test client" { cargo build -p haven_game }
    Write-Host "Launching isolated W54G Estate visual test; normal gameplay saves are not used"
    & (Join-Path $Root "target/debug/haven_game.exe") --estate-visual-test
}

function Build-AssetIntake {
    $Python = Find-Python
    Invoke-Step "bake asset intake atlas" { & $Python (Join-Path $Root "tools/automation/assets/Bake-AssetIntakeAtlasV66.py") }
}


function Build-TerrainLibraries {
    $Python = Find-Python
    Invoke-Step "promote normalized LPC water and ground transition families" {
        & $Python (Join-Path $Root "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py")
    }
    Invoke-Step "promote expandable LPC pond families" {
        & $Python (Join-Path $Root "tools/automation/terrain/Promote-LpcExpandablePondsV87.py")
    }
}

function Test-Web {
    Write-Host "The legacy browser editor is archived under archive/source/legacy_web_editor."
    Write-Host "Use the native Havenwild editor or the in-game Player World Builder."
}

function Test-Validation {
    param([string]$Domain = "all")
    $Python = Find-Python
    Invoke-Step "Havenwild validation: $Domain" { & $Python (Join-Path $Root "tools/automation/validation/validate.py") $Domain }
}

Push-Location $Root
try {
    Normalize-WorkspaceLayout
    Write-Host "Active Rust sources are authoritative; legacy build-time source rewriters are disabled"
    switch ($Command) {
        "all" { Ensure-FrontendMusic; Ensure-LpcDependency; Ensure-UniversalLpcDependency; Build-LpcProjectFoundation; Build-AssetPromotionCloseout -Strict; Prepare-UniversalLpcRuntimeAssets; Prepare-ElizaWyRuntimeAssets; Build-Rust; Test-Validation "all"; Build-Catalog; Build-ApplicationBinaries }
        "rust" { Build-Rust }
        "check" { Test-RustFormat; Test-RustCheck; Test-RustClippy }
        "test" { Test-RustTests }
        "validate" { Test-Validation $(if ($ExtraArgs.Count) { $ExtraArgs[0] } else { "all" }) }
        "character-audit" {
            Require-Command "cargo"
            Invoke-Step "cargo test character pipeline" { cargo test --workspace character }
            $Python = Find-Python
            Invoke-Step "build Universal LPC Character Conformance Lab" {
                & $Python (Join-Path $Root "tools/automation/characters/Build-UniversalLpcCharacterConformanceLabV1.py")
            }
            Invoke-Step "validate C1-C20 Universal LPC character/gameplay conformance" {
                & $Python (Join-Path $Root "tools/automation/validation/checks/characters/Validate-UniversalLpcCharacterConformanceC1C20.py")
            }
        }
        "catalog" { Build-Catalog }
        "lpc-sync" { Ensure-LpcDependency; Ensure-UniversalLpcDependency; Sync-OgaLpcPrototypes; Build-LpcProjectFoundation; Build-AssetPromotionCloseout -Strict }
        "lpc-audit" {
            Ensure-LpcDependency
            $Python = Find-Python
            Invoke-Step "force complete ElizaWy/LPC project asset audit" {
                & $Python (Join-Path $Root "tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py") --force --strict
            }
            Ensure-UniversalLpcDependency
            Build-LpcProjectFoundation
            Build-AssetPromotionCloseout -Strict
        }
        "lpc-foundation" { Ensure-LpcDependency; Ensure-UniversalLpcDependency; Build-LpcProjectFoundation; Build-AssetPromotionCloseout -Strict }
        "oga-prototypes" { Sync-OgaLpcPrototypes }
        "asset-sources" { Ensure-LpcDependency; Ensure-UniversalLpcDependency; Sync-OgaLpcPrototypes; Build-LpcProjectFoundation; Build-AssetPromotionCloseout -Strict }
        "asset-promotion-audit" { Build-AssetPromotionCloseout }
        "asset-truth" { Build-AssetTruthInventory }
        "published-assets" { Validate-PublishedWorldAssetAuthority }
        "asset-acceptance" { Build-WorldAssetAcceptance }
        "exact-source" { Validate-ExactSourcePixelStudioAuthority }
        "structure-sources" { Build-StructureSourceInventory }
        "structure-components" { Build-StructureComponentCertification }
        "structure-surfaces" { Build-StructureSurfaceCertification }
        "structure-roof-trim" { Build-StructureRoofTrimCertification }
        "structure-roof-review" { Build-ExactRoofReviewEvidence }
        "structure-support-review" { Build-StructureSupportReviewEvidence }
        "structure-exact-modules" { Build-ExactStructureModules }
        "building-recipes" { Build-BuildingRecipes }
        "building-instances" { Build-BuildingInstances }
        "building-persistence" { Build-BuildingPersistence }
        "building-interiors" { Build-BuildingInteriors }
        "production-tavern" { Build-ProductionTavern }
        "cave-assets" { Build-CaveAssets }
        "cave-resolver" { Build-CaveResolver }
        "structural-connectors" { Build-StructuralConnectors }
        "world-visual-certification" { Build-WorldVisualCertification }
        "estate-regeneration" { Build-HomeEstateRegeneration }
        "cliff-height-grammar" { Build-CliffHeightGrammar }
        "estate-composition" { Build-EstateComposition }
        "building-exterior" { Build-BuildingExterior }
        "building-exterior-evidence" { Build-BuildingExteriorEvidence }
        "building-exterior-selections" { Build-BuildingExteriorSelections }
        "visual-checkpoint" { Build-VisualCheckpoint }
        "estate-visual-test" { Invoke-EstateVisualTest }
        "asset-bake" { Build-AssetIntake }
        "tiles" { Ensure-LpcDependency; Build-TerrainLibraries }
        "web" { Test-Web }
        "worldgen" { Test-Validation "world" }
        "editor" { Require-Command "cargo"; cargo run -p haven_editor_native -- @ExtraArgs }
        "game" { Require-Command "cargo"; cargo run -p haven_game -- @ExtraArgs }
        "devgame" { Invoke-DevelopmentWorld }
        "client" { Ensure-FrontendMusic; Build-ClientBinary }
        "apps" { Ensure-FrontendMusic; Build-ApplicationBinaries }
        "fmt" { Require-Command "cargo"; Invoke-Step "cargo fmt --all" { cargo fmt --all } }
        { $_ -in "help", "-h", "--help" } {
            Write-Host "Usage: tools/build/Build.cmd [all|rust|check|test|validate [domain]|character-audit|catalog|asset-sources|asset-promotion-audit|asset-truth|published-assets|asset-acceptance|exact-source|structure-sources|structure-components|structure-surfaces|structure-roof-trim|structure-roof-review|structure-support-review|structure-exact-modules|building-recipes|building-instances|building-persistence|building-interiors|production-tavern|cave-assets|cave-resolver|structural-connectors|world-visual-certification|estate-regeneration|cliff-height-grammar|estate-composition|building-exterior|building-exterior-evidence|building-exterior-selections|visual-checkpoint|estate-visual-test|lpc-sync|lpc-audit|lpc-foundation|asset-bake|tiles|web|worldgen|editor|game|devgame|client|apps|fmt|help]"
        }
        default { throw "Unknown build command: $Command" }
    }
}
finally {
    Pop-Location
    if ($TranscriptStarted) {
        try {
            Stop-Transcript | Out-Null
        }
        catch {
            Write-Warning "Unable to close PowerShell transcript cleanly: $($_.Exception.Message)"
        }
    }
    Write-Host "Havenwild build log: $LogPath"
}
