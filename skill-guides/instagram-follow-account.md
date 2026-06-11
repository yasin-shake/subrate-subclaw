# Instagram skill: follow_account

**Goal**: Follow a profile you are currently viewing.

**Prerequisite**: You are on the target profile (see `instagram-search-account.md`).

## Steps

1. `get_layout` and locate the follow button: `resource-id` `com.instagram.android:id/profile_header_follow_button`.
   - `content-desc="Follow <Name>"` → not following yet.
   - `content-desc="Following <Name>"` → already following; stop and report success.
2. Click the center of the follow button bounds (example: bounds `33,1071,325,1161` → center `179,1116`).
3. Re-read layout. Verify the button content-desc is now `Following <Name>`.

## Notes

- The parent container may carry `selected="true"` regardless of state; rely on the **content-desc** (`Follow` vs `Following`), not on `selected`.
- If a "Edit profile" button is shown instead of a follow button, you are viewing your own logged-in account — do not attempt to follow.
- Do not tap a "Following" button unless you intend to unfollow.
