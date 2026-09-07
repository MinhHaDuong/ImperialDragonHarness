#!/usr/bin/env bash
# Guard (ticket 0359): a shell suite must spawn its bash children hermetically.
#
# BASH_ENV points every child bash at scripts/bash-env.sh, which re-runs the
# credential selection at child startup. A suite that spawns `bash -c` without
# clearing that path hands the child whatever the live harness loaded — so a
# failing assertion prints a real credential (two leaked into a terminal and a
# session transcript on 2026-07-27), and an inherited value silently masks the
# behaviour under test (green while testing nothing).
#
# Two remedies are accepted, both already in the tree:
#   * spawn hermetically — `env -i HOME=… PATH=… bash -c …`, every variable the
#     child needs passed explicitly (test_bash_env_keys_selection_explicit.sh);
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
# negative control in section (0c)–(0k) below, which fails against the naive
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
#     `{` `}` or line start) and the `bash` token — never from the whole
#     logical line. An `env -i` sitting elsewhere on the line launders nothing,
#     and a line with N spawns yields N independent verdicts.
#   * The suite-wide `export BASH_ENV=` exemption is matched against the
#     STRIPPED logical lines, so the spelling only counts where it executes.
#   * The spawn shape covers `bash -c`, `bash -lc`, `bash -ec`, long options
#     before it (`bash --posix -c`), an absolute path (`/bin/bash -c`), the
#     `$BASH` / `$SHELL` variable forms, and one level of `eval`/`su`/`sudo`/
#     `ssh`/`xargs` quoting (their quoted argument is re-read as code).
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
#   * A script written by a heredoc and later executed. `bash FILE` takes a
#     script path, not a command string, and is out of this guard's scope by
#     design — but such a child does still inherit BASH_ENV.
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
# `bash …` forms take a script path and are out of scope (see BLIND SPOTS).
_SPAWN_RE='(^|[^[:alnum:]_./-])((/[^[:space:]]*/)?bash|\$\{?(BASH|SHELL)\}?)([[:space:]]+-[^[:space:]]+)*[[:space:]]+-[a-zA-Z]*c([[:space:]]|$)'

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
    local rest="$1" m before tmp seg
    while [[ "$rest" =~ $_SPAWN_RE ]]; do
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
        tmp="${tmp//"{"/$SEP}"
        tmp="${tmp//"}"/$SEP}"
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
    local f="$1" ll lineno s u scanned bad spawns last
    ll="$(_logical_lines "$f")"

    if printf '%s\n' "$ll" | grep -qE -- '^-1'"$LL"; then
        printf 'UNTERMINATED\n'
        return 0
    fi
    if printf '%s\n' "$ll" | grep -qE -- "$LL"'[[:space:]]*export[[:space:]]+BASH_ENV=[[:space:]]*'"$LL"; then
        printf 'EXEMPT\n'
        return 0
    fi

    bad=""
    spawns=0
    last=""
    while IFS="$LL" read -r lineno s u; do
        [ -n "$lineno" ] || continue
        scanned="$s"
        [[ "$s" =~ $_EXEC_RE ]] && scanned="$u"
        [[ "$scanned" =~ $_SPAWN_RE ]] || continue
        _line_spawn_verdicts "$scanned"
        spawns=$((spawns + _LV_TOTAL))
        if [ "$_LV_BAD" -gt 0 ] && [ "$lineno" != "$last" ]; then
            bad="${bad:+$bad,}$lineno"
            last="$lineno"
        fi
    done <<< "$ll"

    if [ -n "$bad" ]; then
        printf 'BAD %s\n' "$bad"
    elif [ "$spawns" -gt 0 ]; then
        printf 'OK %s\n' "$spawns"
    else
        printf 'NONE\n'
    fi
}

# --- (0c)-(0k) static negative controls -----------------------------------------
# The runtime probes above prove the ENFORCED IDIOM works. These prove the
# DETECTOR works, which is a separate claim and the one that rotted: every
# fixture below is a real non-hermetic spawn that the pre-2026-09-07 scanner
# reported as clean (0c-0h), plus the false alarm it raised on inert heredoc
# text (0i), plus the two accepted shapes it must not start rejecting (0j, 0k).
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
            echo "PASS: $b (clears BASH_ENV suite-wide)"
            ;;
        "BAD "*)
            spawners=$((spawners + 1))
            echo "FAIL: $b — non-hermetic bash child spawn at line(s) ${verdict#BAD } (needs 'env -i' or a suite-wide 'export BASH_ENV=')" >&2
            fail=$((fail + 1))
            ;;
        "OK "*)
            spawners=$((spawners + 1))
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
echo "OK: all $checked shell suite(s) spawn bash children hermetically ($spawners spawner(s))"
