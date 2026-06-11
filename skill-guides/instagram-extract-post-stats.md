# Instagram skill: extract_post_stats

**Goal**: Read a feed post's poster username, like count, comment count, and full caption from the layout XML.

**Prerequisite**: The target post's action bar + caption are in view (see `instagram-scroll-feed.md`).

## Where each field lives

- **Username (poster)**: from the post header `resource-id` `row_feed_profile_header`, content-desc `"<user> posted a <type> <date>"`, or `resource-id` `row_feed_photo_profile_name`. The caption also starts with the username.
- **Post type**: the header content-desc says `photo`, `video`, `carousel`, or `reel`.
- **Like count**: `resource-id` `com.instagram.android:id/row_feed_like_count` (the `text=` value), located right after the Like button in `row_feed_view_group_buttons`.
- **Comment count**: `resource-id` `com.instagram.android:id/row_feed_comment_count`, right after the Comment button.
- **Caption / description**: the `text=` node immediately after the action bar, starting with the username. Truncated captions end with a `more` link (content-desc "more").

## Robust fallback: the media content-desc

Photo/carousel media exposes a single content-desc that bundles the stats, e.g.:

- `"Photo by <Name>, N likes"`
- `"Photo 1 of 5 by <Name>, 5,793 likes, 46 comments"` (carousel)
- `"Sponsored Photo by <Name>, N likes, M comments"` (ad — usually skip)

Use this (`row_feed_photo_imageview` / `carousel_video_media_group`) when the numeric count elements are not rendered.

## Getting the COMPLETE caption

1. If the caption ends with a `more` link, click the `more` content-desc center to expand inline.
2. Re-read layout; the caption `text=` now holds the full multi-line description and ends with a `less` link. Strip the trailing `less`.
3. The XML preserves newlines inside the `text=` value; flatten them to spaces (or `\n`) as needed for storage.

## Counts: shown vs hidden

- If `row_feed_like_count` / `row_feed_comment_count` is absent AND the media content-desc has no number, the count is **not shown** — record it as "not shown" rather than 0.
- Some posts show likes but hide the comment count.

## Notes

- Like count reflects the live value; if you Like the post yourself the displayed count increments by 1 — record the pre-like count if you want the original public number.
- To distinguish a Like-button state: `content-desc="Like"` = not liked, `content-desc="Liked"` with `selected="true"` = already liked.
- Coordinates are examples on a 1080x2340 device; always derive from the latest layout.
