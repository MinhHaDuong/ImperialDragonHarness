"""Build native Mistral ideal/real series from preserved attempts.

Costs use token totals and launch-discount EUR rates supplied by the author.
Rates are rounded console values, so estimates need not equal the invoice.
Elapsed times are summed per ticket (not parallel campaign wall time).
"""
import json
import statistics

RATES_EUR_M = {'in_sum': .58, 'cache_read_sum': .06, 'out_sum': 1.78}
USD_EUR = 1.08


def collect(arena):
    records = []
    paths = list((arena / 'runs').glob('*-m/run.json')) + list((arena / 'runs').glob('*-mr/run.json'))
    paths += [p for p in (arena / 'runs-void').rglob('run.json')
              if p.parent.name.endswith(('-m', '-mr')) and 'attempts' not in p.parts]
    seen = set()
    for path in sorted(paths):
        r = json.loads(path.read_text())
        if r.get('arm') not in {'m', 'mr'}:
            continue
        key = (r['ticket'], r['arm'], r.get('finished'), r.get('t0', {}).get('utc'), r.get('attempt'))
        if key in seen:
            continue
        seen.add(key)
        scores = []
        for jf in (path.parent / 'judges').glob('*.json'):
            q = json.loads(jf.read_text()).get('parsed')
            if isinstance(q, dict) and isinstance(q.get('score'), (int, float)):
                scores.append(q['score'])
        tokens = r.get('tokens', {})
        cost = sum(tokens.get(k, 0) * rate / 1e6 for k, rate in RATES_EUR_M.items()) * USD_EUR if tokens else (0 if r.get('cost_usd') == 0 else None)
        records.append({'ticket': r['ticket'], 'finished': r.get('finished', ''),
                        'verdict': r.get('verdict'), 'quality': sum(scores) if len(scores) == 3 else None,
                        'seconds': r.get('seconds'), 'cost_usd': cost,
                        'pi_cost_usd': r.get('cost_usd'), 'source': str(path.relative_to(arena))})
    return records


def add_series(snapshot, arena):
    records = collect(arena)
    tickets = [r['id'] for r in json.loads((arena / 'sample.json').read_text())]
    for arm, real in [('mi', False), ('mr', True)]:
        legs = {}
        for ticket in tickets:
            attempts = [r for r in records if r['ticket'] == ticket]
            successes = [r for r in attempts if r['verdict'] == 'OK' and r['quality'] is not None]
            if not successes:
                continue
            latest = max(successes, key=lambda r: r['finished'])
            legs[ticket] = {'state': 'ok', 'quality': max(r['quality'] for r in successes) if real else latest['quality'],
                            'seconds': sum(r['seconds'] for r in attempts) if real and all(r['seconds'] is not None for r in attempts) else latest['seconds'] if not real else None,
                            'cost_usd': sum(r['cost_usd'] for r in attempts) if real and all(r['cost_usd'] is not None for r in attempts) else latest['cost_usd'] if not real else None}
        def med(key):
            values = [r[key] for r in legs.values() if r[key] is not None]
            return statistics.median(values) if values else None
        snapshot['legs'][arm] = legs
        snapshot['arms'][arm] = {'expected': len(tickets), 'evaluated': len(legs), 'ok': len(legs), 'failures': 0,
                                 'pending': len(tickets)-len(legs), 'final': len(legs)==len(tickets),
                                 'quality_median': med('quality'), 'quality_mean': statistics.mean(r['quality'] for r in legs.values()) if legs else None,
                                 'seconds_median': med('seconds'), 'cost_usd_median': med('cost_usd'),
                                 'time_observed': sum(r['seconds'] is not None for r in legs.values()),
                                 'cost_observed': sum(r['cost_usd'] is not None for r in legs.values())}
    snapshot['mistral_accounting'] = {'scope': 'Mistral direct only; OpenRouter excluded', 'rates_eur_per_million': RATES_EUR_M,
                                     'usd_per_eur': USD_EUR, 'pricing': 'Estimate from rounded console launch-discount rates; not an invoice allocation',
                                     'ideal': 'Latest judged successful run per ticket', 'real': 'All completed attempts summed per ticket, best successful quality',
                                     'attempts': records}
