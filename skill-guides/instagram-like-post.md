# Instagram skill: like_post

**Goal**: Open a post (or the latest post) on a profile and like it.

**Prerequisite**: You are on the target profile.

## Open the latest post

1. The post grid is usually below the fold. `swipe` up to reveal it, e.g. `{"start_x":540,"start_y":1800,"end_x":540,"end_y":700,"duration":400}`.
2. `get_layout`. Post thumbnails are `resource-id` `image_button` with content-desc like `Photo by <Name> at Row 1, Column 1` or `Reel by <Name> at row 1, column 1`. **Row 1, Column 1 is the latest post.**
3. Click the thumbnail center. The post opens in feed view.

## Like

4. Locate `resource-id` `com.instagram.android:id/row_feed_button_like`.
   - `content-desc="Like"` (no `selected`) → not liked. Click its center to like.
   - `content-desc="Liked"` with `selected="true"` → already liked; stop and report success.
5. Re-read layout. Verify `row_feed_button_like` shows `content-desc="Liked"` and `selected="true"` (the adjacent count text also increases by one).

## Notes

- Tapping a "Liked" button **unlikes** it. Only tap once when liking.
- Like/comment buttons sit in `row_feed_view_group_buttons` near the bottom of the post (example like button bounds `34,2076,102,2205`).
- Coordinates are device-specific; derive from the latest layout.
