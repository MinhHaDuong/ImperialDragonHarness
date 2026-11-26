# Raid 9b9a7a runtime evidence

The Codex collaboration launcher accepted requested model and effort parameters,
but returned only task identifiers; worker messages did not expose a verified
provider model identifier. These worker identities are runtime-masked for
attribution. Requested routing is not observed identity.

- Planner: `/root/plan`, requested `gpt-6.1-sol`, medium, OpenAI.
- Blind-Spot: `/root/blind_spot`, requested `gpt-6.1-sol`, medium, OpenAI.
- Feasibility: `/root/feasibility`, requested `gpt-6-luna`, medium, OpenAI.
- Templates coder: `/root/templates`, requested `gpt-6.1-sol`, medium, OpenAI.
- Loader coder: `/root/loader`, requested `gpt-6.1-sol`, low, OpenAI.

The loader experiment is separately observed: Claude session
`7f156d2a-d818-4d3a-9533-db5755ea240b` returned `modelUsage` key
`claude-haiku-5-5`. Its transcript records a `Skill` invocation with
`{"skill":"replicate","args":"assess"}` and a successful tool result.
The experiment stopped after loading instructions and did not run assessment.

The interface session reports Codex based on GPT-6 without a verbatim provider
model identifier. Its runtime is `codex`, session
`01a2169f-577c-78b2-8655-a00002a2c6aa`; model attribution remains masked.

- Wave 1 integration: `/root/integration_wave1`, requested `gpt-6.1-sol`, medium, OpenAI; observed model unavailable.

- Scope coder: `/root/scope_1561`, requested `gpt-6.1-sol`, medium, OpenAI; observed exact identity unavailable.

PR2519's generated gaze header names its requested `openai/gpt-6-luna`,
but the answer explicitly states that the subagent runtime identity was not
independently exposed. The factual memory capture therefore masks that seat's
identity and retains its role, route, outcome, finding, and this evidence;
the original generated header remains on review notes unchanged.
- Wave 2 integration: `/root/integration_scope`, requested `gpt-6.1-sol`, medium, OpenAI; observed model unavailable.

PR2521's gaze likewise reports its correctness worker's model and family as
unavailable despite a generated requested-model header. Its factual capture
uses the same masking policy and leaves raw review notes unchanged.
- Boundary coder: `/root/boundaries_1562`, requested `gpt-6.1-sol`, medium, OpenAI; exact runtime identity not yet exposed.
- Wave 3 integration: `/root/integration_boundaries`, requested `gpt-6.1-sol`, medium, OpenAI; observed model unavailable.
- Access coder: `/root/access_1563`, requested `gpt-6.1-sol`, medium, OpenAI; exact identity not exposed at launch.

PR2522's generated gaze lines name the requested `openai/gpt-6.1-sol`.
The worker reports that its actual runtime identity was unavailable. Its
capture masks that identity while retaining all review attempts, including
the aborted setup's failed status. Raw notes are unchanged.
