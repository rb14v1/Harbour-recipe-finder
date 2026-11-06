from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Recipe

User = get_user_model()


class SeedMigrationTests(APITestCase):
    """The recipes.0002_seed_data data migration runs as part of building
    the test database (Django applies all migrations, including data
    migrations, when creating it), so the demo user/recipes should already
    be present here without any setUp."""

    def test_demo_user_exists(self):
        self.assertTrue(User.objects.filter(email="demo@example.com").exists())

    def test_demo_user_password(self):
        user = User.objects.get(email="demo@example.com")
        self.assertTrue(user.check_password("demo12345"))

    def test_seed_recipe_count(self):
        user = User.objects.get(email="demo@example.com")
        self.assertEqual(Recipe.objects.filter(user=user).count(), 13)

    def test_seed_recipes_have_full_length_embeddings(self):
        user = User.objects.get(email="demo@example.com")
        for recipe in Recipe.objects.filter(user=user):
            self.assertIsNotNone(recipe.embedding)
            self.assertEqual(len(recipe.embedding), settings.EMBEDDING_DIMENSIONS)


class CrossUserIsolationTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username="alice@example.com", email="alice@example.com", password="pw12345678"
        )
        self.user_b = User.objects.create_user(
            username="bob@example.com", email="bob@example.com", password="pw12345678"
        )
        self.recipe_a = Recipe.objects.create(
            user=self.user_a,
            title="Alice's Secret Chicken Soup",
            ingredients="chicken, carrot, celery, onion",
            instructions="Simmer everything together for an hour.",
        )
        self.recipe_b = Recipe.objects.create(
            user=self.user_b,
            title="Bob's Secret Beef Stew",
            ingredients="beef, potato, carrot",
            instructions="Braise for two hours.",
        )

    def test_recipe_list_only_shows_own_recipes(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/recipes/")
        self.assertEqual(response.status_code, 200)
        titles = [r["title"] for r in response.data]
        self.assertIn("Alice's Secret Chicken Soup", titles)
        self.assertNotIn("Bob's Secret Beef Stew", titles)

    def test_recipe_detail_404s_for_other_users_recipe(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f"/api/recipes/{self.recipe_b.id}/")
        self.assertEqual(response.status_code, 404)

    def test_search_never_surfaces_another_users_recipes(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/search/", {"query": "chicken soup"}, format="json")
        self.assertEqual(response.status_code, 200)
        matched_ids = [m["recipe_id"] for m in response.data["matches"]]
        self.assertIn(self.recipe_a.id, matched_ids)
        self.assertNotIn(self.recipe_b.id, matched_ids)

        # Flip perspective: user B must never see user A's recipe either.
        self.client.force_authenticate(user=self.user_b)
        response = self.client.post("/api/search/", {"query": "beef stew"}, format="json")
        self.assertEqual(response.status_code, 200)
        matched_ids = [m["recipe_id"] for m in response.data["matches"]]
        self.assertIn(self.recipe_b.id, matched_ids)
        self.assertNotIn(self.recipe_a.id, matched_ids)


class SearchEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="carol@example.com", email="carol@example.com", password="pw12345678"
        )
        self.recipe = Recipe.objects.create(
            user=self.user,
            title="Garlic Butter Shrimp",
            ingredients="shrimp, garlic, butter, parsley, lemon",
            instructions="Saute shrimp in garlic butter until pink, finish with lemon and parsley.",
        )
        self.client.force_authenticate(user=self.user)

    def test_search_response_shape(self):
        response = self.client.post("/api/search/", {"query": "shrimp garlic"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("matches", response.data)
        self.assertIn("suggestion", response.data)
        self.assertEqual(len(response.data["matches"]), 1)
        match = response.data["matches"][0]
        self.assertEqual(match["recipe_id"], self.recipe.id)
        self.assertEqual(match["title"], "Garlic Butter Shrimp")
        self.assertIsInstance(match["score"], float)

    def test_search_suggestion_is_stub_formatted(self):
        # No OPENAI_API_KEY is configured in the test environment, so the
        # suggestion must come from the deterministic stub template.
        response = self.client.post("/api/search/", {"query": "shrimp garlic"}, format="json")
        suggestion = response.data["suggestion"]
        self.assertIn("[STUB AI RESPONSE", suggestion)
        self.assertIn("Found 1 matching recipe(s)", suggestion)
        self.assertIn("Garlic Butter Shrimp", suggestion)

    def test_search_requires_query(self):
        response = self.client.post("/api/search/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_search_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/search/", {"query": "shrimp"}, format="json")
        self.assertEqual(response.status_code, 401)


class RecipeCrudTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dave@example.com", email="dave@example.com", password="pw12345678"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_recipe_computes_embedding(self):
        response = self.client.post(
            "/api/recipes/",
            {
                "title": "Test Pancakes",
                "ingredients": "flour, milk, eggs, sugar, baking powder",
                "instructions": "Mix and cook on a griddle.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        recipe = Recipe.objects.get(id=response.data["id"])
        self.assertIsNotNone(recipe.embedding)
        self.assertEqual(len(recipe.embedding), settings.EMBEDDING_DIMENSIONS)

    def test_update_recipe_recomputes_embedding(self):
        recipe = Recipe.objects.create(
            user=self.user,
            title="Original Title",
            ingredients="a, b, c",
            instructions="do things",
        )
        original_embedding = list(recipe.embedding)
        response = self.client.put(
            f"/api/recipes/{recipe.id}/",
            {
                "title": "Updated Title",
                "ingredients": "x, y, z",
                "instructions": "do other things",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        recipe.refresh_from_db()
        # pgvector-django returns VectorField values as numpy arrays on
        # Postgres (vs plain lists from SQLite's JSONField fallback);
        # comparing arrays directly raises "ambiguous truth value" under
        # assertNotEqual, so cast to list first to compare on either backend.
        self.assertNotEqual(list(recipe.embedding), original_embedding)
