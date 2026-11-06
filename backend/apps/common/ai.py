"""
AI layer: embeddings + chat/answer generation, with a deterministic stub
fallback so the entire pipeline is testable with zero API key, zero network
access, and zero cost.

Mode is selected purely by the presence of the OPENAI_API_KEY env var:
- Set    -> real OpenAI calls (requires `openai` package + network + a key
            with available quota).
- Unset  -> deterministic stubs. The `openai` package is NOT imported at
            all in this mode, so the app works with openai uninstalled too.

IMPORTANT: the stub embedding is NOT semantically meaningful. It is a
reproducible pseudo-random vector derived from a SHA-256 hash of the input
text, purely so that the same text always yields the same vector (making
similarity_search and caching logic testable/deterministic). It captures
nothing about actual word/ingredient meaning -- two recipes about "chicken"
will NOT be close together in stub-vector space the way they would with a
real embedding model. Real semantic search quality requires a real
OPENAI_API_KEY.
"""
import hashlib
import math
import random

from django.conf import settings


def _stub_vector(text: str, dimensions: int) -> list[float]:
    seed = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rng = random.Random(seed)
    raw = [rng.uniform(-1.0, 1.0) for _ in range(dimensions)]
    norm = math.sqrt(sum(x * x for x in raw))
    if norm == 0:
        return raw
    return [x / norm for x in raw]


def get_embedding(text: str) -> list[float]:
    """
    Return an embedding vector for `text`.

    Real mode (OPENAI_API_KEY set): calls OpenAI's embeddings API using
    OPENAI_EMBEDDING_MODEL (default text-embedding-3-large), requesting
    `dimensions=EMBEDDING_DIMENSIONS` output floats.

    Stub mode (no key): deterministic SHA-256-seeded pseudo-random unit
    vector. See module docstring -- NOT semantically meaningful, only
    reproducible, so the rest of the pipeline (storage, ranking plumbing,
    endpoint shape) can be fully exercised without a key or network access.
    """
    dimensions = getattr(settings, "EMBEDDING_DIMENSIONS", 1536)
    api_key = getattr(settings, "OPENAI_API_KEY", "")

    if api_key:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        response = client.embeddings.create(
            model=model,
            input=text,
            dimensions=dimensions,
        )
        return response.data[0].embedding

    return _stub_vector(text, dimensions)


def generate_answer(question: str, context_snippets: list[str]) -> str:
    """
    Generate a grounded recipe suggestion/variation given the user's
    question and a list of context snippets (e.g. "Title: ingredients"
    strings for the top-matching recipes).

    Real mode (OPENAI_API_KEY set): calls OpenAI chat completions using
    OPENAI_CHAT_MODEL (default "gpt-5.6-sol", as configured -- wired through
    exactly as given; this model name/behaviour is unverifiable in this
    environment).

    Stub mode (no key): deterministic templated string naming how many
    matches were found and previewing the top match, so the endpoint's
    response shape and downstream UI are fully testable without a key.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "")

    if api_key:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-5.6-sol")
        context_block = "\n".join(f"- {snippet}" for snippet in context_snippets) or "(no matching recipes found)"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful cooking assistant. Suggest a recipe or a "
                    "variation of one, grounded strictly in the provided recipe "
                    "context. Be concise and practical."
                ),
            },
            {
                "role": "user",
                "content": f"User request: {question}\n\nCandidate recipes:\n{context_block}",
            },
        ]
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content

    found = len(context_snippets)
    preview = context_snippets[0][:200] if context_snippets else "none"
    return f"[STUB AI RESPONSE — set OPENAI_API_KEY for real output] Found {found} matching recipe(s). Try: {preview}"
