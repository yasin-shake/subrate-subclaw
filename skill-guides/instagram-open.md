# Instagram skill: open_instagram

**Goal**: Launch Instagram and land on the home feed.

**Package**: `com.instagram.android`

## Steps

1. `open_schema {"schema":"com.instagram.android"}`. Wait ~3s for the app to load.
2. If a promo / "what's new" dialog appears (`resource-id` `igds_headline_primary_action_button` or any `..._dismiss_button`), click its center to dismiss.
3. Confirm you are on the home feed: the bottom tab bar shows `resource-id` `com.instagram.android:id/feed_tab` (content-desc "Home") and the action bar shows `content-desc="Instagram Home Feed"` (`resource-id` `title_logo`).
4. If Instagram resumed on another screen (a profile, Reels, DMs, etc.), tap the Home tab `feed_tab` (example bounds `0,2070,216,2205` → center `108,2137`) to return to the feed.

## Notes

- Tapping `feed_tab` **once** while already on the feed scrolls to the top. Tapping it **twice** (or tapping when already at the top) triggers a pull-to-refresh, which **reloads and reorders the feed** — avoid the double tap unless you intentionally want fresh content.
- The feed is dynamic: organic posts, "Suggested for you" posts, and "Sponsored"/"Ad" posts are interleaved and the order can change on refresh.
- Coordinates above are examples on a 1080x2340 device; always derive from the latest layout.
