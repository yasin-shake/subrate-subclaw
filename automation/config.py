"""Central configuration for the Instagram scrape automation.

Everything here can be overridden with environment variables so the code holds
no secrets and is safe to commit.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Device / node -----------------------------------------------------------
# The ClawPaw node id. Override with OPENCLAW_NODE_ID rather than editing this.
NODE_ID: str = os.environ.get(
    "OPENCLAW_NODE_ID",
    "c5a797c91d282f1c4d0d8c03e41cd797dfbc373592494ccd8f68520c3e9947fe",
)

# Path to the `openclaw` executable. Resolved via PATH if left as the name.
OPENCLAW_BIN: str = os.environ.get("OPENCLAW_BIN", "openclaw")

# Reference device geometry. Coordinates are always recomputed from live element
# bounds; these are only fallbacks for blind gestures (e.g. scroll distances).
DEVICE_W = 1080
DEVICE_H = 2340

IG_PACKAGE = "com.instagram.android"

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"           # per-run artifacts (layouts, screenshots, csv)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# Where the ClawPaw skill guides live. The escalation agent may patch these.
SKILLS_GUIDES_DIR = Path(
    os.environ.get(
        "CLAWPAW_GUIDES_DIR",
        r"C:\Users\User\.openclaw\workspace\skills\clawpaw-android-control\references\guides",
    )
)

# --- Behaviour knobs ---------------------------------------------------------
INVOKE_TIMEOUT_S = int(os.environ.get("OC_INVOKE_TIMEOUT_S", "30"))
AGENT_TIMEOUT_S = int(os.environ.get("OC_AGENT_TIMEOUT_S", "600"))

# Fixed session id for the escalation/recovery agent turns.
AGENT_SESSION_ID = os.environ.get("OC_AGENT_SESSION_ID", "subclaw-recovery")

# How many times to retry a verified swipe (advance) before giving up / escalating.
MAX_ADVANCE_TRIES = 4

# Set OC_ESCALATE=0 to disable the LLM escalation hook (capture-only on failure).
ESCALATION_ENABLED = os.environ.get("OC_ESCALATE", "1") != "0"
