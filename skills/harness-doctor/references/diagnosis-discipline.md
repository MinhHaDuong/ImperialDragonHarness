# Diagnosis discipline: the elaboration

`rules/workflow.md` § Diagnosis discipline keeps the four principles as one
line each. This page carries the reasoning and the checks behind them.

## Report the observation; hold the cause until isolated

Loaded labels (*corrupt*, *broken*, *tampered*, *hacked*) misdirect the fix.
Write "X emits Y for input Z; cause not yet established".

Two kinds of cheap check, kept apart:
- **Is the observation real?** Is the tool intact, is the result deterministic,
  does an independent path reproduce it? A yes confirms the observation. It says
  nothing about intent: an ordinary bug is deterministic and reproducible too.
- **Is it intended?** Only a specification, documentation upstream, a changelog
  or the code's own stated contract is evidence of intended behaviour.

## A null result is not a finding until a positive control has fired

An empty probe cannot tell "absent" from "invisible to me". Produce a known
positive and watch the probe react; where your tooling cannot, report the one
experiment that would settle it, not a null. Three independent zeros are one
zero measured three times. A null result supports only the tested scope.

A control must exercise the whole path the real case takes: on 2026-11-01 a
control for a git override installed one of the repository's two hooks, passed,
and a documented command still failed on the real checkout.

## A number you divided out is not a number you measured

Label derived quantities as derived, show the arithmetic, say which machine a
number came from, and take the cheap direct measurement *before* recommending on
the inference. An unexplained gap is an open question, not a residual to
attribute.

## Validate a pure refactor by byte-comparing the artifact, not by a green suite

Produce the artifact before and after on the same inputs (`SOURCE_DATE_EPOCH`
set) and compare content; tests pass on a refactor that misplaced its output. A
clean-room render is usually seconds: run it yourself.
