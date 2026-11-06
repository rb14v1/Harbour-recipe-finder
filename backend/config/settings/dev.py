"""
Development settings.

Defaults to SQLite unless USE_SQLITE=False is explicitly set in the
environment, so local work (and the test suite) runs with zero external
dependencies. Set USE_SQLITE=False and provide POSTGRES_* env vars to
exercise the real Postgres + pgvector path (requires pgvector installed on
the target Postgres server).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE the setdefault below, so an explicit USE_SQLITE=False in
# .env actually takes effect. load_dotenv() never overrides a variable that
# is already set in os.environ (override=False is its default) — if the
# setdefault ran first, USE_SQLITE would always resolve to "True" here
# regardless of what .env says, silently defeating the Postgres/pgvector
# dev path entirely. base.py calls load_dotenv() again when imported below;
# that second call is a harmless no-op since the values are already loaded.
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
os.environ.setdefault("USE_SQLITE", "True")

from .base import *  # noqa: E402,F401,F403

DEBUG = True
