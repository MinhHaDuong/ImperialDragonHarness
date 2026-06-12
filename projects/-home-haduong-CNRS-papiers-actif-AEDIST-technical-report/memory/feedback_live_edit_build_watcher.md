---
name: feedback-live-edit-build-watcher
description: "To support a user doing a rapid live-editing pass on a build artifact (LaTeX/Quarto), run a background watcher that rebuilds on save and exits-on-failure so the harness re-invokes you to fix the break"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d93d059e-0241-40fb-b77c-497429967a47
---

When the user is rapid-firing edits on a buildable artifact (e.g. `slides-en.tex`)
and repeatedly asking "make X" after each save, offer a watcher instead of
rebuilding on request. Pattern that worked well (one Econom'IA session caught
6 LaTeX breaks this way):

```bash
# run_in_background: true
last=$(stat -c %Y "$TEX")
while true; do
  sleep 2
  cur=$(stat -c %Y "$TEX" 2>/dev/null) || continue
  [ "$cur" = "$last" ] && continue
  last=$cur
  if make -C "$DIR" target.pdf >"$LOG" 2>&1; then
    echo "$(date +%H:%M:%S) OK" >> status.log      # silent success: keep looping
  else
    echo "BUILD FAILED:"; grep -iE "error:|^! |Missing|keyval|Paragraph ended|alignment tab|extra \}" "$LOG" | head
    exit 1                                          # exit -> harness re-invokes you
  fi
done
```

**Why it fits the harness:** a background command re-invokes you *on exit*, not
per-iteration. Exiting only on build failure means clean builds stay silent
(the user's viewer just refreshes) while breaks ping you with the error to fix
and restart. Stop it with `TaskStop <id>` when the user says "stop watcher".

**How to apply:**
- Build from the user's working-tree source ([[feedback_build_from_user_worktree]]), not a worktree copy.
- On a break: read the task `.output`, fix the typo (re-read first — the user
  is still editing and the file moves under you), rebuild, restart the watcher.
- Recurring user LaTeX slips to expect: `\item[` in itemize (needs plain
  `\item`; brackets are description-only), unescaped `_` `&` `#` in text,
  `[title]` vs `{title}` on `\begin{frame}`, bare `\vskip` (needs a length).
