#!/usr/bin/env python3
"""Classify every permission allow rule: dead path, one-shot literal, or subsumed.

An allow rule is not free. It is read on every tool call, it is resident context
the model must weigh, and a stale one silently grants nothing while looking like
policy. The three cheap discriminators here are mechanical; a fourth -- did this
rule ever actually match a command? -- is answered from the session logs.
"""
import argparse
import json
import os
import re
from pathlib import Path

PATHS = re.compile(r"(?:^|[\s(\"'])(/[^\s\"')]+|~/[^\s\"')]+)")
WILDCARD = re.compile(r"[*?]")


def rule_body(rule: str) -> tuple[str, str]:
    m = re.match(r"^([A-Za-z_]+)\((.*)\)$", rule, re.S)
    return (m.group(1), m.group(2)) if m else (rule, "")


def dead_paths(body: str) -> list[str]:
    """Absolute paths the rule names that do not exist.

    A trailing `:*` is the prefix-match syntax of the permission grammar, not
    part of the path. Reading it as one reported the live `erg-pr-merge` script
    as dead on the first run -- the kind of false positive that discredits a
    whole sweep, so it is stripped before any path is probed.
    """
    body = body.removesuffix(":*")
    out = []
    for m in PATHS.finditer(body):
        raw = m.group(1)
        p = raw.lstrip("/") if raw.startswith("//") else raw
        p = os.path.expanduser(p if p.startswith(("/", "~")) else "/" + p)
        probe = WILDCARD.split(p)[0].rstrip("/")
        # walk up to the last concrete ancestor the rule names
        while probe and not Path(probe).exists() and "/" in probe:
            parent = probe.rsplit("/", 1)[0]
            if parent == probe:
                break
            if Path(parent).exists():
                out.append(raw)
                break
            probe = parent
        else:
            if probe and not Path(probe).exists():
                out.append(raw)
    return out


def subsumed_by(rule: str, others: list[str]) -> str | None:
    tool, body = rule_body(rule)
    for other in others:
        if other == rule:
            continue
        t2, b2 = rule_body(other)
        if t2 != tool or not WILDCARD.search(b2):
            continue
        pat = "^" + re.escape(b2).replace(r"\*", ".*").replace(r"\?", ".") + "$"
        if re.match(pat, body):
            return other
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", required=True)
    a = ap.parse_args()
    rules = json.load(open(a.settings))["permissions"]["allow"]

    dead, oneshot, sub, keep = [], [], [], []
    for r in rules:
        _tool, body = rule_body(r)
        s = subsumed_by(r, rules)
        d = dead_paths(body)
        if d:
            dead.append((r, d))
        elif s:
            sub.append((r, s))
        elif body and not WILDCARD.search(body) and len(body) > 40:
            oneshot.append(r)
        else:
            keep.append(r)

    print(f"{len(rules)} regles\n")
    print(f"== chemin inexistant ({len(dead)}) ==")
    for r, d in dead:
        print(f"  {r[:110]}\n      -> absent: {d[0][:90]}")
    print(f"\n== subsumee par une regle plus large ({len(sub)}) ==")
    for r, s in sub:
        print(f"  {r[:100]}\n      -> couverte par {s}")
    print(f"\n== litteral long sans joker, tire une fois ({len(oneshot)}) ==")
    for r in oneshot:
        print(f"  {r[:130]}")
    print(f"\n== conservees ({len(keep)}) ==")
    for r in keep:
        print(f"  {r[:110]}")


main()
