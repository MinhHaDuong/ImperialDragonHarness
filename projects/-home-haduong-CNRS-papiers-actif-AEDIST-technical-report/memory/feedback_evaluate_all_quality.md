---
name: evaluate-all record quality
description: runner evaluate-all produces lower-quality RunRecords than migrate_to_measurements — watch for absolute paths and missing metadata
type: feedback
---

runner.py evaluate-all and migrate_to_measurements.py both write to measurements.jsonl but produce different record quality. evaluate-all stored absolute paths in result_file and -runN in model names until fixed in PR #182.

**Why:** The two code paths evolved independently. evaluate-all was a batch evaluator; migrate was a schema migration tool with richer context.

**How to apply:** After any evaluate-all run, spot-check a record for relative paths and clean model names. If adding a new measurements writer, match the schema quality of existing records.
