"""The perch multi-harness pilot (ticket 0802).

One canonical skill body, three harnesses. The first attempt (PR #780, closed
unmerged) failed on three things that are each a test here rather than a
sentence in a README:

1. it *declared* ``~/.agents`` as the provider-neutral skills home and no code
   path created it, so the two harnesses the pilot exists to reach had nothing
   to find;
2. its version gate was an exact-match allowlist, which went stale twice in
   nine days and refused the CLIs actually installed;
3. its projection target was ``~/.claude/skills/perch``, which in this
   installation *is* the canonical skill directory — install refused its own
   source as an unmanaged entry.

So: the installer creates the neutral home, the version gate is a floor plus a
probe, and a target that already resolves to the canonical source is success,
not a collision. Discovery itself is proved against the real CLIs in
``tests/test_perch_discovery.py`` (integration tier); this module is the
static contract and runs everywhere.
"""

import importlib.util
import json
import os
from pathlib import Path

import jsonschema
import pytest

REPO = Path(__file__).resolve().parent.parent
ADAPTERS = REPO / "adapters"
CANONICAL = REPO / "skills" / "perch" / "SKILL.md"
SCHEMA = ADAPTERS / "pilot-support.schema.json"
INVENTORY = ADAPTERS / "pilot-support.json"


def _module():
    spec = importlib.util.spec_from_file_location("perch_pilot", ADAPTERS / "perch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


perch = _module()


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A clean profile: no ~/.agents, no ~/.claude."""
    root = tmp_path / "home"
    root.mkdir()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.delenv("USERPROFILE", raising=False)
    return root


# --- the canonical body -------------------------------------------------


def test_the_canonical_body_is_the_only_workflow_text():
    """No second copy of the prose anywhere under adapters/."""
    body = CANONICAL.read_text(encoding="utf-8")
    marker = "Mid-session orientation"
    assert marker in body
    for path in sorted(ADAPTERS.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert "## Output shape" not in text, f"{path} carries a second workflow body"


def test_the_canonical_frontmatter_carries_what_all_three_harnesses_require():
    """``name`` and ``description`` are the whole shared core (action 7).

    Claude Code, Codex and Pi each require exactly these two fields. That is
    the only duplication this slice observed, it is already in the canonical
    frontmatter, and so the pilot adds no core identifier of its own.
    """
    fields = perch.frontmatter(CANONICAL)
    assert fields["name"] == "perch"
    assert fields["description"].strip()
    assert perch.SHARED_REQUIRED_FIELDS == ("name", "description")
    for field in perch.SHARED_REQUIRED_FIELDS:
        assert field in fields


def test_the_output_headings_are_stable_and_the_workflow_is_read_only():
    body = CANONICAL.read_text(encoding="utf-8")
    for heading in ("## Done", "## Open", "## Drift", "**Stance:**"):
        assert heading in body
    assert "Read-only report" in body


# --- version policy: a floor plus a probe, never an allowlist -----------


def test_the_policy_is_a_floor_not_an_allowlist():
    """PR #780's ``supported_versions`` list is the defect; it must be gone."""
    for policy in perch.inventory()["versions"]:
        assert "supported_versions" not in policy
        assert perch.parse_version(policy["minimum_version"])


@pytest.mark.parametrize("harness", perch.HARNESSES)
def test_the_declared_minimum_is_supported(harness):
    floor = perch.policy(harness)["minimum_version"]
    assert perch.check_version(harness, supplied=floor) == floor


@pytest.mark.parametrize("harness", perch.HARNESSES)
def test_the_version_probed_on_this_pilot_is_supported(harness):
    """The current release recorded in the inventory must still pass the gate.

    This is the test that PR #780's allowlist could not survive: an upstream
    release must widen support, never revoke it.
    """
    probed = perch.policy(harness)["probed_version"]
    assert perch.check_version(harness, supplied=probed) == probed


@pytest.mark.parametrize("harness", perch.HARNESSES)
def test_a_release_above_the_floor_is_supported(harness):
    major, minor, patch = perch.parse_version(perch.policy(harness)["minimum_version"])
    future = f"{major}.{minor + 5}.{patch}"
    assert perch.check_version(harness, supplied=future) == future


@pytest.mark.parametrize("harness", perch.HARNESSES)
def test_below_the_floor_refuses(harness):
    major, minor, patch = perch.parse_version(perch.policy(harness)["minimum_version"])
    if minor:
        older = f"{major}.{minor - 1}.{patch}"
    elif patch:
        older = f"{major}.{minor}.{patch - 1}"
    else:
        older = f"{max(major - 1, 0)}.99.99"
    assert perch.parse_version(older) < (major, minor, patch), older
    with pytest.raises(perch.Refusal):
        perch.check_version(harness, supplied=older)


def test_a_pre_release_compares_equal_to_its_release():
    """A decision, pinned so it stays one: identifiers are ignored."""
    assert perch.parse_version("0.85.1-rc.1") == perch.parse_version("0.85.1")
    assert perch.parse_version("0.85.1+build.99") == perch.parse_version("0.85.1")


@pytest.mark.parametrize("harness", perch.HARNESSES)
def test_an_unreadable_version_refuses_rather_than_passing(harness):
    """Do not silently accept an unknown version (ticket action 1)."""
    with pytest.raises(perch.Refusal):
        perch.check_version(harness, supplied="not a version at all")


@pytest.mark.integration  # reaches subprocess.run one frame deep, in check_version
def test_a_missing_cli_refuses_rather_than_passing(monkeypatch):
    monkeypatch.setenv("PERCH_CODEX_BIN", "/nonexistent/codex")
    with pytest.raises(perch.Refusal):
        perch.check_version("codex")


# --- the neutral home is built, not asserted ----------------------------


def test_a_clean_profile_does_not_discover_perch(home):
    assert not (home / ".agents").exists()
    assert perch.status("codex")["installed"] is False
    assert perch.status("pi")["installed"] is False


@pytest.mark.parametrize("harness", ("codex", "pi"))
def test_install_creates_the_neutral_home(home, harness):
    perch.install(harness, version="99.0.0")
    target = home / ".agents" / "skills" / "perch"
    assert target.is_symlink()
    assert target.resolve() == (REPO / "skills" / "perch").resolve()
    assert (target / "SKILL.md").read_text(encoding="utf-8") == CANONICAL.read_text(
        encoding="utf-8"
    )
    assert perch.status(harness)["installed"] is True


def test_a_blocked_neutral_home_refuses_instead_of_raising_a_traceback(home):
    """Making the target's parent is an OS call, so it belongs to the contract.

    ``main()`` shows a ``Refusal`` as one line and exits 2; everything else
    leaves the module as a traceback at exit 1. A plain file where the neutral
    home should go is the cheapest way to make ``mkdir`` fail, and it fails
    with ``NotADirectoryError`` — neither a ``Refusal`` nor anything
    ``main()`` catches.
    """
    (home / ".agents").write_text("not a directory\n", encoding="utf-8")
    with pytest.raises(perch.Refusal) as caught:
        perch.install("codex", version="99.0.0")
    assert ".agents" in str(caught.value)
    assert perch.main(["install", "codex", "--version", "99.0.0"]) == 2


def test_codex_and_pi_share_one_target_and_install_is_idempotent(home):
    perch.install("codex", version="99.0.0")
    perch.install("pi", version="99.0.0")
    assert perch.status("codex")["target"] == perch.status("pi")["target"]
    assert (home / ".agents" / "skills" / "perch").is_symlink()


def test_uninstall_restores_the_exact_pre_experiment_state(home):
    before = sorted(p.name for p in home.iterdir())
    perch.install("codex", version="99.0.0")
    perch.uninstall("codex")
    assert sorted(p.name for p in home.iterdir()) == before
    assert not (home / ".agents").exists()


def test_uninstall_keeps_a_neutral_home_that_holds_someone_elses_skill(home):
    other = home / ".agents" / "skills" / "unrelated"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("---\nname: unrelated\n---\n", encoding="utf-8")
    perch.install("pi", version="99.0.0")
    perch.uninstall("pi")
    assert other.is_dir()
    assert not (home / ".agents" / "skills" / "perch").exists()


def test_uninstall_names_every_harness_it_reaches(home):
    """One neutral home, one perch: removing it for Codex removes it for Pi."""
    assert perch.sharing_target("codex") == ("codex", "pi")
    assert perch.sharing_target("claude") == ("claude",)
    perch.install("codex", version="99.0.0")
    message = perch.uninstall("pi")
    assert "codex, pi" in message
    assert perch.status("codex")["installed"] is False


def test_uninstall_never_prunes_above_the_neutral_home(home):
    """$HOME/.claude is Claude Code's own directory, not the pilot's to remove."""
    assert perch.prune_root("codex") == home / ".agents"
    assert perch.prune_root("claude") == home / ".claude" / "skills"
    perch.install("claude", version="99.0.0")
    perch.uninstall("claude")
    assert (home / ".claude").is_dir()
    assert not (home / ".claude" / "skills").exists()


def test_a_link_left_dangling_by_a_moved_checkout_is_named_and_removable(home):
    """Fail-safe is not enough when the safe state cannot be cleaned up."""
    target = home / ".agents" / "skills" / "perch"
    target.parent.mkdir(parents=True)
    target.symlink_to(home / "gone" / "skills" / "perch", target_is_directory=True)
    assert perch.status("codex")["projection"] == "dangling"
    with pytest.raises(perch.Refusal, match="uninstall"):
        perch.install("codex", version="99.0.0")
    assert "no longer exists" in perch.uninstall("codex")
    assert not (home / ".agents").exists()


def test_a_dangling_link_named_perch_but_shaped_wrong_is_left_alone(home):
    """A bare basename match would adopt any dangling link called perch."""
    target = home / ".agents" / "skills" / "perch"
    target.parent.mkdir(parents=True)
    target.symlink_to(home / "gone" / "elsewhere" / "perch", target_is_directory=True)
    assert perch.status("codex")["projection"] == "unmanaged"
    with pytest.raises(perch.Refusal):
        perch.uninstall("codex")


def test_pruning_refuses_to_walk_through_a_symlinked_neutral_home(home, tmp_path):
    """Otherwise the walk rmdirs its way out of $HOME entirely."""
    outside = tmp_path / "outside"
    (outside / "skills").mkdir(parents=True)
    (home / ".agents").symlink_to(outside, target_is_directory=True)
    perch.install("codex", version="99.0.0")
    perch.uninstall("codex")
    assert outside.is_dir()
    assert (outside / "skills").is_dir()
    assert not (outside / "skills" / "perch").exists()


def test_uninstalling_a_link_that_vanished_mid_call_is_not_a_traceback(home):
    perch.install("codex", version="99.0.0")
    target = home / ".agents" / "skills" / "perch"
    target.unlink()
    assert "not installed" in perch.uninstall("codex")


def test_no_surface_still_claims_uninstall_gives_back_only_what_it_created():
    """The round-2 contradiction: the README was fixed, three copies were not."""
    stale = "exactly the directories"
    for path in (
        ADAPTERS / "perch.py",
        ADAPTERS / "README.md",
        INVENTORY,
    ):
        assert stale not in path.read_text(encoding="utf-8"), path


def test_a_dangling_link_that_is_not_ours_is_left_alone(home):
    target = home / ".agents" / "skills" / "perch"
    target.parent.mkdir(parents=True)
    target.symlink_to(home / "gone" / "something-else", target_is_directory=True)
    assert perch.status("codex")["projection"] == "unmanaged"
    with pytest.raises(perch.Refusal):
        perch.uninstall("codex")


def test_install_refuses_to_replace_an_unmanaged_entry(home):
    target = home / ".agents" / "skills" / "perch"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("someone else's perch\n", encoding="utf-8")
    with pytest.raises(perch.Refusal):
        perch.install("codex", version="99.0.0")
    assert (target / "SKILL.md").read_text(encoding="utf-8") == "someone else's perch\n"


def test_uninstall_refuses_to_remove_an_unmanaged_entry(home):
    target = home / ".agents" / "skills" / "perch"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("someone else's perch\n", encoding="utf-8")
    with pytest.raises(perch.Refusal):
        perch.uninstall("codex")
    assert target.is_dir()


# --- the ~/.claude collision: the source IS the target here -------------


def test_claude_needs_no_projection_when_the_repo_is_the_claude_home(home):
    """The live shape on this machine: ``~/.claude`` is the harness checkout.

    PR #780 refused here, calling its own canonical skill an unmanaged entry.
    A target that already resolves to the canonical source is the goal state.
    """
    (home / ".claude").symlink_to(REPO, target_is_directory=True)
    state = perch.status("claude")
    assert state["installed"] is True
    assert state["projection"] == "none"
    assert perch.install("claude", version="99.0.0")  # a line, not a Refusal
    assert (home / ".claude" / "skills" / "perch" / "SKILL.md").is_file()


def test_the_floor_is_asserted_even_when_install_creates_nothing(home):
    """The already-discoverable path is a support claim, not a bare report.

    It is also the reference machine's own topology, so a floor skipped here
    is a floor never asserted for Claude Code at all.
    """
    (home / ".claude").symlink_to(REPO, target_is_directory=True)
    assert perch.status("claude")["installed"] is True
    with pytest.raises(perch.Refusal):
        perch.install("claude", version="0.0.1")


def test_status_never_probes_a_cli(home, monkeypatch):
    """status is the read-only report; it must answer with no CLI at all."""
    monkeypatch.setenv("PERCH_CODEX_BIN", "/nonexistent/codex")
    monkeypatch.setenv("PERCH_CLAUDE_BIN", "/nonexistent/claude")
    monkeypatch.setenv("PERCH_PI_BIN", "/nonexistent/pi")
    for harness in perch.HARNESSES:
        assert perch.status(harness)["installed"] is False


def test_claude_uninstall_never_deletes_the_canonical_skill(home):
    (home / ".claude").symlink_to(REPO, target_is_directory=True)
    perch.uninstall("claude")
    assert CANONICAL.is_file()
    assert (REPO / "skills" / "perch").is_dir()


def test_claude_gets_a_link_when_the_repo_lives_elsewhere(home):
    perch.install("claude", version="99.0.0")
    target = home / ".claude" / "skills" / "perch"
    assert target.is_symlink()
    assert target.resolve() == (REPO / "skills" / "perch").resolve()
    perch.uninstall("claude")
    assert not target.exists()


def test_another_checkouts_perch_is_named_as_such_not_clobbered(home):
    """Run from a worktree, the skills root holds the primary checkout's copy.

    Fail closed, and say which situation it is: a refusal that reads as the
    unmanaged-entry collision sends the reader hunting the wrong defect.
    """
    target = home / ".claude" / "skills" / "perch"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text(
        CANONICAL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert perch.status("claude")["projection"] == "other-checkout"
    with pytest.raises(perch.Refusal, match="another checkout"):
        perch.install("claude", version="99.0.0")
    assert (target / "SKILL.md").is_file()


def test_claude_discovery_never_reaches_the_neutral_home(home):
    """Claude Code reads only ``~/.claude/skills``; no duplicate perch."""
    perch.install("codex", version="99.0.0")
    assert perch.status("claude")["installed"] is False


# --- the evidence inventory ---------------------------------------------


def test_the_inventory_is_schema_valid():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(json.loads(INVENTORY.read_text(encoding="utf-8")), schema)


def test_the_schema_rejects_a_malformed_entry():
    """Positive control: the validator reacts to a case known to be bad."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    broken = json.loads(INVENTORY.read_text(encoding="utf-8"))
    broken["assertions"][0]["disposition"] = "probably-fine"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, schema)


def test_every_named_test_exists():
    """An inventory that names a test nobody runs is a claim, not evidence."""
    for entry in perch.inventory()["assertions"]:
        if entry["evidence_kind"] in ("manual-smoke", "documentation"):
            continue
        path, _, nodeid = entry["test"].partition("::")
        assert (REPO / path).is_file(), entry["test"]
        assert nodeid.split("[")[0] in (REPO / path).read_text(encoding="utf-8")


def test_manual_only_assertions_are_marked_pending_and_named():
    manual = [
        entry
        for entry in perch.inventory()["assertions"]
        if entry["evidence_kind"] == "manual-smoke"
    ]
    assert manual, "a live invocation cannot be automated; say so explicitly"
    for entry in manual:
        assert entry["disposition"] == "manual-only"
        assert entry["result"] == "pending"


def test_every_harness_has_a_version_policy_and_an_invocation():
    inventory = perch.inventory()
    assert {p["harness"] for p in inventory["versions"]} == set(perch.HARNESSES)
    invocations = {
        entry["harness"]: entry["native_expression"]
        for entry in inventory["assertions"]
        if entry["source_concept"] == "user invocation"
    }
    assert invocations == {"claude": "/perch", "codex": "$perch", "pi": "/skill:perch"}


def test_the_pilot_introduces_no_generator(monkeypatch):
    """Scope invariant: one hand-ported slice, not a framework."""
    text = (ADAPTERS / "perch.py").read_text(encoding="utf-8")
    for forbidden in ("def generate", "jinja", "template", "render_skill"):
        assert forbidden not in text.lower()


def test_no_absolute_home_path_is_baked_into_the_adapter():
    for path in (ADAPTERS / "perch.py", INVENTORY, SCHEMA):
        text = path.read_text(encoding="utf-8")
        assert "/home/" not in text
        assert os.path.expanduser("~") not in text
