#!/usr/bin/env python3
"""Reproduce the notes-review tutorial with local disposable repositories only.

All review and gate judgments below are synthetic demonstration data. No reviewer,
model, CI service, or forge is invoked. JSON on stdout (or --output) is the evidence.
"""
import argparse
import hashlib
import json
import logging
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def demonstrate(scratch: Path, harness: Path) -> dict:
    # Construct a new environment: inherited Git routing/configuration is untrusted.
    home = scratch / 'home'
    home.mkdir()
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'XDG_CONFIG_HOME': str(home),
           'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_SYSTEM': '/dev/null',
           'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0',
           'GIT_ALLOW_PROTOCOL': 'file', 'IDH_REVIEW_BACKOFF': '0'}
    commands = []

    def run(argv, *, data=None):
        done = subprocess.run([str(a) for a in argv], input=data, capture_output=True,
                              text=True, env=env, cwd=scratch, timeout=30)
        if done.returncode:
            raise RuntimeError(f'{argv[0]} failed: {done.stderr}')
        return done.stdout.strip()

    def git(repo, *args):
        return run(['git', '-C', repo, *args])

    def notes(repo, *args, remote='origin'):
        # Every helper call has an explicit disposable -C, including gate operations.
        commands.append(['harness', Path(repo).name, '--remote', remote,
                         *(str(arg).replace(str(scratch), '<sandbox>') for arg in args)])
        return run([sys.executable, harness / 'scripts/review_notes.py', '-C', repo,
                    '--remote', remote, *args])

    def entries(repo, rid):
        return [json.loads(line) for line in notes(repo, 'show', rid).splitlines() if line.strip()]

    def check(value, message):
        if not value:
            raise AssertionError(message)

    def identity(repo):
        git(repo, 'config', 'user.name', 'Example participant')
        git(repo, 'config', 'user.email', 'example@example.invalid')
        git(repo, 'config', 'commit.gpgsign', 'false')

    before = git(harness, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/notes/')
    origin, a, b = (scratch / name for name in ('origin.git', 'author', 'reviewer'))
    run(['git', 'init', '-q', '--bare', '-b', 'main', origin])
    run(['git', 'init', '-q', '-b', 'main', a])
    identity(a)
    (a / 'value.txt').write_text('one\n')
    (a / 'other.txt').write_text('base\n')
    git(a, 'add', '.')
    git(a, 'commit', '-qm', 'base')
    git(a, 'remote', 'add', 'origin', str(origin))
    git(a, 'push', '-q', 'origin', 'main')
    git(a, 'switch', '-qc', 'feature')
    (a / 'value.txt').write_text('two\n')
    git(a, 'commit', '-qam', 'feature')
    git(a, 'push', '-q', 'origin', 'feature')
    head1 = git(a, 'rev-parse', 'HEAD')
    rid = notes(a, 'open', '--branch', 'feature', '--base-ref', 'origin/main',
                '--why', 'DEMONSTRATION: review the value change', '--intent', 'synthetic example')
    req1 = entries(a, rid)[0]
    sample_first_tip = git(a, 'rev-parse', 'refs/notes/review')
    check(notes(a, 'publish', req1['id']) == 'retrievable', 'request publication failed')

    run(['git', 'clone', '-q', origin, b])
    identity(b)
    # Positive demonstration: default clone transports branches, not this notes ref.
    check(not git(b, 'for-each-ref', '--format=%(refname)', 'refs/notes/review'), 'unexpected notes')
    notes(b, 'setup')
    notes(b, 'refresh')
    check(entries(b, rid)[0]['id'] == req1['id'], 'second clone did not retrieve request')
    retained = f"refs/review-heads/{rid}/{req1['request_id']}"
    check(git(b, 'rev-parse', retained) == head1, 'first retained head differs')

    # Two clones append before either publishes: create divergent notes histories.
    report_ids = []
    for repo, seat in ((a, 'author-observation'), (b, 'reviewer-observation')):
        fields = {'run_id': 'example-run', 'seat_id': seat, 'status': 'ran',
                  'text': 'DEMONSTRATION ONLY: synthetic observation; no review performed.'}
        report_ids.append(notes(repo, 'add', 'report', '--review', rid, '--request',
                                req1['request_id'], '--head', head1, '--json', json.dumps(fields)))
    for repo, entry in zip((a, b), report_ids):
        check(notes(repo, 'publish', entry) == 'retrievable', 'report publication failed')
    notes(a, 'refresh')
    got = {e['id'] for e in entries(a, rid)}
    check(set(report_ids) <= got, 'concurrent writer lost an entry')

    answer = {'run_id': 'example-run', 'result': 'REVIEWED', 'seats': 'self-only',
              'coverage': {'scope': 'full'},
              'text': 'DEMONSTRATION ONLY: synthetic REVIEWED, no actual quality judgment.'}
    aid = notes(a, 'add', 'answer', '--review', rid, '--request', req1['request_id'],
                '--head', head1, '--author', '{"role":"demonstration","runtime":"offline-example"}',
                '--json', json.dumps(answer))
    # Nonexistent remote selects documented local mode and avoids detached background sync.
    state = json.loads(notes(a, 'gate', rid, head1, remote='local-only'))
    check(state['ready'], 'synthetic answer did not admit the example gate')
    verdict = scratch / 'synthetic-verdict.txt'
    verdict.write_text('DEMONSTRATION ONLY: APPROVED is fabricated tutorial evidence, not a real gate.\n')
    notes(a, 'verdict', '--review', rid, '--session', '00000000-0000-4000-8000-000000000001',
          '--verdict', 'APPROVED', '--head', head1, '--evidence', aid,
          '--text-file', str(verdict), remote='local-only')
    check(notes(a, 'publish', aid) == 'retrievable', 'answer publication failed')

    # Move main in another file, then rebase the same feature diff.
    git(a, 'switch', '-q', 'main')
    (a / 'other.txt').write_text('new base\n')
    git(a, 'commit', '-qam', 'main advances')
    git(a, 'push', '-q', 'origin', 'main')
    git(a, 'switch', '-q', 'feature')
    git(a, 'rebase', '-q', 'origin/main')
    rebased = git(a, 'rev-parse', 'HEAD')
    check(rebased != head1, 'rebase positive control did not change head')
    rebase_match = json.loads(notes(a, 'coverage', rid, rebased))['match']
    check(rebase_match == 'patch-id', 'unchanged diff did not carry coverage')
    (a / 'value.txt').write_text('three\n')
    git(a, 'commit', '-qam', 'revised feature')
    head2 = git(a, 'rev-parse', 'HEAD')
    changed_match = json.loads(notes(a, 'coverage', rid, head2))['match']
    check(changed_match == 'none', 'changed diff unexpectedly carried coverage')
    # No force-push is needed: heads travel through newly minted retained-head refs.
    notes(a, 'request', '--review', rid, '--branch', 'feature', '--base-ref', 'origin/main',
          '--why', 'DEMONSTRATION: revised value', '--intent', 'needs a fresh review')
    req2 = [e for e in entries(a, rid) if e['kind'] == 'request'][-1]
    check(req2['request_id'] != req1['request_id'] and bool(req2['delta']), 'revision lacks identity/delta')
    check(notes(a, 'publish', req2['id']) == 'retrievable', 'revision publication failed')
    notes(b, 'refresh')
    check(git(b, 'rev-parse', retained) == head1, 'old retained head was overwritten')
    check(git(b, 'rev-parse', f"refs/review-heads/{rid}/{req2['request_id']}") == head2,
          'new retained head not retrieved')

    export = scratch / 'review.jsonl'
    export.write_text(notes(a, 'export', rid) + '\n')
    recovery = scratch / 'recovery'
    run(['git', 'init', '-q', '-b', 'main', recovery])
    identity(recovery)
    notes(recovery, 'import', str(export))
    check(entries(recovery, rid) == entries(a, rid), 'JSONL recovery differs')
    # Import restores records, not code objects. Retained refs need separate transport.
    sample_last_tip = git(a, 'rev-parse', 'refs/notes/review')
    check(sample_first_tip != sample_last_tip, 'sample notes positive control failed')
    after = git(harness, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/notes/')
    check(before == after, 'harness notes changed during example; investigate concurrent activity')
    return {'generated_at': datetime.now(timezone.utc).isoformat(), 'synthetic_evidence': True,
            'git_version': run(['git', '--version']),
            'helper_sha256': hashlib.sha256((harness / 'scripts/review_notes.py').read_bytes()).hexdigest(),
            'example_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'checks': {'harness_notes_unchanged': True, 'sample_notes_changed': True,
                       'default_clone_lacks_notes': True, 'concurrent_entries_retrieved': True,
                       'rebase_match': rebase_match, 'changed_revision_match': changed_match,
                       'old_head_retrieved': True, 'new_head_retrieved': True,
                       'export_import_equal': True},
            'commands': commands}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, help='JSON evidence; otherwise stdout')
    parser.add_argument('--scratch-parent', type=Path, default=Path('/tmp'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='notes-review-example-', dir=args.scratch_parent) as tmp:
        result = demonstrate(Path(tmp), args.harness.resolve())
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
        logging.info('Wrote example evidence to %s', args.output)
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
