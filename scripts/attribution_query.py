#!/usr/bin/env python3
"""Read one project's attribution facts; report scores and same-game coverage."""

import argparse
import itertools
import json
import logging
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __package__:
    from .attribution_record import parse_record, runtime_masked
else:
    from attribution_record import parse_record, runtime_masked

LOG = logging.getLogger(__name__)
RECORD_NAME = re.compile(r"\d{4}-\d{2}-\d{2}-review-attribution-pr([1-9][0-9]*)(\.md|\.age|\.md\.age)$")
REVIEWER_FIELDS = ('seat', 'runtime', 'model', 'model-version')
WRITER_FIELDS = ('runtime', 'model', 'model-version', 'effort')
GUIDANCE = (
    'Fixed §7: Eliminate a seat when, over at least 10 labeled games, the 90% CrI '
    'upper bound of its false-finding share exceeds 0.5, or its run-failure rate '
    'upper bound exceeds 0.5. Promote a candidate only when its labeled-game '
    'catch-rate 90% lower bound exceeds the incumbent\'s 90% upper bound on '
    'the same labeled board, and its false-finding share upper bound is below 0.5. '
    'Report correlation always; act only when intervals justify it '
    '(approximately 60 labeled games per pair for fine distinctions). '
    'No automatic roster action; unconfirmed findings are proxies, not proven hallucinations.'
)


def rate(successes, trials):
    """Fixed Jeffreys posterior with central 90% interval (including prior-only)."""
    from scipy.special import betaincinv

    return {'successes': successes, 'trials': trials,
            'value': successes / trials if trials else None,
            'interval90': [float(betaincinv(successes + .5, trials - successes + .5, q))
                           for q in (.05, .95)], 'prior_only': trials == 0}


def identity_key(identity, fields):
    # Missing version is a distinct recorded identity, never inferred or pooled.
    return tuple(identity.get(field) for field in fields)


def identity_dict(key, fields):
    return dict(zip(fields, key))


def project_local(path, project):
    """Do not follow symlink components, including links within the project."""
    relative = path.relative_to(project)
    current = project
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False
    return path.resolve().is_relative_to(project)


def journal_entries(journal, project, counts):
    """Traverse only local directories, never a symlinked journal/year root."""
    pending = [journal]
    while pending:
        directory = pending.pop()
        if not project_local(directory, project):
            counts['unsafe_unavailable'] += 1
            LOG.warning('WARN %s: symlink or escaping journal component unavailable', directory)
            continue
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_symlink() and not RECORD_NAME.fullmatch(path.name):
                counts['unsafe_unavailable'] += 1
                LOG.warning('WARN %s: symlink journal component unavailable', path)
            elif path.is_dir() and not path.is_symlink():
                pending.append(path)
            elif RECORD_NAME.fullmatch(path.name):
                yield path


def read_records(project):
    project = project.resolve()
    candidates = {}
    sources = defaultdict(set)
    unavailable_prs = set()
    counts = {'valid': 0, 'malformed': 0, 'ambiguous_prs': [],
              'ambiguous_records': 0, 'encrypted_unavailable': 0,
              'unsafe_unavailable': 0}
    journal = project / 'memory' / 'journal'
    for path in journal_entries(journal, project, counts):
        match = RECORD_NAME.fullmatch(path.name)
        pr = int(match[1])
        # Reserve identity before parsing: invalid/encrypted evidence is still
        # evidence of another source for this PR, never permission to pick one.
        sources[pr].add(path)
        if not project_local(path, project):
            counts['unsafe_unavailable'] += 1
            unavailable_prs.add(pr)
            LOG.warning('WARN %s: symlink or escaping record unavailable; not read', path)
            continue
        if match[2].endswith('.age'):
            counts['encrypted_unavailable'] += 1
            unavailable_prs.add(pr)
            LOG.warning('WARN %s: encrypted attribution unavailable; no decryption attempted', path)
            continue
        try:
            text = path.read_text()
            header_prs = {int(value) for value in re.findall(
                r'^\s*pr\s*:\s*([1-9][0-9]*)(?=\s|·|$)', text, re.MULTILINE)}
            for header_pr in header_prs:
                sources[header_pr].add(path)
            record = parse_record(text)
            if record['pr'] != pr:
                raise ValueError('filename PR differs from record PR')
        except (ValueError, OSError) as error:
            counts['malformed'] += 1
            unavailable_prs.update(key for key, paths in sources.items() if path in paths)
            LOG.warning('WARN %s: %s; excluding whole record', path, error)
            continue
        candidates[pr] = record
    ambiguous_paths = set()
    for pr, paths in sorted(sources.items()):
        if len(paths) > 1:
            counts['ambiguous_prs'].append(pr)
            ambiguous_paths.update(paths)
            unavailable_prs.add(pr)
            LOG.warning('WARN ambiguous PR %s: excluding all %s record sources: %s',
                        pr, len(paths), ', '.join(str(path) for path in sorted(paths)))
    counts['ambiguous_records'] = len(ambiguous_paths)
    records = [record for pr, record in sorted(candidates.items()) if pr not in unavailable_prs]
    counts['valid'] = len(records)
    counts['runtime_masked'] = sum(runtime_masked(record) for record in records)
    counts['model_attributable'] = counts['valid'] - counts['runtime_masked']
    for record in records:
        if runtime_masked(record):
            LOG.warning('WARN PR %s: runtime-masked identity; whole game excluded from model estimates', record['pr'])
    if not records:
        LOG.warning('WARN %s: no attribution records available', journal)
    return records, counts, unavailable_prs


def game_attempts(record):
    """Union an exact identity's anchors, retaining emitted attempt multiplicity."""
    identities = {}
    labels = set(record['defect_labels'])
    for attempt in record['reviewers']:
        key = identity_key(attempt, REVIEWER_FIELDS)
        entry = identities.setdefault(key, {'attempts': Counter(), 'anchors': set(), 'findings': []})
        entry['attempts'][attempt['status']] += 1
        entry['anchors'].update(finding['anchor'] for finding in attempt['findings'])
        entry['findings'].extend(attempt['findings'])
    for entry in identities.values():
        entry['confirmed'] = entry['anchors'] & labels
        entry['unconfirmed'] = entry['anchors'] - labels
    return identities


def derive(records):
    scores = {}
    pairs = {}
    for record in records:
        if runtime_masked(record):
            continue
        writer = identity_key(record['writer'], WRITER_FIELDS)
        labeled = bool(record['defect_labels'])
        identities = game_attempts(record)
        for key, entry in identities.items():
            score = scores.setdefault((writer, key), {'attempts': Counter(), 'catch': 0,
                                                     'labeled_games': 0, 'noise': 0, 'findings': 0})
            score['attempts'].update(entry['attempts'])
            score['findings'] += len(entry['findings'])
            score['noise'] += sum(f['anchor'] not in record['defect_labels'] for f in entry['findings'])
            if labeled and entry['attempts']['ran']:
                score['labeled_games'] += 1
                score['catch'] += bool(entry['confirmed'])
        if not labeled:
            continue
        ran = [key for key, entry in identities.items() if entry['attempts']['ran']]
        # repr gives deterministic ordering even when version is absent (None).
        for a, b in itertools.combinations(sorted(ran, key=repr), 2):
            pair = pairs.setdefault((writer, a, b), {'cells': Counter(), 'unique_a_games': 0, 'unique_b_games': 0,
                                                    'unique_a_anchors': 0, 'unique_b_anchors': 0, 'intersection': 0,
                                                    'union': 0, 'shared_unconfirmed': 0,
                                                    'unconfirmed_union': 0})
            ac, bc = identities[a]['confirmed'], identities[b]['confirmed']
            cell = 'both' if ac and bc else 'unique_a' if ac else 'unique_b' if bc else 'neither'
            pair['cells'][cell] += 1
            pair['unique_a_games'] += bool(ac - bc)
            pair['unique_a_anchors'] += len(ac - bc)
            pair['unique_b_games'] += bool(bc - ac)
            pair['unique_b_anchors'] += len(bc - ac)
            # Anchor keys are scoped to a game: same path:line in another PR is another trial.
            pair['intersection'] += len(ac & bc)
            pair['union'] += len(ac | bc)
            au, bu = identities[a]['unconfirmed'], identities[b]['unconfirmed']
            pair['shared_unconfirmed'] += len(au & bu)
            pair['unconfirmed_union'] += len(au | bu)
    result_scores = []
    for (writer, key), score in sorted(scores.items(), key=lambda item: repr(item[0])):
        attempts = {status: score['attempts'][status] for status in ('ran', 'failed', 'skipped')}
        attempts['attempted'] = sum(attempts.values())
        result_scores.append({'writer': identity_dict(writer, WRITER_FIELDS),
                              'identity': identity_dict(key, REVIEWER_FIELDS), 'attempts': attempts,
                              'catch': rate(score['catch'], score['labeled_games']),
                              'nonconfirmed_finding_share_proxy': rate(score['noise'], score['findings']),
                              'run_failure': rate(attempts['failed'], attempts['ran'] + attempts['failed'])})
    result_pairs = []
    for (writer, a, b), pair in sorted(pairs.items(), key=lambda item: repr(item[0])):
        cells = {cell: pair['cells'][cell] for cell in ('both', 'unique_a', 'unique_b', 'neither')}
        games = sum(cells.values())
        result_pairs.append({'writer': identity_dict(writer, WRITER_FIELDS),
                             'a': identity_dict(a, REVIEWER_FIELDS), 'b': identity_dict(b, REVIEWER_FIELDS),
                             'labeled_both_ran_games': games, 'cells': cells,
                             'cell_rates': {cell: rate(count, games) for cell, count in cells.items()},
                             'confirmed_anchor_jaccard': {'intersection': pair['intersection'], 'union': pair['union'],
                                                          'value': pair['intersection']/pair['union'] if pair['union'] else None},
                             'shared_nonconfirmed_anchor_proxy': rate(pair['shared_unconfirmed'], pair['unconfirmed_union']),
                             'unique_a_anchors': pair['unique_a_anchors'],
                             'unique_b_anchors': pair['unique_b_anchors'],
                             'marginal_a_given_b': rate(pair['unique_a_games'], games),
                             'marginal_b_given_a': rate(pair['unique_b_games'], games)})
    return {'scores': result_scores, 'pairs': result_pairs}


def coverage(project, since, until, records, unavailable_prs):
    """Enumerate only an explicitly requested range; never infer absent reviewers."""
    enumerator = Path(__file__).resolve().with_name('enumerate-merges.py')
    completed = subprocess.run([sys.executable, str(enumerator), since, '--until', until],
                               cwd=project, text=True, capture_output=True, check=True)
    if completed.stderr:
        LOG.warning('%s', completed.stderr.rstrip())
    merges = [json.loads(line) for line in completed.stdout.splitlines()]
    valid_prs = {record['pr'] for record in records}
    masked_prs = {record['pr'] for record in records if runtime_masked(record)}
    for merge in merges:
        pr = merge['pr']
        merge['attribution'] = ('runtime-masked' if pr in masked_prs else 'available' if pr in valid_prs else 'unavailable' if pr in unavailable_prs
                                else 'missing' if pr is not None else 'unknown-pr')
        if merge['attribution'] != 'available':
            LOG.warning('WARN merge %s PR %s: %s attribution evidence', merge['merge_sha'], pr, merge['attribution'])
    return merges


def describe(identity):
    return ','.join(f'{key}={value if value is not None else "unrecorded"}' for key, value in identity.items())


def describe_rate(value):
    low, high = value['interval90']
    label = ' prior-only' if value['prior_only'] else ''
    return f"{value['successes']}/{value['trials']} [{low:.4f},{high:.4f}]{label}"


def render(data):
    lines = [f"Records: {json.dumps(data['records'])}",
             'Scores: catch=labeled PRs with any confirmed anchor / labeled PRs where identity ran; '
             'noise=nonconfirmed emitted findings / all emitted findings (proxy); '
             'failure=failed/(ran+failed) attempts; skipped separate. All intervals central 90% Jeffreys.',
             'writer | identity | attempted/ran/failed/skipped | catch | nonconfirmed-finding-share proxy | run-failure']
    for score in data['scores']:
        attempts = score['attempts']
        lines.append(' | '.join([describe(score['writer']), describe(score['identity']),
                                 '/'.join(str(attempts[k]) for k in ('attempted','ran','failed','skipped')),
                                 describe_rate(score['catch']), describe_rate(score['nonconfirmed_finding_share_proxy']),
                                 describe_rate(score['run_failure'])]))
    lines += ['Pairs: only labeled PRs where both exact identities ran; binary any-catch cells. '
              'Jaccard uses same-game confirmed anchors. Each directional marginal counts games with any candidate anchor absent the incumbent, '
              'including both-catch games. Shared nonconfirmed anchors are a proxy, not proven hallucinations.',
              'writer | A | B | games | both/unique-A/unique-B/neither | anchor-Jaccard | unique-A anchors | unique-B anchors | marginal A given B | marginal B given A | shared nonconfirmed-anchor proxy']
    for pair in data['pairs']:
        overlap = pair['confirmed_anchor_jaccard']
        lines.append(' | '.join([describe(pair['writer']), describe(pair['a']), describe(pair['b']),
                                 str(pair['labeled_both_ran_games']), '/'.join(str(n) for n in pair['cells'].values()),
                                 f"{overlap['intersection']}/{overlap['union']}", str(pair['unique_a_anchors']), str(pair['unique_b_anchors']),
                                 describe_rate(pair['marginal_a_given_b']),
                                 describe_rate(pair['marginal_b_given_a']), describe_rate(pair['shared_nonconfirmed_anchor_proxy'])]))
    if 'coverage' in data:
        lines.append('Explicit merge-range coverage: ' + json.dumps(data['coverage']))
    lines.append(GUIDANCE)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', nargs='?', type=Path, default=Path.cwd())
    parser.add_argument('--json', action='store_true', help='structured result from the same read-only derivation')
    parser.add_argument('--since', help='explicit git range start for missing-record coverage')
    parser.add_argument('--until', default='HEAD', help='explicit range endpoint (default HEAD); requires --since')
    args = parser.parse_args()
    if args.until != 'HEAD' and not args.since:
        parser.error('--until requires --since')
    try:
        records, counts, unavailable = read_records(args.project)
        result = derive(records)
        result.update(records=counts, guidance=GUIDANCE)
        if args.since:
            result['coverage'] = coverage(args.project, args.since, args.until, records, unavailable)
    except (OSError, subprocess.CalledProcessError) as error:
        LOG.error('attribution-query: %s', error)
        return 1
    sys.stdout.write((json.dumps(result, ensure_ascii=False) if args.json else render(result)) + '\n')
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    sys.exit(main())
