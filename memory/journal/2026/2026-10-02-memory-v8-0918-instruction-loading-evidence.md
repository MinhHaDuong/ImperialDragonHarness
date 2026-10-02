# Instruction-loading evidence available in the acceptance session

Context: Step 6 of ticket 0918's acceptance trial asked whether the runtime natively loaded repository project-instruction files without being asked.

Observation: The visible session supplied AGENTS.md instructions in a user message labeled for this clone. The agent then explicitly read memory/MEMORY.md, its git-worktree topic, docs/memory-v8/README.md, RTK.md, and the linked git-worktree reference using exec_command. No independent native loading of AGENTS.md, CLAUDE.md, or another repository instruction file was evidenced in the visible session.

Consequence: This trial cannot attest native instruction-file loading from its session evidence; the user-supplied instructions establish a separate visible delivery route. This does not establish that hidden runtime loading did not occur.

Evidence: The initial user message and the explicit read tool calls in this session. docs/memory-v8/README.md asks adopters to verify each runtime's loading rather than claim automatic injection. This entry records a material evidentiary limitation of that acceptance check, without assigning a cause.
