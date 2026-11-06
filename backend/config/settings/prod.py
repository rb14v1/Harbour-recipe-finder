"""
Production settings. Always Postgres + pgvector; USE_SQLITE is ignored here
by forcing it off regardless of environment to prevent an accidental SQLite
deploy.
"""
import os

os.environ["USE_SQLITE"] = "False"

from .base import *  # noqa: E402,F401,F403

DEBUG = False
