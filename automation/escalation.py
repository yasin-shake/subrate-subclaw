"""LLM escalation hook.

When a deterministic checkpoint fails, we don't flail. We:
  1. Snapshot the failing state (layout XML + screenshot) to the run dir.
  2. Hand it to the OpenClaw agent via `openclaw agent --json`, which already
     has access to the phone node and the ClawPaw skill guides.
  3. Ask it to (a) recover the live UI to the expected checkpoint and (b) PATCH
     the relevant skill guide if its assumptions were wrong (self-healing skills).

The deterministic driver then re-reads the layout and re-checks the checkpoint.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

import config
from checkpoints import CheckpointError

_ALLOWED = (
    "screenshot, file.read_base64, get_layout, click, swipe, input_text, "
    "input_text_direct, long_press, back, open_schema"
)


def _agent_bin() -> str:
    return shutil.which(config.OPENCLAW_BIN) or config.OPENCLAW_BIN


def _build_prompt(skill_name: str, goal: str, err: CheckpointError,
                  layout_path: Path, shot_path: Path | None) -> str:
    guide = config.SKILLS_GUIDES_DIR / skill_name
    shot_line = f"- Screenshot: {shot_path}\n" if shot_path else ""
    return (
        "You are recovering an automated Instagram scrape running on an Android "
        "ClawPaw node via OpenClaw. A deterministic checkpoint just failed.\n\n"
        f"NODE: {config.NODE_ID}\n"
        f"OVERALL GOAL: {goal}\n"
        f"FAILED CHECKPOINT: {err.name}\n"
        f"DETAIL: {err.detail}\n"
        f"RELEVANT SKILL GUIDE: {guide}\n"
        f"- Saved layout XML: {layout_path}\n"
        f"{shot_line}"
        "\nALLOWED NODE COMMANDS (do not attempt others):\n"
        f"  {_ALLOWED}\n\n"
        "INSTRUCTIONS:\n"
        "1. Read the current screen with get_layout. Recompute every tap target "
        "from live element bounds; never reuse a hard-coded coordinate.\n"
        "2. Drive the UI back to the expected checkpoint state so the script can "
        "continue (e.g. dismiss a dialog, press back out of a wrong screen, "
        "re-open the reels viewer).\n"
        "3. If the skill guide's assumptions are now wrong (renamed resource-id, "
        "shifted element position, new dialog), EDIT the guide markdown file at "
        "the path above to match reality, so future runs don't hit this.\n"
        "4. Do NOT like, follow, comment, or post anything. Read-only recovery.\n"
        "5. Reply with a one-line JSON object: "
        '{"recovered": true|false, "action": "...", "skill_patched": true|false}.'
    )


def escalate(client, skill_name: str, goal: str, err: CheckpointError,
             run_dir: Path) -> dict:
    """Capture artifacts and ask the OpenClaw agent to recover. Returns a status dict."""
    ts = time.strftime("%H%M%S")
    layout_path = run_dir / f"fail_{err.name}_{ts}.xml"
    layout_path.write_text(err.layout, encoding="utf-8")

    shot_path: Path | None = run_dir / f"fail_{err.name}_{ts}.png"
    if not client.screenshot_to(shot_path):
        shot_path = None

    if not config.ESCALATION_ENABLED:
        return {"recovered": False, "action": "capture-only (escalation disabled)",
                "artifacts": [str(layout_path)]}

    prompt = _build_prompt(skill_name, goal, err, layout_path, shot_path)
    args = [
        _agent_bin(), "agent",
        "--session-id", config.AGENT_SESSION_ID,
        "--message", prompt,
        "--thinking", "high",
        "--json",
        "--timeout", str(config.AGENT_TIMEOUT_S),
    ]
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8",
            timeout=config.AGENT_TIMEOUT_S + 30,
        )
    except subprocess.TimeoutExpired:
        return {"recovered": False, "action": "agent timed out"}

    raw = (proc.stdout or "").strip()
    if proc.returncode != 0:
        return {"recovered": False, "action": "agent call failed",
                "rc": proc.returncode, "stderr": (proc.stderr or "")[-300:]}
    status = _extract_status(raw)
    status.setdefault("rc", proc.returncode)
    return status


def _extract_status(raw: str) -> dict:
    """Pull the agent's one-line JSON status out of its (possibly chatty) reply.

    `openclaw agent --json` returns {result: {payloads: [{text: ...}]}}.
    The agent reply may be chatty prose followed by the status object, and the
    object may contain nested braces (e.g. skill_patched sub-objects).
    """
    text = raw
    try:
        outer = json.loads(raw)
        if isinstance(outer, dict):
            payloads = (outer.get("result") or {}).get("payloads") or []
            joined = " ".join(str(p.get("text", "")) for p in payloads if isinstance(p, dict))
            text = joined or str(outer.get("reply") or outer.get("text") or raw)
    except json.JSONDecodeError:
        pass

    # Scan for every '{' and try to parse a valid JSON object from that position
    # forward, allowing nested braces.  Keep the last match that has "recovered".
    best: dict = {}
    for start in (i for i, ch in enumerate(text) if ch == "{"):
        if '"recovered"' not in text[start:]:
            break  # no more status objects possible
        # Walk forward tracking brace depth to find the matching '}'.
        depth = 0
        end = start
        for end, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
        if depth != 0:
            continue
        chunk = text[start: end + 1]
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "recovered" in obj:
            best = obj

    if best:
        return best
    return {"recovered": False, "action": "agent replied without parseable status",
            "reply": text[-300:]}
