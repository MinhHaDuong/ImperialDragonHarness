---
name: feedback-build-prompt-d-variant
description: "build_kieu_prompt collapsed D1/D2 into D; smoke_sota_or.py default variante=\"D2\" is now broken"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 207f5efc-4fd9-4bf1-b8ef-21487b529294
---

`build_kieu_prompt.build_prompt()` accepts only `A`, `C`, `D` (cf. `VALID_VARIANTES`) and **always** includes cultural notes when `cultural_path` is provided. The historical `A1/A2/C1/C2/D1/D2` matrix (suffix `1` = no notes, `2` = with notes) was collapsed in commits `666c4ce` and `1b15aca`.

Side effects:
- `scripts/smoke_sota_or.py` `main()` defaults to `variante="D2"` and passes `kieu_vi_path=`, `michels_path=`, `hst_path=` — all three were removed from `build_prompt()`'s signature. The CLI errors on `KeyError: 'D2'`. The five helpers we import from it (`OR_BASE_URL`, `call_model`, `detect_refusal`, `load_or_key`, `MODEL_OVERRIDES`) remain correct.

**Why:** ticket 0237 inherited the `D2` default + cultural-conditional logic from the smoke script; both had to be replaced with `D` and unconditional cultural notes.

**How to apply:** when building scripts that consume `build_prompt()`, use `variante="D"` and pass `cultural_path=args.cultural` unconditionally. If a script in `scripts/` still references `D2`, `michels_path`, `hst_path`, or `kieu_vi_path` kwargs, it's pre-refactor dead code — fix in-place or note in PR.

Related: [[project_pilot_v1-8_findings]] (D-prompt empirical behaviour), [[feedback_d_token_budget]].
