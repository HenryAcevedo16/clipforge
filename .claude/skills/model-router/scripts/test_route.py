"""Unit tests for ClipForge's model-router classifier."""

import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("route.py")
SPEC = importlib.util.spec_from_file_location("clipforge_model_router", SCRIPT)
ROUTER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ROUTER)


class RouteTests(unittest.TestCase):
    def test_mechanical_lookup_goes_to_haiku(self):
        result = ROUTER.route("find the timestamp helper", files_touched=1)
        self.assertEqual(result["agent"], "haiku-worker")

    def test_normal_implementation_goes_to_sonnet(self):
        result = ROUTER.route("add an export button and focused tests", files_touched=2)
        self.assertEqual(result["agent"], "sonnet-worker")

    def test_architecture_goes_to_opus(self):
        result = ROUTER.route("design cancellation across FastAPI and FFmpeg", files_touched=8)
        self.assertEqual(result["agent"], "opus-worker")

    def test_normal_review_goes_to_sonnet_reviewer(self):
        result = ROUTER.route("review this diff", files_touched=2)
        self.assertEqual(result["agent"], "sonnet-reviewer")

    def test_security_review_escalates_to_opus(self):
        result = ROUTER.route("security review of credential handling", files_touched=2)
        self.assertEqual(result["agent"], "opus-worker")

    def test_review_followup_is_implementation(self):
        result = ROUTER.route("fix the review findings", files_touched=2)
        self.assertEqual(result["agent"], "sonnet-worker")

    def test_failed_haiku_attempt_escalates_to_sonnet(self):
        result = ROUTER.route("find the timestamp helper", files_touched=1, prior_failures=1)
        self.assertEqual(result["agent"], "sonnet-worker")

    def test_failed_review_escalates_to_opus(self):
        result = ROUTER.route("review this diff", files_touched=2, prior_failures=1)
        self.assertEqual(result["agent"], "opus-worker")
    
    def test_spanish_mechanical_lookup_goes_to_haiku(self):
        result = ROUTER.route("buscar la función de timestamps", files_touched=1)
        self.assertEqual(result["agent"], "haiku-worker")

    def test_spanish_architecture_goes_to_opus(self):
        result = ROUTER.route("diseñar la arquitectura del pipeline", files_touched=2)
        self.assertEqual(result["agent"], "opus-worker")

    def test_spanish_diff_review_goes_to_reviewer(self):
        result = ROUTER.route("revisar este diff", files_touched=2)
        self.assertEqual(result["agent"], "sonnet-reviewer")

    def test_spanish_security_review_escalates_to_opus(self):
        result = ROUTER.route("revisión de seguridad de credenciales", files_touched=2)
        self.assertEqual(result["agent"], "opus-worker")

    def test_spanish_review_followup_is_implementation(self):
        result = ROUTER.route("corrige los hallazgos de la revisión", files_touched=2)
        self.assertEqual(result["agent"], "sonnet-worker")


if __name__ == "__main__":
    unittest.main()
