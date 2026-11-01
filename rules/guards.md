<!-- last-reviewed: 2026-10-05 -->
<!-- Module: the floor. Hard limits every agent role obeys, whatever runtime or profile; nothing in the other rules or in a skill overrides them. Bare profiles load this file alone, so it states its rules in full. Loading: rules/README.md § Loading per runtime. -->
# Guards

- **Never display credentials.** Never display API keys, tokens, passwords, or any credentials in chat text — not even partially, not even in  "here's what I found" summaries.
- **Use tickets for inter-project communication.** The only place to write into the harness or another project is its `tickets/` directory. Use it to report incidents, ask for features, or report your work done to a tracker.
- **A run that starts compacting should split, not grind.** When a worker reach more than 230K tokens of context, consider the task too large. Ask to split the work. Never answer a context wall with a bigger window, KV tricks or compaction. 
