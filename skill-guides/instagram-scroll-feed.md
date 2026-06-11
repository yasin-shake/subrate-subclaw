# Instagram skill: scroll_feed

**Goal**: Scroll the Instagram home feed up or down in a controlled way to bring a target post (header, action bar, or caption) into view.

**Prerequisite**: On the home feed (see `instagram-open.md`).

## Mechanics

- Scroll **down** (advance to next posts): `swipe` with `start_y` high and `end_y` low, e.g. `{"start_x":540,"start_y":1700,"end_x":540,"end_y":700,"duration":500}`.
- Scroll **up** (return to previous posts): reverse it, e.g. `{"start_x":540,"start_y":700,"end_x":540,"end_y":1750,"duration":500}`.
- The swipe distance ≈ `start_y - end_y` pixels of feed movement.

## Recommended approach

1. A single feed post (especially video/Reel) is roughly one screen tall (~1800–2000 px), so its **header** (username) and its **action bar + caption** are usually NOT visible at the same time.
2. Scroll in **moderate increments (~600–1000 px)** and re-read layout after each swipe. Large swipes (>1200 px) routinely overshoot a whole post.
3. After each swipe, `get_layout` and locate landmarks:
   - Post header: `resource-id` `row_feed_profile_header` (content-desc like `"<user> posted a photo/video/carousel <date>"`).
   - Action bar: `resource-id` `row_feed_view_group_buttons` (contains the Like/Comment buttons and counts).
   - Caption: the `text=` node immediately following the action bar, beginning with the username.
4. To land precisely on a post's action bar + caption, scroll until `row_feed_view_group_buttons` for that post sits in the middle of the screen.

## Notes

- Overshooting is normal because post heights vary (photo vs video vs 5-image carousel). If you pass a post, scroll back up a smaller amount rather than re-deriving from the top.
- Do NOT scroll to the very top by double-tapping Home — that refreshes/reorders the feed (see `instagram-open.md`). To reach the top without refreshing, swipe down repeatedly until the stories tray (`reels_tray_container`) is visible.
- Coordinates are examples on a 1080x2340 device; always derive from the latest layout.
