Claude Code’s Source Got Leaked. Here’s What’s Actually Worth Learning.

Pawel Jozefiak

Apr 01, 2026

https://thoughts.jock.pl/p/claude-code-source-leak-what-to-learn-ai-agents-2026

uilt, and pulling out anything useful.

Here’s what matters if you’re building AI agents or want to understand where this technology is actually going.
The three-layer memory system

This is probably the most important architectural discovery in the leak. Claude Code uses a memory system with three layers:

    Core index (MEMORY.md): A lightweight file of pointers, always loaded into context. Each entry is under 150 characters. It’s an index, not the memory itself.

    Topic files: Detailed knowledge distributed across separate files, fetched on-demand when the index suggests they’re relevant.

    Raw transcripts: Never re-read in full. Only grep’d for specific identifiers when needed.

The key insight is what they call “skeptical memory.” The agent treats its own memory as a hint, not a fact. Before acting on something it remembers, it verifies against the actual codebase. Memory says a function exists? Check first. Memory says a file is at this path? Verify before using it.

This solves context entropy, the gradual degradation of agent performance in long-running sessions. Most agents get worse the longer they run because their context fills up with stale observations. This architecture keeps the active context small (just the index) and only loads what’s needed.

I’ve been running a similar pattern with working memory that rolls over on a schedule and a permanent index that persists across sessions. The leak confirmed this is the right approach. The verification step is something I’m now adding to my own system.
Memory consolidation during idle time (autoDream)

The leak includes a system called autoDream in the services/autoDream/ directory. It’s a background memory consolidation engine that runs as a forked subagent with read-only access to the project. Three gates must pass before it runs: 24 hours since the last run, at least 5 sessions completed, and a consolidation lock must be available.

When triggered, it runs four phases: orient (scan memory directory), gather (extract new info from logs), consolidate (write and update topic files), and prune (keep total memory under 200 lines and 25KB).

Why this matters for you: if you’re building any agent that runs over multiple sessions, unbounded memory will kill you. Not immediately. Over weeks. Your agent starts referencing things that are no longer true, duplicating observations, and filling context with noise. You need some form of consolidation. autoDream’s approach of forking a read-only subagent is clean because it can’t accidentally corrupt whatever the agent is currently working on.
The tool architecture

Claude Code defines 40+ discrete tools, each wrapped in permission gates. The biggest file in the leak is Tool.ts at roughly 29,000 lines, defining tool types and permission schemas. Every tool operation goes through a PermissionGate structure for granular access control.

Three things stood out:

    File-read deduplication: Before re-reading a file, it checks whether the file has changed since the last read. If not, it skips the read and uses the cached version. Sounds obvious, but most agent setups don’t do this, and the token savings compound fast.

    Large result offloading: When a tool produces a massive result (like searching a large codebase), it writes the full result to disk and only passes a preview plus a file reference back to the context. This keeps the context window clean while still making the data available.

    CLAUDE.md reinsertion on turn changes: The CLAUDE.md file doesn’t just get loaded once at the start. It gets reinserted into the conversation on every turn change (when the model finishes and the user sends a new message). Not at the top of the history, but right where the new message is sent. This repeated injection keeps the model aligned with your instructions even in long conversations where the original system prompt would have scrolled far out of active context.

If you’re using CLAUDE.md files (and you should be), this last detail matters. Your instructions aren’t a one-time primer. They’re actively re-read throughout the conversation. That’s why well-structured CLAUDE.md files have such a big impact on agent behavior. I wrote about how I structure mine after running 1000+ sessions.
Multi-agent coordination

The leak reveals Coordinator Mode. One Claude agent acts as a lead, spawning and managing multiple worker agents in parallel. Workers operate in their own isolated contexts with restricted tool permissions. They communicate via XML-structured task notifications and share data through a scratchpad directory. The system prompt for coordinators emphasizes “parallelism is your superpower.”

The clever implementation detail here: sub-agents share the prompt cache. Instead of each worker spinning up with its own context (paying full input token costs), they all share the same context prefix and only branch at the task-specific instruction. This is what makes multi-agent coordination economically viable. Without cache sharing, spinning up five workers means paying five times the input cost. With it, you pay once for the shared context and only pay incrementally for the task-specific parts. That’s probably why Coordinator Mode isn’t released yet. The cost math is still brutal even with this optimization.

This is the same pattern I landed on independently. I built three persistent domain teams with an Opus lead that plans and delegates, and Sonnet specialists that execute. The convergence here is specific: lead agent that plans, specialist workers that execute in parallel, structured communication, verification at the end.
Risk classification

Actions get labeled LOW, MEDIUM, or HIGH risk. There’s a “YOLO classifier” for fast auto-approval of low-risk operations. Protected files like .gitconfig and .bashrc get special treatment. There’s also a referenced “AFK Mode” that adjusts behavior when the user is away.

Three tiers. Same as what I built. Same reasoning: an autonomous agent needs to know which actions are safe to take alone, which should be flagged, and which need a human in the loop. This one is less a revelation and more a confirmation that the three-tier approach is just the correct default for any agent with real-world access.
Five patterns you can use right now

Here’s the practical part. These are patterns from the leak that you can apply to your own AI agent setup, whether you’re building something complex or just trying to get more out of Claude Code, Cursor, or any AI coding tool.
1. The blocking budget

KAIROS (the unreleased always-on daemon in the leak) has a 15-second blocking budget. Any proactive action that would take longer gets deferred. Max 2 proactive messages per window. Reactive messages (responding to user input) bypass the budget entirely.

Why this matters: if you’re running any kind of proactive agent, whether it’s monitoring code, sending notifications, or checking on things, you need rate limiting. Not just “don’t spam.” Structured rate limiting with different rules for proactive versus reactive work. Without it, your agent will eventually send 4 messages in 30 seconds when one would do.

I implemented this the night I read the leak. A simple state file tracks the budget window. Proactive messages get queued and recovered. Reactive messages go through immediately. About 50 lines of Python.
2. Skeptical memory with verification

Don’t trust your agent’s memory. Make it verify. Every time your agent says “I remember that file X has function Y,” make it check first. Memory is a hint. The codebase is the truth.

This is the single most practical takeaway from the leak. If you’re using CLAUDE.md files, custom system prompts, or any form of persistent context, treat them as suggestions that need verification, not as ground truth. Files get renamed. Functions get deleted. APIs change. Your memory hasn’t.
3. Semantic memory merging

autoDream doesn’t just delete old memories. It merges related observations, removes logical contradictions, and converts vague insights into concrete facts. If your agent noted “user might prefer X” three months ago and “user confirmed X yesterday,” the old entry should be updated, not kept alongside the new one.

Most memory systems I’ve seen (including my own before this) do time-based cleanup. Old stuff gets archived or deleted. That’s fine for preventing memory bloat, but it doesn’t catch contradictions. Two conflicting observations can coexist for months. Semantic merging resolves that.

I built a version using a local LLM (Qwen 9B running on the Mac Mini) to cluster related entries and merge them during nightly maintenance. A safety cap prevents reducing any section by more than 50% in a single pass. You don’t need to go this far. Even a simple script that groups memory entries by topic and flags potential contradictions would be a step up from pure time-based cleanup.
4. Adversarial verification

The leaked Coordinator Mode treats verification as a distinct, adversarial phase with its own worker agent. Not “check if this works.” Not a checklist. A separate agent whose job is to try to break what was built.

This is different from testing. Testing asks “does it work?” Adversarial verification asks “how can I break it?” The distinction matters because the agent that built something has a blind spot about its own work. A fresh agent with the explicit prompt “find problems with this” will catch things the builder missed.

I added this to my nightshift process. Before any task gets marked complete, a separate verification agent runs two phases: existence check (does the deliverable actually exist?) and adversarial challenge (try to break it). The results go into a verification log. It’s caught real issues that would have shipped otherwise.
5. Prompt cache awareness

The source includes a promptCacheBreakDetection.ts file that monitors 14 different cache-break vectors with sticky latches. Things like mode toggles, model changes, context modifications. Each one can invalidate your prompt cache, and cache misses mean you’re paying full price for tokens that could have been cached.

If you’re running many agent sessions per day, cache efficiency directly affects your costs. This one is easy to ignore because you don’t see the waste. But if you track it (which I now do), you’ll likely find that your cache hit rate is lower than you assumed and that specific patterns in your workflow are breaking it.

Related: the source reveals five different compaction strategies for when the context window fills up. If you’ve used Claude Code heavily, you’ve probably hit the moment where it compacts and then loses track of what it was doing. That’s still a hard problem. But knowing they’re actively working on multiple approaches to solve it tells you this is worth investing in for your own long-running agents too.
What I built in one night

Like this? Subscribe for more! I am “do-guy” first, write later.

I didn’t just read the leak. I treated it as a learning exercise and built things from it. That same night, I implemented five modules inspired by patterns in the leaked source:

    Blocking budget for proactive messages. 15-second window, 2-message max, deferred queue.

    Semantic memory consolidation using local LLM to cluster and merge observations during idle time.

    Frustration detection via regex pattern matching. 21 patterns, three action tiers (back off, acknowledge, simplify). Fast enough to run on every incoming message.

    Prompt cache monitor that tracks hit rates, estimates savings, and alerts when efficiency drops.

    Adversarial verification as a formal phase in the nightshift execution loop.

Total time: about 4 hours of reading and building. I already had the foundations (nightshift, memory system, domain teams). These were specific improvements layered on top.

The frustration detection one is worth a note. The leaked code uses regex patterns to detect user frustration. Stuff like “wtf”, “this sucks”, keyword matching. An LLM company using regexes for sentiment analysis. But it makes sense. You don’t burn an LLM inference call on something you can pattern-match in 5 milliseconds. I applied the same logic: 21 patterns, fast evaluation, action suggestions without the overhead of an API call.
What’s not worth your time

Not everything in the leak is useful. Some of it is Anthropic-specific, some is unreleased for good reasons, and some is just fun but not practical.

Buddy System. A Tamagotchi-style terminal pet. 18 species across rarity tiers, procedural stats like DEBUGGING, PATIENCE, CHAOS. It’s genuinely charming and I kind of love it. But unless you’re Anthropic trying to make a CLI tool feel more personal, you don’t need this.

Undercover Mode. Strips Anthropic attribution from open-source contributions. Specific to their internal workflow where employees use Claude Code on public repos. Not applicable unless you have the same problem (and if you do, you probably already know about it).

Anti-distillation mechanisms. The code injects fake tool definitions into API requests to poison anyone trying to train models on intercepted traffic. It also summarizes reasoning chains before returning them to eavesdroppers. Interesting from a security perspective. Not useful for building agents.

ULTRAPLAN. A mode that offloads complex planning to a remote cloud container running Opus 4.6 for up to 30 minutes. Cool concept. Requires infrastructure you probably don’t have and a use case that doesn’t come up often enough to justify building it.

Native client attestation. API requests include computed hashes that prove they come from legitimate Claude Code binaries. Implemented below the JavaScript runtime in Bun’s native HTTP stack (written in Zig). This is DRM for API calls. Interesting engineering but not something you can or should replicate.
