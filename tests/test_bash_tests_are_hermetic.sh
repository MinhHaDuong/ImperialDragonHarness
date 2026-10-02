#!/usr/bin/env bash
# Guard (ticket 0359): a shell suite must spawn its bash children hermetically.
#
# BASH_ENV points every child bash at scripts/bash-env.sh, which re-runs the
# project .env parser at child startup. A suite that spawns `bash -c` without
# clearing that path inherits ambient values and can also load fixture-adjacent
# project values, silently masking the behaviour under test.
#
# Two remedies are accepted, both already in the tree:
#   * spawn hermetically — `env -i HOME=… PATH=… bash -c …`, every variable the
#     child needs passed explicitly (test_bash_env_project_env_parse.sh);
#   * clear the loader for the whole suite — `export BASH_ENV=` before any
#     child runs (test_seat_runner.sh, which also unsets the ambient keys it
#     inherited at its own startup).
#
# This guard makes the choice mechanical across every tests/*.sh, discovered by
# glob so a newly added suite is covered without editing this file.
#
# It reports FILE NAMES and LINE NUMBERS only — never the offending text, never
# an environment value. A guard that echoed what it found would reproduce the
# defect it exists to prevent.
#
# See rules/coding-bash.md § "Unsetting a variable in the parent does not unset
# it in the child".
#
# ---------------------------------------------------------------------------
# HOW IT LOOKS, AND WHAT IT STILL CANNOT SEE
#
# A guard whose "all clear" cannot be told from "I could not look" is not a
# guard. This one is a TEXTUAL scanner over shell source, and a textual scanner
# over shell is necessarily incomplete: the shell decides what is a command at
# runtime. So the coverage is stated here rather than implied.
#
# What it does look at, and why each step exists (each is pinned by a static
# negative control in section (0c)–(0p) below, which fails against the naive
# implementation and passes against this one):
#
#   * Heredoc BODIES are excluded before anything else. Their text is data, so
#     an `export BASH_ENV=` written inside one must not exempt the suite, and a
#     `bash -c` written inside one must not be reported. Delimiters are found
#     heuristically (`<<WORD`, `<<-WORD`, quoted or not; `<<<` herestrings are
#     not heredocs). An UNTERMINATED heredoc means that heuristic was wrong and
#     the rest of the file was skipped blind — the guard fails loudly on it
#     rather than reporting a clean file it never read.
#   * COMMENTS are stripped per PHYSICAL line, BEFORE backslash continuations
#     are folded. The other order lets a comment ending in a backslash swallow
#     the following line, hiding a real spawn inside a discarded buffer.
#   * QUOTED string content is dropped, so `bash -c` inside a grep pattern or a
#     failure message is data, not an invocation — EXCEPT that `$( … )` and
#     backtick command substitutions are kept as CODE even inside double quotes,
#     because they execute. `out="$(bash -c …)"` really does spawn a child.
#   * A spawn's hermeticity is judged from ITS OWN command prefix — the text
#     between the nearest preceding separator (`;` `&&` `||` `|` `&` `(` `)`
#     or line start) and the `bash` token — never from the whole
#     logical line. An `env -i` sitting elsewhere on the line launders nothing,
#     and a line with N spawns yields N independent verdicts. `{` and `}` are
#     NOT separators: they open parameter expansions (`${ARR[@]}`), so
#     treating them as command boundaries would cut an `env -i` prefix at an
#     array expansion (control 0o) — brace GROUPS always carry a `;` or
#     newline that already delimits.
#   * The suite-wide `export BASH_ENV=` exemption is matched against the
#     STRIPPED logical lines, so the spelling only counts where it executes —
#     parsed in the same read pass that scans the file. No second tool re-reads
#     the raw \001-delimited stream: a cross-tool byte contract there is what
#     made the same file BAD on one CI runner and EXEMPT on another (0875).
#   * The spawn shape covers `bash -c`, `bash -lc`, `bash -ec`, long options
#     before it (`bash --posix -c`), an absolute path (`/bin/bash -c`), the
#     `$BASH` / `$SHELL` variable forms, and one level of `eval`/`su`/`sudo`/
#     `ssh`/`xargs` quoting (their quoted argument is re-read as code). The
#     SCRIPT-PATH shape (`bash FILE`, no `-c` — the normal hook invocation,
#     ticket 0875) is detected too, on the quote-unwrapped stream gated by the
#     interpreter appearing as code outside quotes, so a quoted path
#     (`bash "$HOOK"`) survives the quote stripping while quoted DATA naming
#     a path does not (control 0p).
#
# BLIND SPOTS — shapes this scanner does NOT detect. Listed so a reader knows
# what a PASS is worth; none is closed by pretending otherwise:
#
#   * A spawn whose program name is computed — `$RUNNER -c …`, `"${sh}" -c …`,
#     `cmd="bash -c …"; $cmd`, or any name assembled at runtime. Only the
#     literal `bash`, an absolute path ending in `bash`, `$BASH` and `$SHELL`
#     are recognised.
#   * A spawn behind a wrapper outside the `eval|su|sudo|ssh|xargs` list, or
#     behind two levels of quoting (`eval "eval \"bash -c …\""`).
#   * `bash --rcfile FILE -c …` and other option forms where a long option
#     takes a SEPARATE argument word before `-c`.
#   * A script written by a heredoc and later executed. `bash FILE` where FILE
#     is computed at runtime is out of scope, but such a child does still
#     inherit BASH_ENV — as does `bash -x FILE` (options before the path are
#     still not parsed).
#   * In the script-path shape, the FILE token must look like a path: it
#     starts with `$`, `~`, or carries a `/`. A BARE FILENAME (`bash probe.sh`)
#     is missed — a reader of "carries a /" must not expect otherwise.
#   * The interpreter spelled as a RELATIVE path (`./bash FILE`, `bin/bash
#     FILE`) is missed: the recognised program forms are the literal `bash`,
#     an ABSOLUTE path ending in `bash`, `$BASH` and `$SHELL`. A QUOTED program
#     (`"bash" FILE`) is missed too — the gate needs the interpreter as code
#     outside quotes.
#   * Unquoted inert prose naming a script path (`echo run bash /tmp/x.sh now`)
#     reads as code on the unwrapped stream and is reported — the same safe
#     direction as the `bash -c` false alarms below; quoting is what separates
#     data from code here.
#   * `env -i` reached indirectly (a helper function that spawns hermetically
#     on the caller's behalf) is reported as non-hermetic. That is the safe
#     direction — a false alarm, not a miss — and is fixed by inlining the
#     `env -i` or exempting the suite.
#   * Quote state resets at each physical line, so a `bash -c` inside a quoted
#     string that spans several lines is read as code. Also the safe direction.
#
# This file excludes ITSELF from the scan, and must: control (0a) below is a
# deliberately non-hermetic spawn — that is the whole point of a positive
# control — and the detector flags it correctly when pointed at a copy of this
# file under another name.
# ---------------------------------------------------------------------------
set -euo pipefail
export LC_ALL=C

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$(basename "${BASH_SOURCE[0]}")"

fail=0
checked=0
spawners=0
judged=0
exempt=0

# Field separator for the logical-line stream, and the separator sentinel used
# when slicing a spawn's own command prefix. Both are control characters that
# cannot occur in shell source. \001 is deliberately NOT tab: tab is IFS
# whitespace, so consecutive tabs collapse and an empty middle field (a blank
# source line) would silently shift every later field left.
LL=$'\001'
SEP=$'\002'

# --- (0) runtime proof that the idiom this guard enforces actually works --------
# A static scan whose "all clear" is indistinguishable from "I never looked" is
# not a check, so run it first against a case known to be POSITIVE. The probe
# uses a FAKE sentinel loader — a throwaway script exporting a recognisable dummy
# — never a real key: verifying with the live credential is how the 2026-07-27
# leak happened a second time. Both probes assert on a presence BOOLEAN; neither
# ever prints what it found.
_SENTINEL_DIR="$(mktemp -d)"
trap 'rm -rf "$_SENTINEL_DIR"' EXIT
printf 'export HERMETIC_PROBE_0359=dummy-sentinel-value\n' > "$_SENTINEL_DIR/loader.sh"

# (0a) Positive control: the plain `HOME=… bash -c` form — what the four suites
# used before ticket 0359 — DOES receive whatever BASH_ENV injects at child
# startup. If this comes back empty the probe is broken, not the tree clean.
_probe_leaky="$(BASH_ENV="$_SENTINEL_DIR/loader.sh" HOME="$_SENTINEL_DIR" \
    bash -c 'printf "%s" "${HERMETIC_PROBE_0359:-}"')"
if [ -z "$_probe_leaky" ]; then
    echo "FAIL: (0a) positive control saw nothing — the BASH_ENV probe is broken, so this guard proves nothing" >&2
    exit 1
fi
echo "PASS: (0a) positive control — a non-hermetic child does inherit the loader"

# (0b) The enforced form: `env -i` clears BASH_ENV, so the same child startup
# injects nothing. This is the property every conversion relies on.
_probe_hermetic="$(BASH_ENV="$_SENTINEL_DIR/loader.sh" \
    env -i HOME="$_SENTINEL_DIR" PATH="$PATH" \
    bash -c 'printf "%s" "${HERMETIC_PROBE_0359:-}"')"
if [ -n "$_probe_hermetic" ]; then
    echo "FAIL: (0b) an 'env -i' child still inherited the loader — the enforced idiom does not hold here" >&2
    exit 1
fi
echo "PASS: (0b) an 'env -i' child inherits nothing from the loader"
unset _probe_leaky _probe_hermetic

# Emit the file's logical lines as "<first-lineno>\001<code>\001<unwrapped>":
#
#   * heredoc BODY lines are dropped entirely (their text never executes);
#   * comments are removed per physical line, and only THEN is a trailing
#     backslash treated as a continuation — so a comment ending in a backslash
#     cannot fold, and hide, the line after it;
#   * <code> has quoted string content removed, leaving shell code only, but
#     KEEPS `$( … )` and backtick substitutions, which execute even inside
#     double quotes;
#   * <unwrapped> is the same with one level of quoting removed instead of
#     dropped, so `eval "bash -c …"` can be re-read as the code it becomes.
#
# Quote state resets at each physical line: the body of a multi-line `bash -c
# '…'` is then read as code, which can only add candidates, never hide one.
_logical_lines() {
    awk '
        function strip(s, keep,   i, c, n, out, sp, st, last, stk) {
            n = length(s); out = ""; sp = 1; stk[1] = "C"
            for (i = 1; i <= n; i++) {
                c = substr(s, i, 1)
                st = stk[sp]
                if (st == "C" || st == "U" || st == "B") {
                    if (c == "\\") {
                        if (i == n) { out = out "\\"; continue }
                        out = out " "; i++; continue
                    }
                    if (c == SQ) { sp++; stk[sp] = "Q"; continue }
                    if (c == DQ) { sp++; stk[sp] = "D"; continue }
                    if (c == "$" && substr(s, i + 1, 1) == "(") { sp++; stk[sp] = "U"; out = out " "; i++; continue }
                    if (c == "`") { sp++; stk[sp] = "B"; out = out " "; continue }
                    if (st == "U" && c == ")") { sp--; out = out " "; continue }
                    if (st == "B" && c == "`") { sp--; out = out " "; continue }
                    if (c == "#") {
                        last = (out == "") ? "" : substr(out, length(out), 1)
                        if (out == "" || last == " " || last == "\t") break
                    }
                    out = out c
                    continue
                }
                if (st == "Q") {
                    if (c == SQ) { sp--; continue }
                    if (keep) out = out c
                    continue
                }
                if (c == "\\") { if (keep && i < n) out = out substr(s, i + 1, 1); i++; continue }
                if (c == DQ) { sp--; continue }
                if (c == "$" && substr(s, i + 1, 1) == "(") { sp++; stk[sp] = "U"; out = out " "; i++; continue }
                if (c == "`") { sp++; stk[sp] = "B"; out = out " "; continue }
                if (keep) out = out c
            }
            return out
        }
        # Register every heredoc opened by one complete logical line, in order.
        function reghd(rawl,   t, m, d, dash) {
            t = rawl
            gsub(/<<</, "@@@", t)
            while (match(t, /<<-?[ \t]*[^ \t;&|<>()]+/)) {
                m = substr(t, RSTART, RLENGTH)
                t = substr(t, RSTART + RLENGTH)
                dash = (substr(m, 3, 1) == "-") ? 1 : 0
                d = substr(m, dash ? 4 : 3)
                sub(/^[ \t]+/, "", d)
                gsub(SQ, "", d); gsub(DQ, "", d); gsub(/\\/, "", d)
                if (d !~ /^[A-Za-z_][A-Za-z0-9_]*$/) continue
                hdn++; hdd[hdn] = d; hdtab[hdn] = dash
            }
        }
        BEGIN { SQ = sprintf("%c", 39); DQ = sprintf("%c", 34)
                hdn = 0; buf = ""; ubuf = ""; rawbuf = ""; start = 0 }
        {
            if (hdn > 0) {
                t = $0
                if (hdtab[1] == 1) sub(/^[ \t]+/, "", t)
                sub(/[ \t]+$/, "", t)
                if (t == hdd[1]) {
                    for (k = 1; k < hdn; k++) { hdd[k] = hdd[k + 1]; hdtab[k] = hdtab[k + 1] }
                    hdn--
                }
                next
            }
            if (rawbuf == "") start = NR
            s = strip($0, 0)
            u = strip($0, 1)
            if (s ~ /\\$/) {
                sub(/\\$/, " ", s); sub(/\\$/, " ", u)
                buf = buf s; ubuf = ubuf u; rawbuf = rawbuf $0 " "
                next
            }
            buf = buf s; ubuf = ubuf u; rawbuf = rawbuf $0
            if (index(buf, "<<") > 0) reghd(rawbuf)
            printf "%s\001%s\001%s\n", start, buf, ubuf
            buf = ""; ubuf = ""; rawbuf = ""
        }
        END {
            if (rawbuf != "") printf "%s\001%s\001%s\n", start, buf, ubuf
            if (hdn > 0) printf "-1\001\001\n"
        }
    ' "$1"
}

# A child shell running a COMMAND STRING. Covers `bash -c`, clustered short
# flags (`-lc`, `-ec`), long options before it (`bash --posix -c`), an absolute
# path (`/bin/bash -c`), and the `$BASH` / `$SHELL` variable forms. Other
# `bash …` forms take a script path and are covered by _SCRIPT_SPAWN_RE below.
_SPAWN_RE='(^|[^[:alnum:]_./-])((/[^[:space:]]*/)?bash|\$\{?(BASH|SHELL)\}?)([[:space:]]+-[^[:space:]]+)*[[:space:]]+-[a-zA-Z]*c([[:space:]]|$)'

# A child shell running a SCRIPT PATH — `bash FILE` with no `-c` (ticket 0875:
# the normal hook-invocation shape the pre-0875 scanner could not see at all).
# The token after the program must be a PATH and not an option: it either starts
# with `$` (a variable holding the path), or it carries a `/` (a relative,
# `./`, or absolute path). Options before the path (`bash -x FILE`) stay out of
# scope, exactly as before. Matched against the QUOTE-UNWRAPPED stream only,
# and only through the gate below: the dominant real shape is `bash "$HOOK"`,
# and the code stream drops quoted content, so the path would otherwise vanish
# before the regex ever ran — but the unwrapped stream also carries quoted
# DATA, so a line is scanned only when its CODE stream names the interpreter.
_SCRIPT_SPAWN_RE='(^|[^[:alnum:]_./=-])((/[^[:space:]]*/)?bash|\$\{?(BASH|SHELL)\}?)[[:space:]]+(\$[^[:space:]]*|[^[:space:]-][^[:space:]]*/[^[:space:]]*|~[^[:space:]]*)'

# The gate for _SCRIPT_SPAWN_RE: the interpreter named as CODE — at a word
# boundary outside quotes (`=` is not one: `SHELL=/bin/bash` is an assignment
# value, not a command), or an exec-wrapper whose quoted argument re-enters as
# code. Inert quoted text (`echo "docs: run bash /tmp/foo.sh"`, a grep
# pattern, an assignment value) has no interpreter in its code stream and is
# never scanned (control 0p).
_SCRIPT_GATE_RE='(^|[^[:alnum:]_./=-])((/[^[:space:]]*/)?bash|\$\{?(BASH|SHELL)\}?)'

# Wrappers that EXECUTE their quoted argument. On a line containing one, the
# quote-unwrapped variant is scanned instead, so `eval "bash -c …"` is seen.
_EXEC_RE='(^|[^[:alnum:]_])(eval|su|sudo|ssh|xargs)([[:space:]]|$)'

# Count the spawns on one logical line and how many of them are non-hermetic.
# Each spawn is judged on ITS OWN command prefix, so an unrelated `env -i`
# elsewhere on the line launders nothing and one hermetic spawn cannot mask a
# second non-hermetic one beside it. Sets _LV_TOTAL and _LV_BAD.
_line_spawn_verdicts() {
    _LV_TOTAL=0
    _LV_BAD=0
    local re="$2" rest="$1" m before tmp seg
    while [[ "$rest" =~ $re ]]; do
        m="${BASH_REMATCH[0]}"
        # Text before this spawn, plus the boundary character the match ate.
        before="${rest%%"$m"*}${BASH_REMATCH[1]}"
        tmp="${before//"&&"/$SEP}"
        tmp="${tmp//"||"/$SEP}"
        tmp="${tmp//";"/$SEP}"
        tmp="${tmp//"|"/$SEP}"
        tmp="${tmp//"&"/$SEP}"
        tmp="${tmp//"("/$SEP}"
        tmp="${tmp//")"/$SEP}"
        seg="${tmp##*"$SEP"}"
        _LV_TOTAL=$((_LV_TOTAL + 1))
        if [[ "$seg" != *"env -i"* && "$seg" != *"env --ignore-environment"* ]]; then
            _LV_BAD=$((_LV_BAD + 1))
        fi
        rest="${rest#*"$m"}"
    done
}

# One file, one verdict: EXEMPT | "OK <n>" | "BAD <linenos>" | NONE |
# UNTERMINATED (the heredoc heuristic lost track — the file was NOT fully read).
_file_verdict() {
    local f="$1" ll lineno s u scanned bad spawns last line_total line_bad exempt
    ll="$(_logical_lines "$f")"

    if printf '%s\n' "$ll" | grep -qE -- '^-1'"$LL"; then
        printf 'UNTERMINATED\n'
        return 0
    fi

    bad=""
    spawns=0
    last=""
    exempt=0
    while IFS="$LL" read -r lineno s u; do
        [ -n "$lineno" ] || continue
        # Suite-wide exemption, matched on the CODE field of the stripped
        # logical line — parsed in THIS read loop, the same pass that scans
        # the spawns. It used to be a second tool (grep -E over the raw
        # \001-delimited stream); that cross-tool byte contract is what
        # diverged between CI runners (0875: same bytes, same script, BAD on
        # one runner image, EXEMPT on another), so the exemption now lives in
        # one implementation only. Heredoc bodies never reach a field here,
        # so an `export BASH_ENV=` inside one still does not exempt (0d).
        if [[ "$s" =~ ^[[:space:]]*export[[:space:]]+BASH_ENV=[[:space:]]*$ ]]; then
            exempt=1
            break
        fi
        scanned="$s"
        [[ "$s" =~ $_EXEC_RE ]] && scanned="$u"
        line_total=0
        line_bad=0
        # Command-string form (`bash -c …`) on the code stream — or on the
        # unwrapped one when an exec-wrapper quotes it.
        if [[ "$scanned" =~ $_SPAWN_RE ]]; then
            _line_spawn_verdicts "$scanned" "$_SPAWN_RE"
            line_total=$((_LV_TOTAL + line_total))
            line_bad=$((_LV_BAD + line_bad))
        fi
        # Script-path form (`bash FILE`) on the UNWRAPPED stream, gated on the
        # interpreter being named as code outside quotes (or an exec-wrapper
        # re-entering as code): the path is usually quoted, and quoted content
        # is absent from the code stream, but the unwrapped stream also carries
        # quoted data (control 0p). The two shapes are near-mutually-exclusive:
        # the script-path token must not start with `-`, and the command-string
        # form must end in a `-c` flag. A `bash FILE -c …` shape can satisfy
        # both (the `-c` lands in the code stream once the quoted FILE drops
        # out) and counts twice — the safe direction, and rarer than rare.
        if [[ "$s" =~ $_SCRIPT_GATE_RE || "$s" =~ $_EXEC_RE ]] && [[ "$u" =~ $_SCRIPT_SPAWN_RE ]]; then
            _line_spawn_verdicts "$u" "$_SCRIPT_SPAWN_RE"
            line_total=$((_LV_TOTAL + line_total))
            line_bad=$((_LV_BAD + line_bad))
        fi
        spawns=$((spawns + line_total))
        if [ "$line_bad" -gt 0 ] && [ "$lineno" != "$last" ]; then
            bad="${bad:+$bad,}$lineno"
            last="$lineno"
        fi
    done <<< "$ll"

    if [ "$exempt" -eq 1 ]; then
        printf 'EXEMPT\n'
        return 0
    fi
    if [ -n "$bad" ]; then
        printf 'BAD %s\n' "$bad"
    elif [ "$spawns" -gt 0 ]; then
        printf 'OK %s\n' "$spawns"
    else
        printf 'NONE\n'
    fi
}

# --- (0c)-(0p) static negative controls -----------------------------------------
# The runtime probes above prove the ENFORCED IDIOM works. These prove the
# DETECTOR works, which is a separate claim and the one that rotted: every
# fixture below is a real non-hermetic spawn that the pre-2026-09-07 scanner
# reported as clean (0c-0h), plus the false alarm it raised on inert heredoc
# text (0i), plus the two accepted shapes it must not start rejecting (0j, 0k),
# plus the script-path class the pre-0875 scanner could not see at all — both
# its leak (0l) and its accepted remedy (0m) — plus the silence that must stay
# silent (0n), plus the expansion-prefix and inert-data shapes the 0875
# widening must not start rejecting (0o, 0p).
# Fixtures live in a mktemp dir, never under tests/, so they are not themselves
# discovered as suites. They contain no secret and no real credential.
_FIXDIR="$(mktemp -d)"
trap 'rm -rf "$_SENTINEL_DIR" "$_FIXDIR"' EXIT

_fixture() {  # name, then body on stdin
    cat > "$_FIXDIR/$1"
}

_expect_verdict() {  # id, expected-verdict, fixture-name, description
    local got
    got="$(_file_verdict "$_FIXDIR/$3")"
    if [ "$got" != "$2" ]; then
        echo "FAIL: ($1) detector control expected '$2', got '$got' — the static scan cannot be trusted" >&2
        exit 1
    fi
    echo "PASS: ($1) $4"
}

_fixture masked.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
_leaky() { env -i true; bash -c 'printf "%s" "${SOME_TOKEN:-}"'; }
_leaky
FIXTURE
_expect_verdict 0c "BAD 3" masked.sh \
    "an unrelated 'env -i' on the same line does not launder the spawn beside it"

_fixture heredoc_exempt.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
cat > /dev/null <<'DOC'
       export BASH_ENV=
DOC
bash -c 'printf hi'
FIXTURE
_expect_verdict 0d "BAD 6" heredoc_exempt.sh \
    "'export BASH_ENV=' inside a heredoc body does not exempt the suite"

_fixture cont_comment.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
# a comment that ends in a backslash \
bash -c 'printf hi'
FIXTURE
_expect_verdict 0e "BAD 4" cont_comment.sh \
    "a comment ending in a backslash does not swallow the spawn after it"

_fixture cmd_subst.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
out="$(bash -c 'printf hi')"
printf '%s\n' "$out"
FIXTURE
_expect_verdict 0f "BAD 3" cmd_subst.sh \
    "a command substitution inside double quotes is code, not inert data"

_fixture long_option.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
bash --posix -c 'printf hi'
FIXTURE
_expect_verdict 0g "BAD 3" long_option.sh \
    "a long option before -c does not hide the spawn"

_fixture eval_wrapped.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
eval "bash -c 'printf hi'"
FIXTURE
_expect_verdict 0h "BAD 3" eval_wrapped.sh \
    "one level of eval quoting does not hide the spawn"

_fixture heredoc_data.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
cat > /dev/null <<'DOC'
bash -c "documentation, never executed"
DOC
env -i PATH="$PATH" bash -c 'printf hi'
FIXTURE
_expect_verdict 0i "OK 1" heredoc_data.sh \
    "inert heredoc text is not reported as a spawn (no false alarm)"

_fixture hermetic.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
env -i HOME=/tmp PATH="$PATH" bash -c 'printf hi'
FIXTURE
_expect_verdict 0j "OK 1" hermetic.sh \
    "the enforced 'env -i' idiom is still accepted"

_fixture suite_exempt.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
export BASH_ENV=
bash -c 'printf hi'
FIXTURE
_expect_verdict 0k "EXEMPT" suite_exempt.sh \
    "a real suite-wide 'export BASH_ENV=' is still accepted"

# (0l)-(0n) close the 0875 gap: the SCRIPT-PATH form (`bash FILE`, no -c). The
# pre-0875 scanner could not see it at all, so both (0l) and (0m) FAIL against
# that scanner — (0l) is the positive control the ticket demands: a script-path
# spawn without 'env -i' must be BAD, not an invisible SKIP.
_fixture script_leaky.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
bash "$HOOK_DIR/probe.sh"
FIXTURE
_expect_verdict 0l "BAD 3" script_leaky.sh \
    "a script-path spawn (bash FILE, no -c) is seen and judged non-hermetic"

_fixture script_hermetic.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
env -i HOME=/tmp PATH="$PATH" bash "$HOOK_DIR/probe.sh"
FIXTURE
_expect_verdict 0m "OK 1" script_hermetic.sh \
    "the 'env -i' idiom covers the script-path form too"

_fixture no_spawn.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
echo "nothing to spawn here"
FIXTURE
_expect_verdict 0n "NONE" no_spawn.sh \
    "a file with no bash child stays NONE — the widening turns no silence into noise"

# (0o) pins the 0875 widening against its own collateral: a parameter
# expansion (`${ARR[@]+…}`) between `env -i` and the spawn is NOT a command
# boundary, so the prefix judgement must keep seeing the `env -i`.
_fixture array_env_prefix.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
env -i HOME=/tmp PATH="$PATH" ${H_ENV[@]+"${H_ENV[@]}"} bash "$HOOK_DIR/probe.sh"
FIXTURE
_expect_verdict 0o "OK 1" array_env_prefix.sh \
    "an array expansion between 'env -i' and the spawn does not cut the prefix"

# (0p) pins the boundary of the 0875 widening: the unwrapped stream carries
# quoted DATA as well as quoted CODE, and inert text naming a script path must
# not be reported. The code stream gates the unwrapped scan (see the scanner
# contract): a real invocation names the interpreter as code, outside quotes.
_fixture script_inert_quoted.sh <<'FIXTURE'
#!/usr/bin/env bash
set -euo pipefail
echo "docs: run bash /tmp/foo.sh for help"
grep -q "bash ./hook.sh" out.txt
env HOME=/tmp SHELL="/bin/bash" ./run.sh
FIXTURE
_expect_verdict 0p "NONE" script_inert_quoted.sh \
    "inert quoted text naming a script path is data, not a spawn"

# --- the scan ------------------------------------------------------------------
for f in "$TESTS_DIR"/test_*.sh; do
    b="$(basename "$f")"
    [ "$b" = "$SELF" ] && continue
    checked=$((checked + 1))

    verdict="$(_file_verdict "$f")"
    case "$verdict" in
        UNTERMINATED)
            echo "FAIL: $b — unterminated heredoc: the scanner lost track and did not read the whole file" >&2
            fail=$((fail + 1))
            ;;
        EXEMPT)
            spawners=$((spawners + 1))
            exempt=$((exempt + 1))
            echo "PASS: $b (clears BASH_ENV suite-wide)"
            ;;
        "BAD "*)
            spawners=$((spawners + 1))
            # Failure diagnostic (0875 CI divergence): a suite that looks
            # exempt yet lands BAD means the exemption pattern never reached
            # the verdict's read loop. raw-export-line reads the FILE;
            # stream-exempt-token is an INDEPENDENT re-check of the logical
            # stream by grep — the tool the verdict no longer trusts — so a
            # disagreement between the two names the diverging layer in one
            # read of the log. Names and numbers only.
            diag_raw=0
            if grep -qE '^[[:space:]]*export[[:space:]]+BASH_ENV=' "$f"; then diag_raw=1; fi
            diag_tok=0
            diag_ll="$(_logical_lines "$f")"
            if printf '%s\n' "$diag_ll" | grep -qE -- "$LL"'[[:space:]]*export[[:space:]]+BASH_ENV=[[:space:]]*'"$LL"; then diag_tok=1; fi
            diag_stream_lines=$(printf '%s\n' "$diag_ll" | wc -l)
            diag_file_lines=$(wc -l < "$f")
            echo "FAIL: $b — non-hermetic bash child spawn at line(s) ${verdict#BAD } (needs 'env -i' or a suite-wide 'export BASH_ENV=') [diagnostic: raw-export-line=$diag_raw stream-exempt-token=$diag_tok stream-lines=$diag_stream_lines file-lines=$diag_file_lines]" >&2
            fail=$((fail + 1))
            ;;
        "OK "*)
            spawners=$((spawners + 1))
            judged=$((judged + ${verdict#OK }))
            echo "PASS: $b (${verdict#OK } hermetic spawn(s))"
            ;;
        *)
            echo "SKIP: $b (spawns no bash child)"
            ;;
    esac
done

if [ "$checked" -eq 0 ]; then
    echo "FAIL: no tests/test_*.sh found — guard has nothing to protect" >&2
    exit 1
fi
if [ "$spawners" -eq 0 ]; then
    echo "FAIL: no suite spawns a bash child — guard is vacuous, check its detection" >&2
    exit 1
fi
if [ "$fail" -ne 0 ]; then
    echo "GUARD FAILED: $fail of $checked shell suite(s) spawn bash children non-hermetically" >&2
    exit 1
fi
# The verdict line must not read files-read as coverage (ticket 0875): the
# first number is what was READ, the second what was actually EXAMINED. A
# suite-wide exemption skips its spawns, so those appear in neither count's
# denominator silently — the exempt count keeps that visible.
echo "OK: $checked shell suite(s) read — $judged bash child spawn(s) examined, all hermetic ($spawners spawner file(s), $exempt suite-wide exempt)"
