"""
Backend-agnostic similarity search.

On Postgres, pgvector lets us push the nearest-neighbour search down into
the database via `CosineDistance(...)` in an `.order_by()` clause -- fast
and index-friendly (with an ivfflat/hnsw index on the embedding column).

On SQLite there is no vector extension, so we pull the candidate rows back
and compute cosine similarity in plain Python, then sort and slice. This is
fine for small dev/test datasets and keeps the call signature identical
across both backends so calling code never branches on DB vendor.
"""
import math

from django.conf import settings


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def similarity_search(queryset, query_vector, top_k=5, field_name="embedding"):
    """
    Return the top_k objects in `queryset` most similar to `query_vector`,
    nearest first, each annotated with a `.similarity_score` attribute
    (cosine similarity, higher is better, range [-1, 1]).

    Works identically whether `field_name` is a real pgvector VectorField
    (Postgres) or a JSONField storing a list of floats (SQLite dev mode).
    """
    if not getattr(settings, "USE_SQLITE", False):
        from pgvector.django import CosineDistance

        annotated = queryset.exclude(**{f"{field_name}__isnull": True}).annotate(
            _distance=CosineDistance(field_name, query_vector)
        ).order_by("_distance")[:top_k]
        results = list(annotated)
        for obj in results:
            # cosine distance = 1 - cosine similarity
            obj.similarity_score = 1 - obj._distance
        return results

    # --- SQLite / pure-Python path ---
    candidates = [
        obj for obj in queryset if getattr(obj, field_name, None)
    ]
    scored = []
    for obj in candidates:
        vector = getattr(obj, field_name)
        score = _cosine_similarity(query_vector, vector)
        obj.similarity_score = score
        scored.append(obj)

    scored.sort(key=lambda o: o.similarity_score, reverse=True)
    return scored[:top_k]
