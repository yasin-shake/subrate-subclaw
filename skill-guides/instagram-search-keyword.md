# Instagram skill: search_keyword (topic / explore search)

**Goal**: Search a free-text topic (e.g. "real estate uae") and open the results so they can be scraped. Differs from `search_account`, which targets a single username.

**Package**: `com.instagram.android`

## Steps

1. Open Instagram (see `instagram-open.md`) and tap the Search tab `resource-id` `com.instagram.android:id/search_tab` (content-desc "Search and explore"); example center `756,2137`.
2. Tap the search field `resource-id` `com.instagram.android:id/action_bar_search_edit_text`. Re-read; wait for `focused="true"`.
3. Enter the query. **If the query has spaces** (most topics do), `input_text_direct` fails under Windows PowerShell (see `instagram-comment-post.md` for the `cmd /c` workaround). Two reliable options:
   - Use the `cmd /c 'openclaw … --params "{\\\"x\\\":540,\\\"y\\\":146,\\\"text\\\":\\\"real estate uae\\\"}"'` form, OR
   - If the term is in **Recent** searches, just tap that row: `resource-id` `row_search_keyword_title` whose `text` matches; example center of the row image/title.
4. After the query is set, results render in tabs: `For you`, `Accounts`, `Audio`, `Tags`, `Places`, `Reels`. `For you` is selected by default and shows a thumbnail grid.
5. Grid items are `resource-id` `grid_card_layout_container` (two per row) with content-desc like `"Reel by <Name> at row R, column C"` or `"Photo by <Name> …"`. Tap a card center to open it.
6. Tapping a **Reel** card opens the full-screen Reels viewer (`clips_viewer_view_pager`) scoped to this search — its action bar title equals the query (e.g. `clips_viewer_action_bar_title` = "real estate uae"). From there you can page through results by swiping up. See `instagram-extract-reel-stats.md`.

## Notes

- The captured layout may also contain the (off-screen, negative-x bounds) home-feed panel from the ViewPager; ignore nodes whose bounds have negative x. The active results panel has normal `0..1080` x bounds.
- Coordinates are examples on a 1080x2340 device; always derive from the latest layout.
