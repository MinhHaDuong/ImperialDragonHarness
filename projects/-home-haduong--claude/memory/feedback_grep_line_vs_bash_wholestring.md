# grep -E is line-oriented; bash [[ =~ ]] matches the whole string

When converting a boolean grep check to a pure-bash test in a shell test suite,
respect the semantic boundary: **`grep -E` is line-oriented** — a pattern like
`[^|]*` stops at a newline — but **bash `[[ =~ ]]` matches against the entire
string, newlines included**. Over a multi-line haystack, a `[^|]*` written for a
single line silently spans lines under `=~` and the pattern over-matches. In
PR #584 (ticket 0329) three regex sites converted `grep -Eq` → `[[ =~ ]]`; the
change let a guard's pattern match across newlines so a *removed* timeout
wrapper still matched, disarming the guard. Gaze's reroll caught it; all three
reverted to `grep -Eq`. The regex sites were never the flaky element.

**Convert only what's broken.** The 0329 flake was the per-call
`grep -qF <<<` *here-string boolean* check (a subprocess reading a tmpfile that
intermittently returned no-match under parallel load). Its safe, subprocess-free
equivalent is pure-bash literal substring: `[[ "$hay" == *"$needle"* ]]` — a
quoted needle makes `==` a glob-free literal match, identical to `grep -F`. That
substitution is behavior-preserving; the `grep -Eq` → `=~` one is not. Leave
`grep -v` filters, `grep -c` counters, and `grep -qx` exact-line / small-array
sites alone — different mechanism, not the flake.

Diagnosis note: 0329 went flake-ticket → one-session fix because the failing
runs **dumped the haystack to stderr at failure time**. The dump *contained* the
missed needle with no bash/fork/ENOSPC error — ruling out truncation and pinning
the individual grep call itself as flaky before a line of code was written. A
failure-time haystack dump is what turns a nondeterministic grep flake into a
one-pass diagnosis.
