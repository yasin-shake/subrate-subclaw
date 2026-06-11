# Instagram skill: comment_post

**Goal**: Post a text comment on an open post.

**Prerequisite**: A post is open in feed view.

## Steps

1. `get_layout` and tap the comment button `resource-id` `com.instagram.android:id/row_feed_button_comment` (example bounds `186,2076,254,2205` → center `222,2140`). The comment composer opens.
2. Locate the input field `resource-id` `com.instagram.android:id/layout_comment_thread_edittext_multiline`.
3. **Focus the field first**: click its center, then re-read layout and confirm `editable="true" focused="true"`. `input_text_direct` only writes to a focused field — typing before focus silently does nothing.
4. Enter the text with `input_text_direct` at the field center, e.g. `{"x":486,"y":1270,"text":"test successful!"}`.
5. Re-read layout. The field should now show `text="<your text>"`, and a Post control appears: `resource-id` `com.instagram.android:id/layout_comment_thread_post_button_icon` (content-desc "Post", example bounds `901,1231,1030,1310` → center `965,1270`).
6. Click the Post button center.
7. Verify: re-read layout. The comment thread shows `<your_account> said <your text>`, and the composer field resets to its placeholder ("What do you think of this?").

## Critical: passing text with spaces from PowerShell (Windows)

On Windows PowerShell 5.1, the usual escaped `--params '{\"...\":\"...\"}'` form **fails when the JSON value contains a space** — PowerShell mis-quotes the argument and `openclaw` reports `error: too many arguments for 'invoke'`. This silently breaks `input_text_direct` / `input_text` for any multi-word text.

Workaround — route through `cmd /c` with a single-quoted PowerShell string so the JSON reaches `node.exe` intact:

```powershell
cmd /c 'openclaw nodes invoke --node <NODE_ID> --command input_text_direct --params "{\"x\":486,\"y\":1270,\"text\":\"test successful!\"}"'
```

Single-word text (no spaces) works fine with the normal escaped form. On macOS/Linux shells this gotcha does not apply.

## Notes

- The placeholder text "What do you think of this?" is not your input; if you still see it after typing, the field was not focused — repeat step 3.
- Do not post comments unless explicitly requested.
