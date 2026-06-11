# Instagram — Open a profile and like a post

**Scenario**: Open Instagram, navigate to a specific user's profile by username, open one of their posts, and like it (or verify it is already liked).

**Package name**: `com.instagram.android`

**Connection used**: Gateway (Node) via `openclaw nodes invoke`. The same steps work over HTTP with `clawpaw_controller.py`.

---

## Key principles

- The Instagram layout is deep and changes between versions. Always drive clicks from the **latest** `get_layout`, using `resource-id` to locate elements and computing the **center of `bounds`** for the click coordinate.
- `bounds` are reported as `x1,y1,x2,y2` (four comma-separated integers). Center is `((x1+x2)/2, (y1+y2)/2)`.
- Coordinates below are examples from a 1080x2340 device. **Do not reuse them blindly** — re-read the layout on your own device.
- `open_schema`, `click`, and `back` all return the resulting layout in their payload, so you often do not need a separate `get_layout` call.

---

## Standard steps

**Step 1 — Open Instagram.**

```
open_schema  {"schema":"com.instagram.android"}
```

Dismiss any onboarding/promo dialog. Look for a button with `resource-id` `igds_headline_primary_action_button` (content-desc often "Got it") and click its center.

**Step 2 — Go to Search.** In the bottom tab bar, click the element with `resource-id` `com.instagram.android:id/search_tab` (content-desc "Search and explore").

**Step 3 — Focus the search field.** Click `com.instagram.android:id/action_bar_search_edit_text`. Wait until it reports `focused="true"`.

**Step 4 — Type the username.** Use `input_text_direct` at the search field center with the target username, e.g. `{"x":590,"y":175,"text":"yasinshakey"}`.

**Step 5 — Open the Accounts tab.** The "For you" tab can hang on a spinner; the `Accounts` tab returns account rows directly. Click the tab whose `text="Accounts"`.

**Step 6 — Pick the account.** Each result row has `resource-id` `row_search_user_container` with a child `row_search_user_username` showing the username. Match the exact username and click the row center.

**Step 7 — Confirm the profile.** On the profile, `action_bar_title` shows the username, and `profile_header_post_count_front_familiar` has a content-desc like "1posts". Use this to verify you are on the right profile and how many posts exist.

**Step 8 — Open the post.** Post thumbnails are `image_button` elements with content-desc like "Photo by <user> at Row 1, Column 1". Click the desired thumbnail's center.

**Step 9 — Like the post.** Find `resource-id` `com.instagram.android:id/row_feed_button_like`.

- `content-desc="Like"` and no `selected` attribute → not liked. Click its center to like.
- `content-desc="Liked"` with `selected="true"` → already liked. Do **not** click unless you intend to unlike.

**Step 10 — Verify.** Re-read the layout. A liked post shows `row_feed_button_like` with `selected="true"`, and the adjacent like-count text increases by one.

---

## Key element identification

| Element | resource-id | Notes |
|---------|-------------|-------|
| Onboarding "Got it" | `igds_headline_primary_action_button` | Only present sometimes |
| Search tab | `search_tab` | Bottom nav |
| Search field | `action_bar_search_edit_text` | Tap, then `input_text_direct` |
| Accounts tab | (text) `Accounts` | More reliable than "For you" |
| Result row | `row_search_user_container` | Child `row_search_user_username` holds the username |
| Profile username | `action_bar_title` | Confirms correct profile |
| Post count | `profile_header_post_count_front_familiar` | content-desc e.g. "1posts" |
| Post thumbnail | `image_button` | content-desc "Photo by <user> at Row R, Column C" |
| Like button | `row_feed_button_like` | `selected="true"` + content-desc "Liked" means already liked |

---

## Notes / cautions

- Only tap the like button once to like. Tapping a "Liked" button **unlikes** it.
- Search results take a moment to load; re-read the layout if you still see `search_loading_spinner` or shimmer placeholders (`row_shimmer_container`).
- Do not perform follows, comments, DMs, or settings changes unless explicitly asked.
