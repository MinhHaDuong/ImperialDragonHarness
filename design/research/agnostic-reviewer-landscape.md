# Agnostic agentic code-verification landscape

> Deep-research report supporting the verify external-reviewer panel
> (tickets 0205/0206/0207/0208) and the sandbox-runner spinoff.
> Generated 2026-06-05 via the deep-research workflow (28 sources fetched,
> 137 claims extracted, 25 verified by 3-vote adversarial panel, 22 confirmed).
> Independently corroborated by the PR #289 architecture panel (4 reviewers).

## Question

Survey agent- and model-agnostic tools for agentic code verification that can
be driven as **read-only** reviewer "seats" from a CLI harness: a `/verify`
pipeline running 2–4 decorrelated reviewers over a diff, collecting normalized
findings (severity + file:line + rationale), dispositioned at a merge gate.

## Headline verdict: ASSEMBLE, don't buy or build-from-scratch

No single existing tool delivers the full stack (decorrelated panel +
read-only containment + normalized findings). The recommended shape is a thin
assembly: wrap agnostic CLI agents as subprocess reviewer seats, run **each
inside an OS-level sandbox**, and normalize their output yourself.

## The load-bearing finding — containment is OS-level, not protocol-level

Genuine read-only / no-mutation / no-exfiltration containment must come from
**OS-level sandboxing**, NOT from agent "modes" or protocol capability grants:

- **Cooperative-only (a compliant agent voluntarily honors; bypassable):**
  ACP capability grants (`fs.readTextFile` granted, `fs.writeTextFile`
  withheld), A2A's opacity model, and aider's `--ask` mode are all
  protocol/behavioral guarantees. A non-compliant or prompt-injected agent
  ignores them. (copilot-cli issue #845 shows agents can auto-approve/bypass.)
- **Kernel-enforced (holds against a misbehaving process):** Claude Code
  (Seatbelt on macOS, bubblewrap on Linux/WSL2; boundaries inherited by child
  processes; writes restricted to cwd by default) and Codex (bubblewrap
  `--ro-bind / /` mounting the whole FS read-only) give real write containment.

This directly confirms the PR #289 red-team BLOCKER: "containment by capability
omission" is **false as a structural claim** unless backed by an OS sandbox.

### Even OS sandboxes leak by default

- Credential files (`~/.aws/credentials`, `~/.ssh`) remain **readable** unless
  explicitly added to `denyRead`.
- Network filtering allowlists hostnames **without TLS inspection**, so a broad
  allowed domain (e.g. `github.com`) leaves a domain-fronting exfiltration path.
- Anthropic's own doc warns: *"Effective sandboxing requires both filesystem
  and network isolation. Without network isolation, a compromised agent could
  exfiltrate sensitive files like SSH keys."* The sandbox "is not a complete
  isolation boundary."
- Version-dependent: Claude Code's `settings.json` self-protection had a hole
  (CVE-2026-25725, fixed v2.1.2) when the file was missing.

## Candidate matrix (verified claims)

| Tool | License | Model-agnostic | Headless invocation | Read-only mode | Maturity |
|------|---------|----------------|---------------------|----------------|----------|
| **PR-Agent** | Apache-2.0 (reverted from AGPL, Apr 2026 community handover to The-PR-Agent org) | Yes — LiteLLM (OpenAI/Claude/Deepseek/Gemini/local); self-hostable air-gapped | `pr-agent --pr_url <URL> review` | **No** documented write-prevention mode (refuted 0-3) | Active, but ownership transition = maturity risk |
| **aider** | Apache-2.0 | Yes — "almost any LLM" incl. local (Ollama/OpenAI-compatible) | one-shot `--message`, then exits | `--chat-mode ask` discusses, never edits — but **prompt-level only**, and default `--message` DOES edit | Active |
| **ACP** (Zed) | Apache (JSON-RPC) | Per-agent (each owns its model/auth) | substrate, not a reviewer | capability grant + permission flow — **cooperative only** | Active, multi-vendor (7 agents bound) |
| **A2A** (Google→Linux Foundation) | Open, LF-governed | design-intent agnostic | agent-to-agent, not a code-review tool | no read-only mechanism; opacity ≠ sandbox | Active; academic critiques flag deployment gaps |

## Honest gaps (did NOT survive verification / unaddressed)

1. **Decorrelation evidence — ABSENT.** No claim substantiating that
   multi-model cross-vendor ensembles catch more *real* defects than one strong
   model survived verification. This is the **premise** of the whole 2–4-seat
   panel. → Dedicated follow-up launched (deep-research wbclco9po, 2026-06-05),
   framed around whether Linus's Law transfers from human review to LLMs.
2. **Output normalization — UNVERIFIED.** No evidence on structured-output
   (JSON/SARIF) support for any candidate. Free-text → {severity, file:line}
   is the make-or-break cost of "assemble"; currently unquantified.
3. **Coverage gaps.** Gemini CLI, Copilot CLI, Codex-as-reviewer, Continue,
   Cline, OpenHands, CodeRabbit, Danger, Semgrep-as-LLM, reviewdog —
   read-only modes, headless invocation, and licenses unassessed.

## Implication for the spinoff

The spinoff is NOT "an ACP client." It is a small **sandbox-runner +
output-normalizer**: a wrapper that turns any agnostic CLI agent into a
contained reviewer seat (run inside Seatbelt/bubblewrap with scoped FS +
network isolation; capture and normalize findings). ACP becomes optional
plumbing; the OS sandbox is the load-bearing requirement; the unresolved
decorrelation question should gate how many seats are worth running at all.

## Sources (primary)

- PR-Agent: https://github.com/The-PR-Agent/pr-agent ·
  https://github.com/qodo-ai/pr-agent ·
  https://www.qodo.ai/blog/qodo-is-handing-pr-agent-over-to-the-community/
- aider: https://github.com/Aider-AI/aider ·
  https://aider.chat/docs/usage/modes.html · https://aider.chat/docs/scripting.html
- ACP: https://agentclientprotocol.com · https://zed.dev/docs/ai/external-agents ·
  https://github.com/agentclientprotocol/agent-client-protocol
- A2A: https://a2a-protocol.org/latest/ ·
  https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents
- Sandboxing: https://code.claude.com/docs/en/sandboxing ·
  https://github.com/openai/codex/blob/main/codex-rs/linux-sandbox/README.md
- A2A critiques: arXiv 2505.03864, 2505.12490
