"""Hybrid Instagram reels scraper.

Deterministic happy-path with verify-after-act checkpoints; on any checkpoint
failure it escalates to the OpenClaw agent to recover (and self-patch skills),
then retries the step once.

Usage:
    python scrape_reels.py --query "real estate uae" --count 10 --out out.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import config
from openclaw_client import OpenClawClient, find, find_all, first_number
from checkpoints import CheckpointError, assert_present, wait_for
from escalation import escalate


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


class Scraper:
    def __init__(self, query: str, count: int, run_dir: Path):
        self.client = OpenClawClient()
        self.query = query
        self.count = count
        self.run_dir = run_dir
        self.goal = f"Search Instagram for '{query}' and scrape {count} reels to CSV."

    # -- recovery wrapper ----------------------------------------------------
    def guarded(self, step_name: str, skill: str, fn):
        try:
            return fn()
        except CheckpointError as e:
            log(f"CHECKPOINT FAILED: {e}. Escalating to OpenClaw agent...")
            status = escalate(self.client, skill, self.goal, e, self.run_dir)
            log(f"Escalation result: {status}")
            # Recovery happened on the live device; retry the step once.
            return fn()

    # -- phases --------------------------------------------------------------
    def open_instagram(self):
        self.client.open_schema(config.IG_PACKAGE)
        time.sleep(3)
        # IG may resume on an inner screen (reels viewer, a profile, the map).
        # Press Back / dismiss promos until the bottom nav (search_tab) is present.
        layout = ""
        for _ in range(5):
            layout = self.client.get_layout()
            promo = find(layout, resource_id="com.instagram.android:id/igds_headline_primary_action_button")
            if promo and promo.center:
                self.client.click(*promo.center)
                time.sleep(1)
                continue
            if find(layout, resource_id="com.instagram.android:id/search_tab"):
                log("Instagram open (bottom nav present).")
                return
            self.client.back()
            time.sleep(1.5)
        raise CheckpointError("instagram_home",
                              "bottom nav (search_tab) not reachable after opening", layout)

    def run_search(self):
        layout = self.client.get_layout()

        # Idempotent: if recovery already put us in the reel viewer, we're done.
        if find(layout, resource_id="com.instagram.android:id/clips_author_username"):
            log("Already in reels viewer; skipping search.")
            return

        # Idempotent: results grid already on screen (query committed automatically).
        if self._on_results_page(layout):
            log("Search results already loaded.")
            return

        # Make sure the search screen is up.
        tab = find(layout, content_desc_re=r"Search and explore")
        if tab and tab.center:
            self.client.click(*tab.center)
            time.sleep(2)
        layout, field = wait_for(self.client, "search_field",
                                 resource_id="com.instagram.android:id/action_bar_search_edit_text")
        self.client.click(*field.center)
        time.sleep(1.5)
        self.client.input_text_direct(*field.center, self.query)  # spaces ok via Python
        time.sleep(2.5)

        # Some IG builds show a keyword-suggestion row that must be tapped to commit
        # the search; newer builds auto-load results without it.  Tap only if present.
        layout = self.client.get_layout()
        kw = self._find_keyword_row(layout)
        if kw:
            self.client.click(*kw.center)
            time.sleep(1.5)

        layout, _ = wait_for(self.client, "results_grid",
                             resource_id="com.instagram.android:id/grid_card_layout_container",
                             attempts=6)
        log("Search results grid loaded.")

    def _on_results_page(self, layout: str) -> bool:
        """True when the live keyword-search results page is already rendered."""
        return (
            find(layout, resource_id="com.instagram.android:id/grid_card_layout_container") is not None
            or find(layout, resource_id="com.instagram.android:id/row_search_user_container") is not None
        )

    def _find_keyword_row(self, layout: str):
        q = self.query.lower()
        for n in find_all(layout, resource_id="com.instagram.android:id/row_search_keyword_title"):
            if n.text and q in n.text.lower() and n.center:
                return n
        # Fallback: any keyword title row.
        rows = find_all(layout, resource_id="com.instagram.android:id/row_search_keyword_title")
        return rows[0] if rows and rows[0].center else None

    def open_first_reel(self):
        layout = self.client.get_layout()

        # Idempotent: already in the reel viewer (e.g. recovery navigated here).
        if find(layout, resource_id="com.instagram.android:id/clips_author_username"):
            log("Reels viewer already open.")
            return

        cards = find_all(layout, resource_id="com.instagram.android:id/grid_card_layout_container")
        target = next((c for c in cards if c.content_desc and c.content_desc.startswith("Reel")), None)
        target = target or (cards[0] if cards else None)
        if not target or not target.center:
            raise CheckpointError("grid_card", "no tappable grid card found", layout)
        self.client.click(*target.center)
        wait_for(self.client, "reels_viewer",
                 resource_id="com.instagram.android:id/clips_author_username", attempts=6)
        log("Reels viewer open.")

    # -- per-reel extraction -------------------------------------------------
    def _read_reel(self, layout: str) -> dict:
        user = find(layout, resource_id="com.instagram.android:id/clips_author_username")
        like = find(layout, resource_id="com.instagram.android:id/like_count")
        comment = find(layout, resource_id="com.instagram.android:id/comment_count")
        return {
            "username": (user.text or user.content_desc or "").strip() if user else "",
            "likes": first_number(like.content_desc) if like else "",
            "comments": first_number(comment.content_desc) if comment else "0",
        }

    def _full_caption(self, prev_caption: str = "") -> str:
        layout = self.client.get_layout()
        cap = find(layout, resource_id="com.instagram.android:id/clips_caption_component")
        if not cap or not cap.center:
            return prev_caption
        # Expand by tapping the caption's live center (varies per reel -> recompute).
        self.client.click(*cap.center)
        time.sleep(1.5)
        layout = self.client.get_layout()
        m = re.search(
            r'resource-id="com\.instagram\.android:id/clips_caption_component"[\s\S]{0,4000}?content-desc="([^"]*)"',
            layout,
        )
        text = m.group(1) if m else prev_caption
        return text.replace("\n", " ").strip()

    def _advance(self) -> str:
        """Swipe to the next reel; verify the username changed. Returns new username."""
        prev = self._last_user
        for _ in range(config.MAX_ADVANCE_TRIES):
            self.client.swipe(540, 1500, 540, 500, duration=300)
            time.sleep(2.5)
            layout = self.client.get_layout()
            node = find(layout, resource_id="com.instagram.android:id/clips_author_username")
            user = (node.text or node.content_desc or "").strip() if node else ""
            if user and user != prev:
                return user
        return prev  # could not advance; caller will escalate

    def scrape(self) -> list[dict]:
        rows: list[dict] = []
        self._last_user = ""
        for i in range(1, self.count + 1):
            layout = self.client.get_layout()
            if not find(layout, resource_id="com.instagram.android:id/clips_author_username"):
                raise CheckpointError("reel_view", f"not on a reel at index {i}", layout)
            stats = self._read_reel(layout)
            stats["caption"] = self._full_caption(prev_caption="")
            stats["post"] = i
            rows.append(stats)
            log(f"Reel {i}: @{stats['username']} likes={stats['likes']} "
                f"comments={stats['comments']}")
            self._last_user = stats["username"]
            if i < self.count:
                new_user = self._advance()
                if new_user == self._last_user:
                    # Verified-advance failed -> escalate, then try once more.
                    err = CheckpointError("advance_reel",
                                          "swipe did not move to a new reel",
                                          self.client.get_layout())
                    log(f"CHECKPOINT FAILED: {err}. Escalating...")
                    log(f"Escalation result: {escalate(self.client, 'instagram-extract-reel-stats.md', self.goal, err, self.run_dir)}")
                    self._advance()
        return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    cols = ["post", "username", "likes", "comments", "caption"]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Hybrid Instagram reels scraper")
    ap.add_argument("--query", required=True, help="search topic, e.g. 'real estate uae'")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--out", default=None, help="CSV output path")
    args = ap.parse_args(argv)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = config.RUNS_DIR / f"{re.sub(r'[^a-z0-9]+', '_', args.query.lower())}_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else run_dir / "summary.csv"

    s = Scraper(args.query, args.count, run_dir)
    log(f"Run dir: {run_dir}")
    try:
        s.guarded("open_instagram", "instagram-open.md", s.open_instagram)
        s.guarded("run_search", "instagram-search-keyword.md", s.run_search)
        s.guarded("open_first_reel", "instagram-search-keyword.md", s.open_first_reel)
        rows = s.scrape()
    except CheckpointError as e:
        log(f"FATAL: unrecovered checkpoint '{e.name}': {e.detail}")
        (run_dir / "fatal.xml").write_text(e.layout, encoding="utf-8")
        return 2

    write_csv(rows, out_path)
    log(f"Done. {len(rows)} reels -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
