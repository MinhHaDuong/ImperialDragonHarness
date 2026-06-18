#!/usr/bin/env bash
# Harness shell init — source this from ~/.bashrc or ~/.zshrc.
# Wraps the claude CLI to: skip permission prompts, name the session after the project.

claude() {
  local name top
  top=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null)
  name=$(basename "${top:-$PWD}")
  command claude --dangerously-skip-permissions --name "$name" "$@"
}
