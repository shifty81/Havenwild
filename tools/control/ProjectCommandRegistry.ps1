@(
    @{ Id='1'; Key='project.status';  Label='Project status';                  Kind='Script'; Script='ProjectStatus.ps1';       Category='sessions';    Menu=@('project'); MenuOrder=10; Args=@() }
    @{ Id='2'; Key='build.all';  Label='Build all';                       Kind='Build';  Category='builds';     Menu=@('build'); MenuOrder=20; Args=@('all') }
    @{ Id='3'; Key='build.check-editor';  Label='Check native editor/workspace';   Kind='Build';  Category='builds';     Menu=@('build'); MenuOrder=50; Args=@('check') }
    @{ Id='4'; Key='build.client-apps';  Label='Build client applications';       Kind='Build';  Category='builds';     Menu=@('build'); MenuOrder=60; Args=@('apps') }
    @{ Id='5'; Key='run.editor';  Label='Run native editor';               Kind='Build';  Category='builds';     Menu=@('run'); MenuOrder=10; Args=@('editor') }
    @{ Id='6'; Key='run.game';  Label='Run game client';                 Kind='Build';  Category='builds';     Menu=@('run'); MenuOrder=20; Args=@('game') }
    @{ Id='7'; Key='maintenance.clean';  Label='Clean build outputs';             Kind='Script'; Script='WorkspaceMaintenance.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=30; Args=@('-Action','clean') }
    @{ Id='8'; Key='maintenance.repair';  Label='Repair workspace';                Kind='Script'; Script='WorkspaceMaintenance.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=40; Args=@('-Action','repair') }
    @{ Id='9'; Key='validate.source';  Label='Validate current source';                Kind='Build';  Category='validation'; Menu=@('build'); MenuOrder=40; Args=@('validate','all') }
    @{ Id='10'; Key='test.workspace'; Label='Run tests';                       Kind='Build';  Category='validation'; Menu=@('build'); MenuOrder=30; Args=@('test') }
    @{ Id='11'; Key='logs.active-session'; Label='View active session log';         Kind='LatestLog'; Category='sessions'; Menu=@('logs'); MenuOrder=10; Args=@() }
    @{ Id='12'; Key='logs.open-folder'; Label='Open logs folder';                Kind='Open'; Path='logs'; Category='sessions'; Menu=@('logs'); MenuOrder=40; Args=@() }
    @{ Id='13'; Key='assets.refresh-catalog'; Label='Refresh asset catalog';           Kind='Build'; Category='assets'; Menu=@('assets'); MenuOrder=10; Args=@('catalog') }
    @{ Id='14'; Key='package.incremental-patch'; Label='Package incremental patch';       Kind='Package'; Mode='patch'; Category='packaging'; Menu=@('package'); MenuOrder=10; Args=@() }
    @{ Id='15'; Key='package.source-rollup'; Label='Package lean complete source rollup';  Kind='Package'; Mode='rollup'; Category='packaging'; Menu=@('package'); MenuOrder=20; Args=@() }
    @{ Id='16'; Key='package.capture-baseline'; Label='Capture package baseline';        Kind='Package'; Mode='baseline'; Category='packaging'; Menu=@('package'); MenuOrder=30; Args=@() }
    @{ Id='17'; Key='doctor.environment'; Label='Environment doctor';               Kind='EnvironmentDoctor'; Category='diagnostics'; Menu=@('project'); MenuOrder=50; Args=@() }
    @{ Id='18'; Key='assets.sync-lpc'; Label='Sync and audit all LPC sources';    Kind='Build'; Category='assets'; Menu=@('assets'); MenuOrder=20; Args=@('asset-sources') }
    @{ Id='19'; Key='audit.root-cleanliness'; Label='Root cleanliness audit';          Kind='Script'; Script='AuditRoot.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=60; Args=@() }
    @{ Id='20'; Key='audit.normalization'; Label='Project-wide normalization audit';Kind='Script'; Script='NormalizationAudit.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=70; Args=@() }
    @{ Id='21'; Key='audit.terrain-tuples'; Label='Terrain tuple catalog audit';     Kind='Script'; Script='TerrainTupleAudit.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=80; Args=@() }
    @{ Id='22'; Key='assets.rebuild-terrain-atlas'; Label='Rebuild terrain runtime atlas';   Kind='Script'; Script='RebuildTerrainAtlas.ps1'; Category='assets'; Menu=@('world'); MenuOrder=220; Args=@() }
    @{ Id='23'; Key='audit.terrain-acceptance'; Label='Terrain acceptance audit';       Kind='Script'; Script='TerrainAcceptanceAudit.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=90; Args=@() }
    @{ Id='24'; Key='audit.terrain-gameplay'; Label='Terrain gameplay audit';         Kind='Script'; Script='TerrainGameplayAudit.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=100; Args=@() }
    @{ Id='25'; Key='audit.terrain-certification'; Label='Terrain certification audit';      Kind='Script'; Script='TerrainCertificationAudit.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=110; Args=@() }
    @{ Id='26'; Key='certify.terrain-pipeline'; Label='Certify terrain pipeline';         Kind='Script'; Script='CertifyTerrainPipeline.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=120; Args=@() }
    @{ Id='27'; Key='terrain.generate-acceptance-scenes'; Label='Generate terrain acceptance scenes'; Kind='Script'; Script='GenerateTerrainAcceptanceScenes.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=130; Args=@() }
    @{ Id='28'; Key='terrain.collect-certification-evidence'; Label='Collect terrain certification evidence'; Kind='Script'; Script='CollectTerrainCertificationEvidence.ps1'; Category='diagnostics'; Menu=@('project'); MenuOrder=140; Args=@() }
    @{ Id='29'; Key='project.open-folder'; Label='Open project folder';             Kind='Open'; Path='.'; Category='sessions'; Menu=@('project'); MenuOrder=150; Args=@() }
    @{ Id='30'; Key='help.advanced'; Label='Advanced commands/help';          Kind='Help'; Category='sessions'; Menu=@('logs'); MenuOrder=50; Args=@() }
    @{ Id='31'; Key='assets.rebuild-promotion-matrix'; Label='Rebuild asset promotion matrix';   Kind='Build'; Category='assets'; Menu=@('assets'); MenuOrder=30; Args=@('asset-promotion-audit') }
    @{ Id='32'; Key='run.development-world'; Label='Run development world';          Kind='Build';  Category='builds';     Menu=@('run'); MenuOrder=30; Args=@('devgame') }
    @{ Id='33'; Key='assets.world-truth-inventory'; Label='Build world asset truth inventory'; Kind='Build'; Category='assets'; Menu=@('assets','world'); MenuOrder=40; Args=@('asset-truth') }
    @{ Id='34'; Key='assets.validate-published-world'; Label='Validate published world asset authority'; Kind='Build'; Category='assets'; Menu=@('assets','world'); MenuOrder=50; Args=@('published-assets') }
    @{ Id='35'; Key='assets.world-acceptance-scenes'; Label='Build world asset acceptance scenes'; Kind='Build'; Category='assets'; Menu=@('assets','world'); MenuOrder=60; Args=@('asset-acceptance') }
    @{ Id='36'; Key='assets.validate-exact-source-pixel'; Label='Validate exact-source Pixel Studio authority'; Kind='Build'; Category='assets'; Menu=@('assets','world'); MenuOrder=70; Args=@('exact-source') }
    @{ Id='37'; Key='structures.source-certification-queue'; Label='Build structural source certification queue'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=370; Args=@('structure-sources') }
    @{ Id='38'; Key='structures.component-certification'; Label='Build structural component certification'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=380; Args=@('structure-components') }
    @{ Id='39'; Key='structures.surface-certification'; Label='Build structural surface certification'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=390; Args=@('structure-surfaces') }
    @{ Id='40'; Key='structures.roof-wall-certification'; Label='Build roof topology + wall-border certification'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=400; Args=@('structure-roof-trim') }
    @{ Id='41'; Key='structures.roof-review-evidence'; Label='Build exact roof review evidence bundle'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=410; Args=@('structure-roof-review') }
    @{ Id='42'; Key='structures.support-review-evidence'; Label='Build exact structure support review evidence bundle'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=420; Args=@('structure-support-review') }
    @{ Id='43'; Key='structures.exact-module-acceptance'; Label='Build exact roof + support publication acceptance'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=430; Args=@('structure-exact-modules') }
    @{ Id='44'; Key='buildings.recipe-authority'; Label='Build building recipe authority'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=440; Args=@('building-recipes') }
    @{ Id='45'; Key='buildings.instance-runtime'; Label='Build native building instance runtime'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=450; Args=@('building-instances') }
    @{ Id='46'; Key='buildings.persistence-authority'; Label='Build building placement + persistence authority'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=460; Args=@('building-persistence') }
    @{ Id='47'; Key='buildings.interior-grammar'; Label='Validate same-world building interior grammar'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=470; Args=@('building-interiors') }
    @{ Id='48'; Key='buildings.production-tavern'; Label='Build production tavern acceptance'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=480; Args=@('production-tavern') }
    @{ Id='49'; Key='caves.asset-authority'; Label='Validate cave asset authority'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=490; Args=@('cave-assets') }
    @{ Id='50'; Key='caves.resolver-pcg-acceptance'; Label='Build cave resolver + PCG acceptance'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=500; Args=@('cave-resolver') }
    @{ Id='51'; Key='structures.connector-acceptance'; Label='Build structural connector acceptance'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=510; Args=@('structural-connectors') }
    @{ Id='52'; Key='world.visual-certification'; Label='Build world visual certification'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=520; Args=@('world-visual-certification') }
    @{ Id='53'; Key='estate.regenerate-validate'; Label='Regenerate + validate Home Estate'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=530; Args=@('estate-regeneration') }
    @{ Id='54'; Key='run.estate-visual-test'; Label='Run integrated Estate visual test'; Kind='Build'; Category='builds'; Menu=@('run'); MenuOrder=40; Args=@('estate-visual-test') }
    @{ Id='55'; Key='cliffs.height-grammar-acceptance'; Label='Build cliff height grammar acceptance'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=550; Args=@('cliff-height-grammar') }
    @{ Id='56'; Key='estate.regenerate-composition'; Label='Regenerate Estate composition'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=560; Args=@('estate-composition') }
    @{ Id='57'; Key='buildings.exterior-grammar'; Label='Validate building exterior grammar'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=570; Args=@('building-exterior') }
    @{ Id='58'; Key='validate.integrated-visual-checkpoint'; Label='Validate integrated visual checkpoint'; Kind='Build'; Category='validation'; Menu=@(); MenuOrder=160; Args=@('visual-checkpoint') }
    @{ Id='59'; Key='buildings.exterior-review-evidence'; Label='Build exact exterior review evidence'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=590; Args=@('building-exterior-evidence') }
    @{ Id='60'; Key='buildings.exterior-selection-validation'; Label='Validate exact exterior selections'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=600; Args=@('building-exterior-selections') }
    @{ Id='61'; Key='buildings.starter-cottage-layout'; Label='Validate starter cottage production layout'; Kind='Build'; Category='assets'; Menu=@('world'); MenuOrder=610; Args=@('starter-cottage') }
    @{ Id='62'; Key='validate.cottage-estate-visual-repair'; Label='Validate cottage + Estate visual repair'; Kind='Build'; Category='validation'; Menu=@(); MenuOrder=170; Args=@('cottage-visual-repair') }
    @{ Id='63'; Key='package.authoring-changes'; Label='Package authoring changes'; Kind='Script'; Script='PackageAuthoringChanges.ps1'; Category='packaging'; Menu=@('package'); MenuOrder=40; Args=@() }
    @{ Id='64'; Key='recovery.create'; Label='Create backup/recovery rollup'; Kind='Script'; Script='CreateRecoveryRollup.ps1'; Category='packaging'; Menu=@('package'); MenuOrder=50; Args=@() }
    @{ Id='66'; Key='package.open-folder'; Label='Open source/packages folder'; Kind='Open'; Path='artifacts\packages'; Category='packaging'; Menu=@('package'); MenuOrder=80; Args=@() }
    @{ Id='65'; Key='recovery.open-folder'; Label='Open recovery rollups folder'; Kind='Open'; Path='artifacts\recovery'; Category='packaging'; Menu=@('package'); MenuOrder=90; Args=@() }
    @{ Id='67'; Key='validation.full-quality-gate'; Label='Full quality gate (run-scoped logs + root audit + build + tests + debug ZIP)'; Kind='BuiltinQualityGate'; Category='validation'; Menu=@('build'); MenuOrder=10; Args=@() }
    @{ Id='68'; Key='package.open-latest-source-rollup'; Label='Open latest source rollup'; Kind='OpenArtifact'; Artifact='source-rollup'; Category='packaging'; Menu=@('package'); MenuOrder=60; Args=@() }
    @{ Id='69'; Key='recovery.open-latest-rollup'; Label='Open latest recovery rollup'; Kind='OpenArtifact'; Artifact='recovery'; Category='packaging'; Menu=@('package'); MenuOrder=70; Args=@() }
    @{ Id='70'; Key='logs.open-latest-debug-bundle'; Label='Open latest debug bundle'; Kind='OpenArtifact'; Artifact='debug-bundle'; Category='sessions'; Menu=@('logs'); MenuOrder=20; Args=@() }
    @{ Id='71'; Key='artifacts.open-index'; Label='Open artifact index'; Kind='OpenArtifact'; Artifact='artifact-index'; Category='sessions'; Menu=@('logs'); MenuOrder=30; Args=@() }
    @{ Id='72'; Key='control.self-test'; Label='Control Center self-test'; Kind='ControlSelfTest'; Category='diagnostics'; Menu=@('project'); MenuOrder=20; Args=@() }
    @{ Id='73'; Key='validation.quality-gate-history'; Label='Quality gate history'; Kind='QualityGateHistory'; Category='diagnostics'; Menu=@('logs'); MenuOrder=25; Args=@() }
    @{ Id='74'; Key='updates.status'; Label='Patch / update status'; Kind='UpdateStatus'; Category='updates'; Menu=@('project'); MenuOrder=25; Args=@() }
    @{ Id='75'; Key='recovery.inspect-latest'; Label='Inspect latest recovery rollup'; Kind='RecoveryInspect'; Category='diagnostics'; Menu=@('package'); MenuOrder=75; Args=@() }
    @{ Id='76'; Key='validation.open-latest-quality-gate'; Label='Open latest quality gate record'; Kind='OpenArtifact'; Artifact='quality-gate'; Category='sessions'; Menu=@('logs'); MenuOrder=27; Args=@() }
    @{ Id='77'; Key='updates.open-latest-failed'; Label='Open latest failed update'; Kind='OpenArtifact'; Artifact='failed-update'; Category='updates'; Menu=@('logs'); MenuOrder=35; Args=@() }
    @{ Id='78'; Key='recovery.preview-undo-latest'; Label='Preview undo latest root patch'; Kind='Script'; Script='RestoreLatestPatchBackup.ps1'; Category='updates'; Menu=@('project'); MenuOrder=27; Args=@('-Mode','Preview') }
    @{ Id='79'; Key='recovery.undo-latest'; Label='Undo latest root patch (transactional)'; Kind='Script'; Script='RestoreLatestPatchBackup.ps1'; Category='updates'; Menu=@('project'); MenuOrder=28; Args=@('-Mode','Restore') }
    @{ Id='80'; Key='updates.open-undone-folder'; Label='Open undone update archives'; Kind='Open'; Path='artifacts\updates\undone'; Category='updates'; Menu=@('project'); MenuOrder=29; Args=@() }
    @{ Id='81'; Key='updates.open-last-undo-record'; Label='Open last patch-undo record'; Kind='OpenArtifact'; Artifact='undo-record'; Category='updates'; Menu=@('logs'); MenuOrder=37; Args=@() }
    @{ Id='82'; Key='validation.fast-quality-gate'; Label='Fast development gate (patch intake + root audit + self-test + cargo check)'; Kind='BuiltinFastQualityGate'; Category='validation'; Menu=@('build'); MenuOrder=15; Args=@() }
    @{ Id='83'; Key='validation.compare-quality-gates'; Label='Compare latest Full Quality Gates'; Kind='QualityGateCompare'; Category='diagnostics'; Menu=@('logs'); MenuOrder=26; Args=@() }
    @{ Id='84'; Key='diagnostics.compiler-warnings'; Label='Compiler warning summary'; Kind='CompilerWarningSummary'; Category='diagnostics'; Menu=@('logs'); MenuOrder=28; Args=@() }
    @{ Id='85'; Key='validation.open-latest-fast-gate'; Label='Open latest Fast Development Gate record'; Kind='OpenArtifact'; Artifact='fast-gate'; Category='sessions'; Menu=@('logs'); MenuOrder=29; Args=@() }
)
