"""Verify-after-act checkpoints.

The cheap deterministic loop calls these after every meaningful action. A failed
checkpoint is the signal to escalate to the LLM agent (see escalation.py).
"""

from __future__ import annotations

import time
from collections.abc import Callable

from openclaw_client import OpenClawClient, UINode, find


class CheckpointError(AssertionError):
    """An expected UI state was not reached. Carries context for escalation."""

    def __init__(self, name: str, detail: str, layout: str):
        super().__init__(f"checkpoint '{name}' failed: {detail}")
        self.name = name
        self.detail = detail
        self.layout = layout


def assert_present(layout: str, name: str, *, resource_id: str | None = None,
                   content_desc_re: str | None = None) -> UINode:
    node = find(layout, resource_id=resource_id, content_desc_re=content_desc_re)
    if node is None:
        want = resource_id or content_desc_re
        raise CheckpointError(name, f"expected element ({want}) not found", layout)
    return node


def wait_for(client: OpenClawClient, name: str, *, resource_id: str | None = None,
             content_desc_re: str | None = None, attempts: int = 5,
             delay: float = 1.5) -> tuple[str, UINode]:
    """Poll get_layout until the element appears. Returns (layout, node)."""
    layout = ""
    for _ in range(attempts):
        layout = client.get_layout()
        node = find(layout, resource_id=resource_id, content_desc_re=content_desc_re)
        if node is not None:
            return layout, node
        time.sleep(delay)
    want = resource_id or content_desc_re
    raise CheckpointError(name, f"element ({want}) never appeared after {attempts} polls", layout)


def retry(fn: Callable[[], bool], attempts: int, *, delay: float = 1.0) -> bool:
    """Run fn() until it returns True or attempts run out. fn does its own action."""
    for _ in range(attempts):
        if fn():
            return True
        time.sleep(delay)
    return False
