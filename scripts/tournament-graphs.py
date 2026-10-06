#!/usr/bin/env python3
"""Render reproducible paired-comparison graphs as A4 landscape PDF + DOT.
Usage: python3 scripts/tournament-graphs.py --arena ~/arena --output docs/tournament-graphs
"""
import argparse
import csv
import datetime
import importlib.util
import itertools
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['pdf.fonttype'] = 42
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch
from matplotlib.transforms import Bbox
import numpy as np
from scipy.stats import rankdata

spec = importlib.util.spec_from_file_location('analysis', Path(__file__).with_name('tournament-analysis.py'))
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
LABELS = {
'a': 'Qwen 3.8 27B\nQ4_K_M · llama.cpp\nxhigh (fixé côté serveur)',
'b': 'Qwen 3.8 Flash-Next Coder\nIQ1_M · Strata · pruned\nxhigh (fixé côté serveur)',
'b2': 'Qwen 3.8 Flash-Next\nIQ3_S · Strata\nxhigh (fixé côté serveur)',
'b3': 'Qwen 3.8 Flash-Next\nQ2_0 · Strata\nxhigh (fixé côté serveur)',
'c': 'Qwen 3.6 35B-A3B\nUD-Q4_K_XL · llama.cpp\neffort non mesuré',
'c2': 'Qwen 3 Coder 30B-A3B\nUD-Q4_K_XL · llama.cpp\neffort non mesuré',
'd': 'Claude Opus 5.5\nAPI Anthropic\nmedium',
'd2': 'Claude Opus 5.5\nAPI Anthropic\nlow',
'e': 'GPT 6 Sol\nAPI OpenAI\nmedium',
'e2': 'GPT 6.1 Sol\nAPI OpenAI\nlow',
'e3': 'GPT 6.1 Sol\nAPI OpenAI\nmedium',
'f': 'GLM 5.3\nAPI Mistral\nhigh',
'g': 'Claude Sonnet 5.5\nAPI Anthropic\nmedium',
'i': 'DeepSeek Flash\nAPI DeepSeek\nhigh',
'j': 'GLM 5.3 Flash\nAPI OpenRouter\nhigh',
'k': 'Mimo v2.6 Flash\nAPI OpenRouter\nmedium',
'l': 'GPT 6 Luna\nAPI OpenAI\nmedium',
}
AXES = {'quality': ('Qualité', 1, 'points /30'), 'seconds': ('Vitesse', -1, 'secondes'), 'cost_usd': ('Coût', -1, 'USD par tentative')}


def signed_rank(differences):
    """Exact two-sided sign permutation of Wilcoxon ranks, including tied ranks.
    Zero differences omitted; nonzero differences assumed symmetric under H0.
    """
    d = np.round(np.asarray(differences, dtype=float), 9)
    d = d[d != 0]
    if not len(d):
        return 1.0, 0
    ranks = rankdata(abs(d))
    observed = float(np.dot(np.sign(d), ranks))
    extreme = sum(abs(np.dot(signs, ranks)) >= abs(observed) - 1e-10
                  for signs in itertools.product((-1, 1), repeat=len(d)))
    return float(extreme / 2 ** len(d)), 1 if observed > 0 else -1 if observed < 0 else 0


def reachable(start, end, edges):
    seen = {start}; todo = [start]
    while todo:
        u = todo.pop()
        for a, b in edges:
            if a == u:
                if b == end:
                    return True
                if b not in seen:
                    seen.add(b); todo.append(b)
    return False


def reduce_edges(nodes, edges):
    # SCC condensation: preserve within-cycle evidence; reduce only between SCCs.
    groups = []
    remaining = set(nodes)
    while remaining:
        u = min(remaining)
        group = {v for v in remaining if v == u or (reachable(u, v, edges) and reachable(v, u, edges))}
        groups.append(group); remaining -= group
    membership = {v: i for i, g in enumerate(groups) for v in g}
    condensed = {(membership[a], membership[b]) for a, b in edges if membership[a] != membership[b]}
    reduced = set(condensed)
    for edge in sorted(condensed):
        if reachable(*edge, reduced - {edge}):
            reduced.remove(edge)
    result = {(a, b) for a, b in edges if membership[a] == membership[b] or (membership[a], membership[b]) in reduced}
    return result, groups


def holm(rows):
    order = sorted(range(len(rows)), key=lambda i: rows[i]['p'])
    previous = 0
    for rank, i in enumerate(order):
        previous = max(previous, min(1, (len(rows) - rank) * rows[i]['p']))
        rows[i]['p_holm'] = previous


def pareto_xy(arms, xkey, ykey):
    """Two-axis frontier of complete identities; quality up, resources down."""
    eligible = {a: r for a, r in arms.items() if r['final'] and r.get('quality_median') is not None and r['quality_median'] >= 15
                and r.get(xkey) is not None and r.get(ykey) is not None}
    def dominates(x, y):
        advantages = [(x[k] - y[k]) * (1 if k == 'quality_median' else -1) for k in [xkey, ykey]]
        return all(v >= 0 for v in advantages) and any(v > 0 for v in advantages)
    return {a for a, r in eligible.items() if not any(dominates(other, r) for b, other in eligible.items() if b != a)}


def render(output, snapshot):
    nodes = sorted(snapshot['arms'])
    results = {}
    for metric, (title, direction, units) in AXES.items():
        rows = []
        for a, b in itertools.combinations(nodes, 2):
            if not snapshot['arms'][a]['final'] or not snapshot['arms'][b]['final']:
                continue
            common = sorted(set(snapshot['legs'][a]) & set(snapshot['legs'][b]))
            differences = [direction * (snapshot['legs'][a][t][metric] - snapshot['legs'][b][t][metric])
                           for t in common if snapshot['legs'][a][t][metric] is not None and snapshot['legs'][b][t][metric] is not None]
            if not differences:
                continue
            p, sign = signed_rank(differences)
            rows.append({'axis': metric, 'a': a, 'b': b, 'n': len(differences), 'p': p,
                         'winner': a if sign > 0 else b if sign < 0 else '',
                         'loser': b if sign > 0 else a if sign < 0 else '',
                         'median_advantage': statistics.median(differences) * sign})
        holm(rows)
        edges = {(r['winner'], r['loser']) for r in rows if r['p'] < .05 and r['winner']}
        reduced, groups = reduce_edges(nodes, edges)
        for r in rows:
            r['shown'] = (r['winner'], r['loser']) in reduced and r['p'] < .05
        results[metric] = {'comparisons': rows, 'edges': sorted(edges), 'reduced': sorted(reduced),
                           'holm_edges': [(r['winner'], r['loser']) for r in rows if r['p_holm'] < .05]}
        dot = ['digraph G {', 'rankdir=TB;', 'node [shape=box, fontname="DejaVu Sans"];']
        for a in nodes:
            label = LABELS[a] + ('\nPROVISOIRE' if not snapshot['arms'][a]['final'] else '')
            dot.append(f'{a} [label={json.dumps(label, ensure_ascii=False)}];')
        for a, b in sorted(reduced):
            r = next(r for r in rows if r['winner'] == a and r['loser'] == b)
            dot.append(f'{a} -> {b} [label="p={r["p"]:.4f}; n={r["n"]}"];')
        dot.append('}')
        (output / f'{metric}.dot').write_text('\n'.join(dot)+'\n')
    with PdfPages(output / 'comparaisons-modeles.pdf', metadata={'Title': 'Tournoi : comparaisons appariées à 95 %', 'Author': 'Minh Ha Duong', 'Subject': 'Qualité, vitesse et coût ; réduction transitive'}) as pdf:
        for metric, (title, direction, units) in AXES.items():
            edges = set(map(tuple, results[metric]['reduced']))
            _, groups = reduce_edges(nodes, edges)
            membership = {v: i for i, g in enumerate(groups) for v in g}
            ranks = dict.fromkeys(range(len(groups)), 0)
            for _ in range(len(groups)):
                for a, b in edges:
                    if membership[a] != membership[b]:
                        ranks[membership[b]] = max(ranks[membership[b]], ranks[membership[a]] + 1)
            layers = {}
            for a in nodes:
                layers.setdefault(ranks[membership[a]], []).append(a)
            # Barycentric ordering reduces crossings without changing the graph.
            for _ in range(5):
                for level in sorted(layers):
                    previous_positions = {a: i for lay in layers.values() for i, a in enumerate(lay)}
                    layers[level].sort(key=lambda a: statistics.mean([previous_positions[u] for u, v in edges if v == a]) if any(v == a for u, v in edges) else previous_positions[a])
            positions = {}
            maxrank = max(layers)
            for rank, layer in layers.items():
                for index, a in enumerate(layer):
                    positions[a] = ((index+.5)/len(layer), 1 - (rank + .5)/(maxrank+1))
            fig, ax = plt.subplots(figsize=(11.6929, 8.2677))
            fig.subplots_adjust(left=.035, right=.965, bottom=.13, top=.85)
            fig.suptitle(f'{title} — qui bat qui ?', fontsize=19, fontweight='bold', x=.045, ha='left')
            fig.text(.045,.89,'Meilleur en haut · flèche vers le moins bon · Wilcoxon apparié exact · p < 0,05 bilatéral',fontsize=10)
            for a, b in sorted(edges):
                ax.add_patch(FancyArrowPatch(positions[a], positions[b], arrowstyle='-|>', mutation_scale=12,
                                            color='#64748b', linewidth=1, shrinkA=32, shrinkB=34,
                                            connectionstyle='arc3,rad=0.04', zorder=1))
            for a, (x,y) in positions.items():
                provisional = not snapshot['arms'][a]['final']
                ax.text(x,y,LABELS[a]+ ('\nPROVISOIRE' if provisional else ''),ha='center',va='center',fontsize=7.3,
                        bbox={'boxstyle':'round,pad=.4','facecolor':'#fff7ed' if provisional else '#eff6ff',
                              'edgecolor':'#ea580c' if provisional else '#2563eb','linestyle':'--' if provisional else '-'},zorder=2)
            ax.set_xlim(-.015,1.015);ax.set_ylim(-.02,1.02);ax.axis('off')
            summary=results[metric]
            fig.text(.045,.075,f"{len(summary['edges'])} différences significatives ; {len(edges)} flèches après réduction transitive. "
                     f"Holm (famille de {len(summary['comparisons'])} tests) : {len(summary['holm_edges'])} flèches.",fontsize=9)
            fig.text(.045,.045,'Seuil nominal par comparaison, sans garantie simultanée. Absence de flèche ≠ équivalence.\n'
                     'Un chemin indirect ne constitue pas un nouveau test significatif. Détails p et n dans le CSV et les fichiers DOT.',fontsize=8)
            pdf.savefig(fig);fig.savefig(output/f'{metric}.png',dpi=160);plt.close(fig)
        scatter_axes = [
            ('quality-cost', 'Qualité / coût', 'cost_usd_median', 'quality_median',
             'Coût médian (USD ; plus bas = moins cher)', 'Qualité médiane (/30 ; plus haut = meilleur)'),
            ('quality-speed', 'Qualité / vitesse', 'seconds_median', 'quality_median',
             'Durée médiane (minutes ; plus bas = plus rapide)', 'Qualité médiane (/30 ; plus haut = meilleur)'),
            ('speed-cost', 'Vitesse / coût', 'cost_usd_median', 'seconds_median',
             'Coût médian (USD ; plus bas = moins cher)', 'Durée médiane (minutes ; plus bas = plus rapide)'),
        ]
        for name, title, xkey, ykey, xlabel, ylabel in scatter_axes:
            fig=plt.figure(figsize=(11.6929,8.2677))
            ax=fig.add_axes([.08,.16,.54,.66])
            fig.suptitle(title,fontsize=20,fontweight='bold',x=.045,ha='left')
            fig.text(.045,.89,'Identités modèle × variante × effort · médianes par ticket, échecs de modèle inclus',fontsize=10)
            entries=[]
            frontier=pareto_xy(snapshot['arms'],xkey,ykey)
            for a in nodes:
                row=snapshot['arms'][a]
                if row[xkey] is None or row[ykey] is None:continue
                x=row[xkey]/60 if xkey == 'seconds_median' else row[xkey]
                y=row[ykey]/60 if ykey == 'seconds_median' else row[ykey]
                color='#2563eb' if a in analysis.LOCAL else '#059669'
                provisional=not row['final']
                ax.scatter(x,y,s=65,marker='o' if a in analysis.LOCAL else 's',
                           facecolors='none' if provisional else color,edgecolors='#ea580c' if provisional else color,zorder=3)
                if a in frontier:
                    ax.scatter(x,y,s=210,facecolors='none',edgecolors='#b45309',linewidths=1.8,zorder=2)
                entries.append((a,x,y,color,provisional))
            if xkey in {'cost_usd_median','seconds_median'}:ax.set_xscale('log')
            if ykey == 'seconds_median':ax.set_yscale('log')
            if ykey == 'quality_median':ax.set_ylim(0,32)
            ax.margins(x=.17,y=.15);ax.grid(alpha=.2,which='both');ax.set_xlabel(xlabel,fontsize=10);ax.set_ylabel(ylabel,fontsize=10)
            # Deterministic label placement in display coordinates, with leader lines.
            fig.canvas.draw(); renderer=fig.canvas.get_renderer(); boxes=[]
            point_boxes=[]
            for _,x,y,_,_ in entries:
                px,py=ax.transData.transform((x,y))
                point_boxes.append(Bbox.from_extents(px-13,py-13,px+13,py+13))
            bounds=ax.get_window_extent(renderer)
            for a,x,y,color,provisional in sorted(entries,key=lambda item:(item[0] not in frontier,item[2],item[1])):
                annotation=None
                offsets=[(dx,dy) for radius in range(15,226,10)
                         for dx,dy in [(radius,radius),(-radius,radius),(radius,-radius),(-radius,-radius),
                                       (0,radius),(0,-radius),(radius,0),(-radius,0),
                                       (radius/2,radius),(-radius/2,radius),(radius/2,-radius),(-radius/2,-radius)]]
                if name == 'quality-cost' and a in {'c', 'c2'}:
                    preferred = [(22, 20), (30, 28)] if a == 'c' else [(-22, -20), (-30, -28)]
                    offsets = preferred + offsets
                placed=False
                for dx,dy in offsets:
                    if annotation:annotation.remove()
                    label=(a+' · '+LABELS[a]) if a in frontier else a+("*" if provisional else "")
                    annotation=ax.annotate(label,(x,y),xytext=(dx,dy),textcoords='offset points',
                                           fontsize=7 if a in frontier else 9,ha='center',va='center',
                                           color='#92400e' if a in frontier else '#ea580c' if provisional else color,
                                           arrowprops={'arrowstyle':'-','color':'#94a3b8','lw':.7},
                                           bbox={'facecolor':'none','edgecolor':'none','pad':1.3})
                    annotation.update_positions(renderer)
                    annotation.update_bbox_position_size(renderer)
                    box=annotation.get_bbox_patch().get_window_extent(renderer).expanded(1.05,1.08)
                    inside=box.x0 >= bounds.x0+2 and box.x1 <= bounds.x1-2 and box.y0 >= bounds.y0+2 and box.y1 <= bounds.y1-2
                    if inside and not any(box.overlaps(other) for other in boxes+point_boxes):
                        placed=True;break
                if not placed:
                    raise RuntimeError(f'No collision-free position for {name}/{a}')
                boxes.append(box)
            fig.text(.665,.85,'Modèle · variante / moteur · effort',fontsize=10,fontweight='bold')
            for i,a in enumerate(nodes):
                label=LABELS[a].split('\n')
                description=label[0]+'\n'+label[1]+' · '+label[2]
                color='#ea580c' if not snapshot['arms'][a]['final'] else '#2563eb' if a in analysis.LOCAL else '#059669'
                fig.text(.665,.81-i*.041,a+('*' if not snapshot['arms'][a]['final'] else ''),fontsize=9,fontweight='bold',color=color,va='top')
                fig.text(.70,.81-i*.041,description,fontsize=7.4,va='top',linespacing=1.1,fontweight='bold' if a in frontier else 'normal')
            fig.text(.045,.08,'Cercle doré + nom complet : frontière de Pareto sur ces deux axes (identités complètes, qualité médiane ≥ 15/30).',fontsize=8)
            fig.text(.045,.045,'Bleu : local ; vert : hébergé ; orange / creux / * : provisoire. Coût et durée en échelle logarithmique.\n'
                     'Coût local = électricité seule ; coût hébergé = API. Les graphiques de significativité utilisent uniquement les identités complètes.',fontsize=8)
            pdf.savefig(fig);fig.savefig(output/f'{name}.png',dpi=160);plt.close(fig)
        fig=plt.figure(figsize=(11.6929,8.2677));fig.text(.06,.91,'Méthode et périmètre',fontsize=20,fontweight='bold')
        paragraphs=[
            f"Instantané UTC : {snapshot['generated_at']}. Cycles additifs : 17 identités, 10 tickets par identité.\nSpaceBunny et les essais préliminaires 0188 sont exclus. Les bras en rejeu sont isolés et marqués provisoires.",
            'Unité statistique : le ticket (au plus 10 paires), pas les trois juges.\nQualité : somme des trois notes /30 ; DNF et soumission vide admissible = 0.\nVitesse : durée consommée ; un DNF au plafond garde ses 7 200 secondes.\nCoût : API consommée, ou électricité locale à 0,23 EUR/kWh × 600 W, convertie à 1,08 USD/EUR.\nLe coût local exclut matériel et amortissement : ce sont des coûts marginaux différents.',
            'Test : Wilcoxon des rangs signés, bilatéral ; permutations exhaustives des signes (2^m).\nDifférences nulles exclues, rangs ex æquo moyens, arrondi des différences à 9 décimales.\nHypothèse : différences indépendantes entre tickets et symétriques autour de zéro sous H0.\nLa direction suit la somme des rangs signés ; aucune flèche tirée d’une simple différence de médianes.',
            'Les pages principales utilisent p < 0,05 par comparaison. Les p ajustés de Holm, par axe,\nsont fournis dans le CSV ; les comptes ajustés figurent au bas des graphes. Avec 10 tickets\net de nombreuses paires, la correction est peu puissante. Pas de flèche ne signifie pas égalité.',
            'Réduction transitive : supprimer uniquement les liens déjà reliés par un autre chemin ;\nconserver toutes les comparaisons directes dans le CSV. La significativité n’est pas transitive.\nLes cycles, s’ils existent, restent visibles à l’intérieur de leurs composantes fortement connexes.',
            'Les erreurs fournisseur/quota restent invalides et nécessitent un rejeu. Aucun score de modèle\nn’est déduit de ces erreurs. Instantané provisoire tant que GLM Flash et Mimo ne sont pas complets.\nSource statistique : docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html',
        ]
        y=.83
        for text in paragraphs:
            fig.text(.06,y,text,fontsize=10,va='top',linespacing=1.6);y-=.115 if len(text.splitlines())<=3 else .175
        pdf.savefig(fig);plt.close(fig)
    allrows=[r for result in results.values() for r in result['comparisons']]
    with (output/'comparisons.csv').open('w') as out:
        writer=csv.DictWriter(out,fieldnames=list(allrows[0]));writer.writeheader();writer.writerows(allrows)
    (output/'tests.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arena',type=Path,default=Path.home()/'arena')
    parser.add_argument('--output',type=Path,default=Path('docs/tournament-graphs'))
    parser.add_argument('--snapshot',type=Path,help='Render from a frozen cleared snapshot, without accessing arena transcripts')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if args.snapshot:
        snapshot=json.loads(args.snapshot.read_text())
    else:
        summary=analysis.analyze(args.arena)
        snapshot={'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'arms':summary['arms'], 'legs':{}}
        for arm in summary['arms']:
            legs={}
            for directory in sorted((args.arena/'runs').glob(f'*-{arm}')):
                if directory.name.startswith('0188-'):continue
                row=analysis.read_leg(directory,arm)
                if row['state'] in {'ok','failure'}:legs[directory.name.rsplit('-',1)[0]]=row
            snapshot['legs'][arm]=legs
    (args.output/'snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    results=render(args.output,snapshot)
    for axis,r in results.items():print(axis,len(r['edges']),'significant;',len(r['reduced']),'shown;',len(r['holm_edges']),'Holm')


if __name__=='__main__':main()
