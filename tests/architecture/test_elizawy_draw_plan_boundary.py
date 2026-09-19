"""Contract-only approval boundary; these tests do NOT certify any terrain art."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

class DrawPlanBoundaryTests(unittest.TestCase):
    def test_original_source_and_semantic_debug_are_separate(self):
        contract=json.loads((ROOT/'content/architecture/havenwild_elizawy_draw_plan_publication_v0_1.json').read_text())
        self.assertEqual(contract['status'],'CONTRACT_ONLY_NO_PRODUCTION_DRAW_PLAN_OR_PIE')
        self.assertFalse(contract['inputConstraints']['crossFamilyFallback'])
        self.assertTrue(contract['inputConstraints']['noImplicitTransforms'])
        self.assertIn('unmapped scene cells fail production publish, remain visible in authoring',
                      contract['publicationRequirements'])
        self.assertIn('sourceRectPx',contract['requiredDrawCallFields'])
        self.assertIn('collisionRef',contract['requiredNonDrawFields'])

    def test_candidate_reports_semantic_debug_not_approved_renderer(self):
        d=json.loads((ROOT/'content/architecture/havenwild_bevy_experimental_candidate_v0_1.json').read_text())
        self.assertEqual(d['pass'],'B48R28C3')
        self.assertFalse(d['sourceIntake']['approvedArtRoles'])
        self.assertEqual(d['authority']['candidateSaveWriter'],'disabled')
        self.assertEqual(d['authority']['originalSourceModification'],'prohibited')
        self.assertIn('experimental.bevy.scene-plan',d['projectOperations']['registeredKeys'])
        self.assertIn('experimental.bevy.draft-plan',d['projectOperations']['registeredKeys'])
        draft=json.loads((ROOT/'content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json').read_text())
        self.assertFalse(draft['sourceArtApproval'])
        self.assertFalse(draft['runtimePublicationAllowed'])
        self.assertEqual(draft['selectionPolicy'],'EXPLICIT_FIRST_CELL_ONLY_NO_ADJACENCY_NO_AUTOTILE')
        text=(ROOT/'experiments/haven_bevy_candidate/src/main.rs').read_text()
        self.assertIn('SEMANTIC_DEBUG_ONLY_NOT_RENDERER_PARITY',text)
        self.assertIn('UNMAPPED_ELIZAWY_REVIEW_REQUIRED',text)
        self.assertIn('World elevation: UNKNOWN',text)
        self.assertIn('UNAPPROVED DRAFT',text)
        self.assertIn('TextureAtlasLayout::from_grid',text)
        self.assertIn('RenderLayers::layer(2)',text)
        self.assertNotIn('fn save_world(',text)

if __name__=='__main__': unittest.main()
