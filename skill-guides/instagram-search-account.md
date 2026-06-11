# Instagram skill: search_account

**Goal**: Find and open a specific Instagram profile by username.

**Package**: `com.instagram.android`

## Steps

1. `open_schema {"schema":"com.instagram.android"}`. If a promo dialog appears (`resource-id` `igds_headline_primary_action_button`), click its center to dismiss.
2. Tap the Search tab: `resource-id` `com.instagram.android:id/search_tab` (content-desc "Search and explore"), in the bottom tab bar.
3. Tap the search field `com.instagram.android:id/action_bar_search_edit_text`. Re-read layout; wait for `focused="true"`.
4. Type the username with `input_text_direct` at the field center, e.g. `{"x":590,"y":175,"text":"<username>"}`.
5. Tap the `Accounts` tab (`text="Accounts"`). It is more reliable than "For you", which can hang on a spinner (`search_loading_spinner` / `row_shimmer_container`).
6. Find the result row `resource-id` `row_search_user_container` whose child `row_search_user_username` text exactly equals the target username. Click the row center.
7. Confirm arrival: the profile `action_bar_title` text equals the username.

## Notes

- Bounds format is `x1,y1,x2,y2`; click the center.
- If the username is already open (e.g. from a prior navigation), `open_schema` may resume on that profile — verify `action_bar_title` before searching again.
- Coordinates above are examples on a 1080x2340 device; always derive from the latest layout.
