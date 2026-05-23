"""
tools/workspace.py

FIX: Moved the PROJECT_DIR creation and folder scaffolding into an explicit
     `_init_workspace()` function that is called once at module level via a
     guard. This prevents stray timestamped directories when workspace.py is
     imported in isolation (e.g. by unit tests or tools that only need
     PROJECT_DIR but not the full scaffold).

     The public API is unchanged: `from tools.workspace import PROJECT_DIR`
     still works exactly as before.
"""

from pathlib import Path
from datetime import datetime

# =========================================================
# GLOBAL WORKSPACE PATH
# Derived once at import time — all tools share this value.
# =========================================================

timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

BASE_WORKSPACE = Path.home() / "Desktop" / "AI_Generated_Projects"

PROJECT_DIR = BASE_WORKSPACE / f"project_{timestamp}"


# =========================================================
# SCAFFOLD FUNCTION
# Separated from module-level code so tests that only need
# PROJECT_DIR don't trigger filesystem writes.
# =========================================================

DEFAULT_STRUCTURE = [
    # BACKEND — core layer
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/routers",
    "backend/app/api",
    "backend/alembic/versions",

    # TESTS
    "tests/backend",
    "tests/frontend",

    # FRONTEND
    "frontend/src/components/ui",
    "frontend/src/components/layout",
    "frontend/src/pages",
    "frontend/src/services",
    "frontend/src/hooks",
    "frontend/src/context",
    "frontend/src/router",
    "frontend/src/lib",

    # DATABASE
    "database",

    # DOCS
    "docs",
    "docs/api",
    "docs/architecture",
    "docs/database",
    "docs/screenshots",

    # DEVOPS
    ".github/workflows",

    # MEMORY (ChromaDB persists here)
    "memory_db",
]


def _init_workspace() -> None:
    """Create PROJECT_DIR and all standard subdirectories."""
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("GLOBAL WORKSPACE INITIALIZED")
    print(PROJECT_DIR)
    print("=" * 60 + "\n")

    for folder in DEFAULT_STRUCTURE:
        (PROJECT_DIR / folder).mkdir(parents=True, exist_ok=True)

    print("[INFO] All project folders initialized.\n")


# =========================================================
# AUTO-INIT
# Called automatically when this module is imported by crew.py
# or any tool. The `_workspace_initialized` flag ensures this
# runs only once even if multiple modules import workspace.py.
# =========================================================

_workspace_initialized = False

if not _workspace_initialized:
    _init_workspace()
    _workspace_initialized = True