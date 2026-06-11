"""Thin Python wrapper around `openclaw nodes invoke`, plus layout parsing.

Why a Python wrapper instead of PowerShell:
  * Args are passed as a list with shell=False, so JSON params reach the CLI
    verbatim. This sidesteps the PowerShell argument-mangling that broke
    `input_text_direct` for any text containing spaces (no `cmd /c` hack needed).
  * Layout is parsed once into a flat list of UI nodes that callers can query by
    resource-id / content-desc, and ALWAYS recompute tap centers from live
    bounds (the single most important habit for skills that don't drift).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass

import config


class OpenClawError(RuntimeError):
    """Raised when a node command fails to execute (transport / CLI error)."""


@dataclass
class UINode:
    resource_id: str | None
    content_desc: str | None
    text: str | None
    bounds: tuple[int, int, int, int] | None
    raw: str

    @property
    def center(self) -> tuple[int, int] | None:
        if not self.bounds:
            return None
        x1, y1, x2, y2 = self.bounds
        return (x1 + x2) // 2, (y1 + y2) // 2


_BOUNDS_RE = re.compile(r'bounds="(-?\d+),(-?\d+),(-?\d+),(-?\d+)"')
_RID_RE = re.compile(r'resource-id="([^"]*)"')
_CD_RE = re.compile(r'content-desc="([^"]*)"')
_TEXT_RE = re.compile(r'text="([^"]*)"')
# Each UI element is a token that starts with `<` and ends before the next `<` or `>`.
_TOKEN_RE = re.compile(r"<[^<>]*>")


def _attr(token: str, pattern: re.Pattern[str]) -> str | None:
    m = pattern.search(token)
    return m.group(1) if m else None


def _bounds(token: str) -> tuple[int, int, int, int] | None:
    m = _BOUNDS_RE.search(token)
    if not m:
        return None
    return tuple(int(v) for v in m.groups())  # type: ignore[return-value]


class OpenClawClient:
    def __init__(self, node_id: str = config.NODE_ID):
        self.node_id = node_id
        self.bin = shutil.which(config.OPENCLAW_BIN) or config.OPENCLAW_BIN

    # -- low level -----------------------------------------------------------
    def invoke(self, command: str, params: dict | None = None,
               timeout_s: int = config.INVOKE_TIMEOUT_S) -> dict:
        params = params or {}
        args = [
            self.bin, "nodes", "invoke",
            "--node", self.node_id,
            "--command", command,
            "--params", json.dumps(params, ensure_ascii=False),
        ]
        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8",
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            raise OpenClawError(f"{command} timed out after {timeout_s}s") from e
        if proc.returncode != 0:
            raise OpenClawError(
                f"{command} failed (rc={proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
            )
        return self._parse_json(proc.stdout)

    @staticmethod
    def _parse_json(stdout: str) -> dict:
        stdout = stdout.strip()
        if not stdout:
            return {}
        # Tolerate any leading log noise before the JSON object.
        start = stdout.find("{")
        if start == -1:
            return {"payload": stdout}
        try:
            return json.loads(stdout[start:])
        except json.JSONDecodeError:
            return {"payload": stdout}

    # -- actions -------------------------------------------------------------
    def get_layout(self) -> str:
        return str(self.invoke("get_layout", {}).get("payload", ""))

    def click(self, x: int, y: int) -> None:
        self.invoke("click", {"x": int(x), "y": int(y)})

    def click_center(self, node: UINode) -> None:
        c = node.center
        if not c:
            raise OpenClawError("node has no bounds to click")
        self.click(*c)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> None:
        self.invoke("swipe", {"start_x": x1, "start_y": y1,
                              "end_x": x2, "end_y": y2, "duration": duration})

    def back(self) -> None:
        self.invoke("back", {})

    def open_schema(self, schema: str) -> None:
        self.invoke("open_schema", {"schema": schema}, timeout_s=max(config.INVOKE_TIMEOUT_S, 20))

    def input_text_direct(self, x: int, y: int, text: str) -> None:
        # Works with spaces because Python passes argv literally (shell=False).
        self.invoke("input_text_direct", {"x": int(x), "y": int(y), "text": text})

    def screenshot_to(self, local_path) -> bool:
        """Best-effort: capture a device screenshot and save it locally as PNG."""
        try:
            res = self.invoke("screenshot", {})
            payload = res.get("payload", res)
            device_path = None
            if isinstance(payload, str):
                device_path = payload
            elif isinstance(payload, dict):
                device_path = payload.get("path") or payload.get("file") or payload.get("uri")
            if not device_path:
                return False
            b64 = self.invoke("file.read_base64", {"path": device_path}).get("payload", "")
            if isinstance(b64, dict):
                b64 = b64.get("base64") or b64.get("data") or ""
            import base64
            data = base64.b64decode(b64)
            with open(local_path, "wb") as fh:
                fh.write(data)
            return True
        except Exception:
            return False

    # -- gestures ------------------------------------------------------------
    def scroll_down(self, frac: float = 0.55) -> None:
        cx = config.DEVICE_W // 2
        self.swipe(cx, int(config.DEVICE_H * 0.72), cx, int(config.DEVICE_H * (0.72 - frac)))

    def scroll_up(self, frac: float = 0.55) -> None:
        cx = config.DEVICE_W // 2
        self.swipe(cx, int(config.DEVICE_H * (0.72 - frac)), cx, int(config.DEVICE_H * 0.72))


# --- layout query helpers ----------------------------------------------------

def parse_nodes(layout: str) -> list[UINode]:
    nodes: list[UINode] = []
    for tok in _TOKEN_RE.findall(layout):
        nodes.append(UINode(
            resource_id=_attr(tok, _RID_RE),
            content_desc=_attr(tok, _CD_RE),
            text=_attr(tok, _TEXT_RE),
            bounds=_bounds(tok),
            raw=tok,
        ))
    return nodes


def _is_on_screen(n: UINode) -> bool:
    """Reject the off-screen ViewPager panels (negative-x or negative-width bounds)."""
    if not n.bounds:
        return True  # no bounds (e.g. a text container) -> don't exclude on geometry
    x1, y1, x2, y2 = n.bounds
    return x1 >= 0 and x2 > x1


def find(layout: str, *, resource_id: str | None = None,
         content_desc_re: str | None = None, on_screen: bool = True) -> UINode | None:
    """First node matching the given resource-id and/or content-desc regex.

    on_screen filters out the off-screen ViewPager panels (negative-x bounds).
    """
    cd = re.compile(content_desc_re) if content_desc_re else None
    for n in parse_nodes(layout):
        if resource_id and n.resource_id != resource_id:
            continue
        if cd and not (n.content_desc and cd.search(n.content_desc)):
            continue
        if on_screen and not _is_on_screen(n):
            continue
        return n
    return None


def find_all(layout: str, *, resource_id: str | None = None,
             content_desc_re: str | None = None, on_screen: bool = True) -> list[UINode]:
    cd = re.compile(content_desc_re) if content_desc_re else None
    out: list[UINode] = []
    for n in parse_nodes(layout):
        if resource_id and n.resource_id != resource_id:
            continue
        if cd and not (n.content_desc and cd.search(n.content_desc)):
            continue
        if on_screen and not _is_on_screen(n):
            continue
        out.append(n)
    return out


def first_number(text: str | None) -> str:
    """Extract a count like '1,234' from a content-desc such as 'Like number is1,234. ...'."""
    if not text:
        return ""
    m = re.search(r"(\d[\d,]*)", text)
    return m.group(1) if m else ""
