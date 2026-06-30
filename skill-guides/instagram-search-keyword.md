# Instagram skill: search_keyword (topic / explore search)

**Goal**: Search a free-text topic (e.g. "real estate uae") and open the results so they can be scraped. Differs from `search_account`, which targets a single username.

**Package**: `com.instagram.android`

## Steps

1. Open Instagram (see `instagram-open.md`) and tap the Search tab `resource-id` `com.instagram.android:id/search_tab` (content-desc "Search and explore"); example center `756,2137`.
2. Tap the search field `resource-id` `com.instagram.android:id/action_bar_search_edit_text`. Re-read; wait for `focused="true"`.
3. Enter the query via `input_text_direct`. Spaces are fine when invoked from Python with `shell=False` — no workaround needed.
4. After typing, **two behaviors are observed depending on build**:
   - **Suggestion row present**: a `resource-id` `com.instagram.android:id/row_search_keyword_title` row appears with the query text. Tap its center to commit the search.
   - **Auto-commit (newer builds)**: results load immediately with no suggestion row. Do not wait for one; proceed directly to verifying the grid.
5. After the query is committed, results render in tabs. **Current observed tabs**: `For you`, `Accounts`, `Audio`, `Tags`. (A dedicated `Reels` tab is not always present.) `For you` is selected by default and shows a mixed thumbnail grid.
6. Grid items are `resource-id` `grid_card_layout_container` (two per row) with content-desc like `"Reel by <Name> at row R, column C"` or `"Photo by <Name> …"`. Tap a **Reel** card center to open the full-screen viewer.
7. Tapping a **Reel** card opens the full-screen Reels viewer (`clips_viewer_view_pager`) scoped to this search — its action bar title equals the query or a related hashtag (e.g. `clips_viewer_action_bar_title` = "#realestateuae"). From there you can page through results by swiping up. See `instagram-extract-reel-stats.md`.

## Notes

- **Do not require a keyword suggestion row.** If `row_search_keyword_title` is absent, check whether `grid_card_layout_container` or `row_search_user_container` elements are already visible with positive x bounds — if so, the search committed automatically.
- The captured layout also contains the off-screen home-feed panel from the ViewPager (negative-x bounds). Ignore any node whose bounds have a negative x1. The active results panel has normal `0..1080` x bounds.
- Coordinates are examples on a 1080×2340 device; always derive from the latest layout.
