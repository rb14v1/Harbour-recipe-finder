from django.test import TestCase, override_settings

from apps.common.ai import generate_answer, get_embedding
from apps.common.vector_search import similarity_search


class EmbeddingStubTests(TestCase):
    """OPENAI_API_KEY is unset in the test environment, so get_embedding
    runs in deterministic stub mode."""

    def test_stub_embedding_is_deterministic(self):
        v1 = get_embedding("chicken and broccoli")
        v2 = get_embedding("chicken and broccoli")
        self.assertEqual(v1, v2)

    def test_stub_embedding_differs_for_different_text(self):
        v1 = get_embedding("chicken and broccoli")
        v2 = get_embedding("beef and potatoes")
        self.assertNotEqual(v1, v2)

    def test_stub_embedding_has_configured_dimensions(self):
        from django.conf import settings

        vector = get_embedding("anything")
        self.assertEqual(len(vector), settings.EMBEDDING_DIMENSIONS)

    def test_stub_embedding_is_unit_normalized(self):
        import math

        vector = get_embedding("normalize me")
        norm = math.sqrt(sum(x * x for x in vector))
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_generate_answer_stub_format(self):
        answer = generate_answer("chicken", ["Chicken Stir-Fry: chicken, broccoli, soy sauce"])
        self.assertIn("[STUB AI RESPONSE", answer)
        self.assertIn("Found 1 matching recipe(s)", answer)
        self.assertIn("Chicken Stir-Fry", answer)

    def test_generate_answer_stub_no_matches(self):
        answer = generate_answer("nonexistent dish", [])
        self.assertIn("Found 0 matching recipe(s)", answer)
        self.assertIn("Try: none", answer)


class _FakeObj:
    """Minimal stand-in exposing an `embedding` attribute, used to test
    similarity_search's pure-Python (SQLite) path in isolation from the
    Recipe model/queryset."""

    def __init__(self, name, embedding):
        self.name = name
        self.embedding = embedding

    def __repr__(self):
        return f"_FakeObj({self.name!r})"


@override_settings(USE_SQLITE=True)
class SimilaritySearchRankingTests(TestCase):
    def test_nearest_first_with_known_vectors(self):
        query = [1.0, 0.0, 0.0]
        exact_match = _FakeObj("exact", [1.0, 0.0, 0.0])
        close_match = _FakeObj("close", [0.9, 0.1, 0.0])
        orthogonal = _FakeObj("orthogonal", [0.0, 1.0, 0.0])
        opposite = _FakeObj("opposite", [-1.0, 0.0, 0.0])

        candidates = [opposite, orthogonal, close_match, exact_match]

        results = similarity_search(candidates, query, top_k=4, field_name="embedding")

        self.assertEqual([r.name for r in results], ["exact", "close", "orthogonal", "opposite"])
        self.assertAlmostEqual(results[0].similarity_score, 1.0, places=6)
        self.assertAlmostEqual(results[-1].similarity_score, -1.0, places=6)

    def test_top_k_slicing(self):
        query = [1.0, 0.0]
        candidates = [
            _FakeObj("a", [1.0, 0.0]),
            _FakeObj("b", [0.7, 0.7]),
            _FakeObj("c", [0.0, 1.0]),
        ]
        results = similarity_search(candidates, query, top_k=2, field_name="embedding")
        self.assertEqual(len(results), 2)
        self.assertEqual([r.name for r in results], ["a", "b"])

    def test_skips_objects_with_no_embedding(self):
        query = [1.0, 0.0]
        candidates = [
            _FakeObj("has_embedding", [1.0, 0.0]),
            _FakeObj("no_embedding", None),
        ]
        results = similarity_search(candidates, query, top_k=5, field_name="embedding")
        self.assertEqual([r.name for r in results], ["has_embedding"])
