"""
Backend-agnostic vector embedding field.

Postgres (production path): a real `pgvector.django.VectorField`, which
requires the `vector` extension to be installed on the Postgres server (see
the migration guard pattern used in apps/recipes/migrations/0001_initial.py).

SQLite (dev/local/test path, USE_SQLITE=True): pgvector has no SQLite
backend, so we fall back to a plain `JSONField` storing a list of floats.
`apps.common.vector_search.similarity_search` knows how to handle both
representations transparently, so application code never needs to branch
on the backend itself.

Usage in a model:

    from apps.common.embedding_field import EmbeddingField, EMBEDDING_DIMENSIONS

    class Recipe(models.Model):
        embedding = EmbeddingField(null=True, blank=True)
"""
from django.conf import settings
from django.db import models

# Default dimensionality for stored embeddings. OpenAI's
# text-embedding-3-large is natively 3072-dimensional but supports the
# `dimensions` parameter to shorten the output (Matryoshka representation
# learning), so 1536 is a reasonable, configurable default.
EMBEDDING_DIMENSIONS = getattr(settings, "EMBEDDING_DIMENSIONS", 1536)


def EmbeddingField(**kwargs):
    """
    Factory returning the correct field type for the active DB backend.

    Chosen via settings.USE_SQLITE at class-definition time (i.e. when
    models.py is imported), matching the backend configured in
    config/settings/base.py.
    """
    if getattr(settings, "USE_SQLITE", False):
        return models.JSONField(**kwargs)

    # Imported lazily so environments without pgvector installed (e.g. a
    # SQLite-only dev machine that never installed the postgres extras)
    # never need to import pgvector.django at all.
    from pgvector.django import VectorField

    return VectorField(dimensions=EMBEDDING_DIMENSIONS, **kwargs)
