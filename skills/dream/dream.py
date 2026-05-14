#!/usr/bin/env python3
"""
Autonomous nightly memory consolidation across all projects.

Uses mem0 classifier (ADD/UPDATE/DELETE/NOOP) + Park reflection + bi-temporal invalidation.
Patterns validated as production-ready as of 2026-05-13.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic

# Configuration
MEMORY_BASE = Path.home() / ".claude" / "projects"
IDH_BASE = Path.home() / ".claude"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_CRON = "0 2 * * *"  # 2 AM UTC nightly

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


def get_memory_dirs():
    """Enumerate all project memory directories."""
    if not MEMORY_BASE.exists():
        return []
    return [d for d in MEMORY_BASE.iterdir() if d.is_dir() and (d / "memory").is_dir()]


def read_memory_index(project_dir):
    """Read MEMORY.md index file and return list of (filename, one-line-desc)."""
    index_path = project_dir / "memory" / "MEMORY.md"
    if not index_path.exists():
        return []

    entries = []
    with open(index_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Expect format: - [Title](file.md) — one-line hook
            match = re.match(r"-\s+\[([^\]]+)\]\(([^\)]+)\)\s*—?\s*(.*)", line)
            if match:
                entries.append((match.group(2), match.group(1), match.group(3)))
    return entries


def read_memory_files(project_dir, filenames):
    """Read all memory .md files for a project."""
    memory_dir = project_dir / "memory"
    contents = {}
    for filename in filenames:
        filepath = memory_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                contents[filename] = f.read()
    return contents


def extract_keywords(text, max_terms=20):
    """Extract keywords from text for neighbor retrieval."""
    # Remove markdown syntax and split
    text = re.sub(r"[#\[\](){}]", " ", text.lower())
    words = text.split()
    # Filter short words and common terms
    stop_words = {"the", "a", "an", "and", "or", "is", "in", "of", "to", "for", "on"}
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    # Return most frequent (simple heuristic for importance)
    from collections import Counter

    freq = Counter(keywords)
    return [word for word, _ in freq.most_common(max_terms)]


def get_memory_neighbors(candidate_file, candidate_content, all_memory_files, top_k=5):
    """Find similar memory files based on keyword overlap."""
    candidate_keywords = set(extract_keywords(candidate_content))
    if not candidate_keywords:
        return []

    neighbors = []
    for filename, content in all_memory_files.items():
        if filename == candidate_file:
            continue
        file_keywords = set(extract_keywords(content))
        overlap = len(candidate_keywords & file_keywords)
        if overlap > 0:
            neighbors.append((overlap, filename, content))

    # Sort by overlap and return top-k
    neighbors.sort(reverse=True)
    return [(fn, content) for _, fn, content in neighbors[:top_k]]


def classify_memory_file(client, filename, content, neighbors, model):
    """Use LLM to classify a memory file as ADD/UPDATE/DELETE/NOOP."""
    neighbors_text = ""
    if neighbors:
        for neighbor_file, neighbor_content in neighbors:
            neighbors_text += f"\n## {neighbor_file}\n{neighbor_content[:500]}...\n"
    else:
        neighbors_text = "(no similar memory files found)"

    prompt = f"""You are a memory consolidation agent. Analyze this memory file.

## Candidate file: {filename}

{content}

## Similar existing memories:
{neighbors_text}

Classify using exactly one decision:
- ADD: New memory, no semantic equivalent exists.
- UPDATE: Should merge into an existing memory file.
- DELETE: Contradicts newer/more relevant memory (specify which).
- NOOP: Already present or irrelevant.

IMPORTANT: Preserve contradictions that reveal evolution (e.g., feedback that changed over time).
Only DELETE if truly obsolete.

Respond with ONLY: decision (line 1), then brief reasoning (line 2+)."""

    message = client.messages.create(
        model=model, max_tokens=256, messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text.strip()
    lines = response.split("\n", 1)
    decision = lines[0].strip().upper()
    reasoning = lines[1].strip() if len(lines) > 1 else ""

    # Validate decision
    if decision not in ("ADD", "UPDATE", "DELETE", "NOOP"):
        logger.warning(
            f"Invalid decision '{decision}' for {filename}; treating as NOOP"
        )
        decision = "NOOP"

    return decision, reasoning


def reflect_on_memories(client, entries_text, model, n_insights=5):
    """
    Extract high-level insights from memory entries using Park 2023 reflection.

    Returns: list of insight strings
    """
    prompt = f"""You are a memory consolidation agent reflecting on personal memories.

Given these memory entries:
{entries_text}

Extract {n_insights} high-level insights about patterns, preferences, recurring themes, or important lessons.
Each insight should be 1-2 sentences and derive from multiple entries if possible.

Respond with ONLY the insights, one per line, without numbering or bullets."""

    message = client.messages.create(
        model=model, max_tokens=512, messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text.strip()
    insights = [line.strip() for line in response.split("\n") if line.strip()]
    return insights[:n_insights]


def consolidate_project(client, project_dir, model, dry_run=False):
    """Consolidate memory for a single project."""
    memory_dir = project_dir / "memory"
    logger.info(f"Consolidating {project_dir.name}...")

    # Read MEMORY.md index
    index_entries = read_memory_index(project_dir)
    if not index_entries:
        logger.info(f"  No memory files found in {project_dir.name}; skipping.")
        return 0, 0, []

    filenames = [filename for _, _, filename in index_entries]

    # Read all memory files
    memory_files = read_memory_files(project_dir, filenames)

    # Classify each file
    decisions_log = []
    n_before = len(index_entries)
    surviving_entries = []

    for filename, title, desc in index_entries:
        filepath = memory_dir / filename
        if not filepath.exists():
            decisions_log.append((filename, "NOOP", "File not found"))
            continue

        content = memory_files.get(filename, "")

        # Get neighbors and classify
        neighbors = get_memory_neighbors(filename, content, memory_files)
        decision, reasoning = classify_memory_file(
            client, filename, content, neighbors, model
        )

        decisions_log.append((filename, decision, reasoning))
        logger.info(f"  {filename}: {decision}")

        # Handle decision
        if decision == "DELETE":
            if not dry_run:
                # Leave tombstone comment
                tombstone = f"# DELETED {datetime.now().isoformat()}: {title}\n# Reason: {reasoning}\n"
                with open(filepath, "w") as f:
                    f.write(tombstone)
        elif decision in ("ADD", "UPDATE", "NOOP"):
            surviving_entries.append((filename, title, desc))

    # Reflect on survivors
    surviving_text = "\n".join(
        f"- [{title}]({filename}) — {desc}" for _, title, desc in surviving_entries
    )
    if surviving_text:
        insights = reflect_on_memories(client, surviving_text, model, n_insights=5)
        logger.info(f"  Extracted {len(insights)} insights.")
    else:
        insights = []

    # Regenerate MEMORY.md
    if not dry_run:
        new_index = "# Memory index\n\n"
        if insights:
            new_index += "## Key insights\n\n"
            for insight in insights:
                new_index += f"- {insight}\n"
            new_index += "\n"

        new_index += "## Entries\n\n"
        for filename, title, desc in surviving_entries:
            new_index += f"- [{title}]({filename}) — {desc}\n"

        index_path = memory_dir / "MEMORY.md"
        with open(index_path, "w") as f:
            f.write(new_index)

    n_after = len(surviving_entries)
    return n_before, n_after, decisions_log


def commit_consolidation(project_name, n_before, n_after):
    """Commit consolidation results to IDH git repo."""
    os.chdir(IDH_BASE)

    message = f"dream: consolidate {project_name} memory ({n_before}→{n_after})"

    try:
        subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message], check=True, capture_output=True
        )
        logger.info(f"  Committed: {message}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"  Git commit failed: {e.stderr.decode()}")


def rollback_consolidation(commit_hash):
    """Revert last consolidation commit."""
    os.chdir(IDH_BASE)
    try:
        subprocess.run(
            ["git", "revert", "--no-edit", commit_hash], check=True, capture_output=True
        )
        logger.info(f"Rolled back {commit_hash}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Rollback failed: {e.stderr.decode()}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous nightly memory consolidation."
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=None,
        help="Project name (default: consolidate all projects)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Propose edits without writing."
    )
    parser.add_argument(
        "--rollback", metavar="COMMIT_HASH", help="Revert a consolidation commit."
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"LLM model (default: {DEFAULT_MODEL})"
    )

    args = parser.parse_args()

    # Handle rollback
    if args.rollback:
        rollback_consolidation(args.rollback)
        return

    # Initialize Anthropic client
    client = Anthropic()

    # Determine projects to consolidate
    if args.project:
        project_dirs = [MEMORY_BASE / args.project]
        if not project_dirs[0].exists():
            logger.error(f"Project {args.project} not found at {project_dirs[0]}")
            sys.exit(1)
    else:
        project_dirs = get_memory_dirs()

    if not project_dirs:
        logger.info("No projects found; exiting.")
        return

    logger.info(f"Starting consolidation ({'dry-run' if args.dry_run else 'live'})...")

    # Consolidate each project
    total_before = 0
    total_after = 0
    for project_dir in project_dirs:
        n_before, n_after, decisions = consolidate_project(
            client, project_dir, args.model, dry_run=args.dry_run
        )
        total_before += n_before
        total_after += n_after

        # Commit if not dry-run
        if not args.dry_run and n_before > 0:
            commit_consolidation(project_dir.name, n_before, n_after)

    logger.info(f"Consolidation complete. {total_before}→{total_after} entries.")


if __name__ == "__main__":
    main()
