# Instagram skill: extract_reel_stats (Reels viewer)

**Goal**: Scrape poster username, like count, comment count, and full caption for a sequence of reels in the full-screen Reels/clips viewer (e.g. opened from a topic search or the Reels tab). The layout differs completely from feed posts (`extract_post_stats.md`).

**Prerequisite**: A reel is open in the clips viewer (`resource-id` `com.instagram.android:id/clips_viewer_view_pager`).

## Where each field lives

- **Username**: `text=` of `resource-id` `com.instagram.android:id/clips_author_username`.
- **Like count**: `resource-id` `com.instagram.android:id/like_count`, content-desc `"Like number is<N>. View likes"` (N may contain commas, e.g. `26,447`). If hidden it reads `"View likes"` with no number.
- **Comment count**: `resource-id` `com.instagram.android:id/comment_count`, content-desc `"Comment number is<N>. View comments"`. **If there are 0 comments this element is absent** — record 0 / not shown.
- **Reshare**: `resource-id` `ufi_text_component`, `"Reshare number is<N>"` (optional).
- **Caption (truncated)**: `resource-id` `com.instagram.android:id/clips_caption_component` → child content-desc; ends with `…` when truncated.
- **Search scope**: `clips_viewer_action_bar_title` shows the originating query.

## Getting the COMPLETE caption

1. Tap the **center of the `clips_caption_component` bounds** to expand it inline. Derive the center from the latest layout each time — its y-position shifts per reel:
   - reel WITH a music/audio line: caption ≈ `y 1900–1970` (center ~`489,1930`).
   - reel WITHOUT a music line: caption sits lower ≈ `y 1930–1997` (center ~`489,1964`).
   A fixed y can miss; always recompute from `clips_caption_component` bounds.
2. Re-read; the expanded `clips_caption_component` content-desc holds the full multi-line caption (newlines preserved).
3. **Do NOT tap below/around the caption after expansion** — an expanded reel renders a location row (e.g. "Dubai, United Arab Emirates") and an audio link right under the caption. A stray tap there navigates to the Map / audio page and derails the scrape.

## Advancing through reels (robust loop)

The reels viewer is a vertical pager. To move to the next result, **swipe up** `{"start_x":540,"start_y":1500,"end_x":540,"end_y":500,"duration":300}`.

Critical reliability rules learned the hard way:

- **Swiping while the caption is expanded often just collapses it instead of advancing.** So after expanding+reading a caption, the next swipe may not change reels.
- Therefore **verify advancement**: after each swipe, read `clips_author_username` and compare to the previous reel's username. If unchanged (or empty), swipe again (retry up to ~4 times). This naturally handles the "collapse first, then advance" case.
- Per-reel order: (a) read stats from the collapsed view, (b) tap to expand and read the full caption, (c) swipe-with-verification to the next reel.
- Swipe **down** with the same verification to go back to a previous reel if you need to re-capture one.

## Notes

- Scraping does not require liking; avoid double-tapping the video (that likes the reel).
- Some reels have no caption — the expand tap is then harmless (it may pause the video).
- Coordinates are examples on a 1080x2340 device; always derive from the latest layout.
