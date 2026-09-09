---
name: feedback-verify-security-exemption-premises-live
description: "A security check's skip condition needs its own live measurement, not just the code's inputs — an unverified \"mechanism X is unreliable\" claim can be flatly wrong"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1fdebb29-23af-4c69-80a0-fcb348964f4f
  modified: 2026-09-04T07:35:04.994Z
---

When a security check carries an exemption ("skip this validation under
condition X because X makes the signal unreliable"), the exemption's
premise is itself a claim that needs verification — the same "verify,
don't trust" discipline the check exists to enforce applies recursively to
why the check is skipped, not only to what it validates.

**Why:** ticket 0638 (search-works-for-zotero) added a `USER`-environment
check to catch a forged `--spawned-under` claim, then exempted it under
`podman-unshare` on the assumption that the mechanism's uid-remapping also
made environment variables ("identity-bound names") untrustworthy there.
That assumption was inherited from the ticket's own prose, never measured,
and was wrong: `podman unshare unshare -n -- env` still reports the real
`USER` even though `id` in the same namespace reports `uid=0` —
`unshare`/`podman unshare` remap uid/mount/net namespaces but never touch
`envp`. The exemption it justified was a confirmed, unauthenticated,
hand-typeable bypass with no legitimate caller once the premise fell. Two
review rounds *hardened* the exemption (better failure mode, better docs)
before a red-team pass ran the one discriminating command and falsified it
outright. The fix was to delete the exemption, not patch it further.

**How to apply:** before shipping (or approving) a mechanism-conditional
skip in a security-relevant check, ask what live command would prove or
disprove the skip's stated reason, and run it — don't accept the reason
because it sounds analogous to a *different*, already-verified fact (here:
`getuid()` really is unreliable inside the namespace; that did not mean
`USER` also was). A skip whose premise cannot be cheaply measured is a
signal to escalate to the author rather than ship, not a reason to skip
the measurement.
