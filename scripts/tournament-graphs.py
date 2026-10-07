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
from matplotlib.font_manager import FontProperties
import numpy as np
from scipy.stats import rankdata

def wrap_paragraph(fig, text, fontsize, width=.88):
    """Wrap prose to the available physical width of the landscape page."""
    renderer = fig.canvas.get_renderer()
    font = FontProperties(size=fontsize)
    limit = fig.bbox.width * width
    lines, line = [], ''
    for word in text.split():
        candidate = f'{line} {word}' if line else word
        if line and renderer.get_text_width_height_descent(candidate, font, False)[0] > limit:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return '\n'.join(lines)


spec = importlib.util.spec_from_file_location('analysis', Path(__file__).with_name('tournament-analysis.py'))
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
DASHED_MODELS = {'c', 'c2', 'e', 'mr'}
AXIS_WORDS = {'quality': ('Juste', 'Faux'), 'seconds': ('Rapide', 'Lent'), 'cost_usd': ('Abordable', 'Cher')}
DISPLAY_CODES = {'mr': 'mβ'}
LABELS = {
'mi': 'Mistral Large 4 · Idéal\nAPI Mistral + OR (0874)\noff',
'mr': 'Mistral Large 4 · beta\nAPI Mistral + OR (0874)\noff',
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


def pareto_xy(arms, xkey, ykey, quality_key="quality_median"):
    """Two-axis frontier of complete identities; quality up, resources down."""
    eligible = {a: r for a, r in arms.items() if r['final'] and r.get(quality_key) is not None and r[quality_key] >= 15
                and r.get(xkey) is not None and r.get(ykey) is not None}
    def dominates(x, y):
        advantages = [(x[k] - y[k]) * (1 if k in {'quality_median', 'quality_mean'} else -1) for k in [xkey, ykey]]
        return all(v >= 0 for v in advantages) and any(v > 0 for v in advantages)
    return {a for a, r in eligible.items() if not any(dominates(other, r) for b, other in eligible.items() if b != a)}


def total_cost_median(legs, hourly_usd):
    costs = [r['cost_usd'] + hourly_usd * r['seconds'] / 3600
             for r in legs.values() if r.get('cost_usd') is not None and r.get('seconds') is not None]
    return statistics.median(costs) if costs else None


def render(output, snapshot):
    nodes = sorted(snapshot['arms'])
    source_text = f"Source: minh.ha-duong@cnrs.fr, {snapshot['generated_at'][:10]}"
    hourly_usd = snapshot.get('time_value_usd_per_erg_hour', 1.0)
    for arm in nodes:
        legs = snapshot['legs'][arm]
        for metric in ['quality', 'seconds', 'cost_usd']:
            values = [r[metric] for r in legs.values() if r.get(metric) is not None]
            snapshot['arms'][arm][metric+'_mean'] = statistics.mean(values) if values else None
        totals = [r['cost_usd'] + hourly_usd*r['seconds']/3600 for r in legs.values()
                  if r.get('cost_usd') is not None and r.get('seconds') is not None]
        snapshot['arms'][arm]['total_cost_usd_mean'] = statistics.mean(totals) if totals else None
        totals_eur = [r['cost_usd']/1.08 + .10*r['seconds']/3600 for r in legs.values()
                      if r.get('cost_usd') is not None and r.get('seconds') is not None]
        snapshot['arms'][arm]['total_cost_eur_010_mean'] = statistics.mean(totals_eur) if totals_eur else None
    (output/'total-cost.json').write_text(json.dumps({'time_value_usd_per_erg_hour': hourly_usd, 'means': {a: snapshot['arms'][a]['total_cost_usd_mean'] for a in nodes}}, indent=2)+'\n')
    (output/'total-cost-010-eur.json').write_text(json.dumps({'time_value_eur_per_erg_hour': .10, 'usd_per_eur': 1.08, 'means': {a: snapshot['arms'][a]['total_cost_eur_010_mean'] for a in nodes}}, indent=2)+'\n')
    dag_nodes = [a for a in nodes if a not in {'c', 'c2', 'e'}]
    results = {}
    for metric, (title, direction, units) in AXES.items():
        rows = []
        for a, b in itertools.combinations(dag_nodes, 2):
            if not snapshot['arms'][a]['final'] or not snapshot['arms'][b]['final']:
                continue
            common = sorted(set(snapshot['legs'][a]) & set(snapshot['legs'][b]))
            differences = [direction * (snapshot['legs'][a][t][metric] - snapshot['legs'][b][t][metric])
                           for t in common if snapshot['legs'][a][t][metric] is not None and snapshot['legs'][b][t][metric] is not None]
            if not differences:
                continue
            paired = [(snapshot['legs'][a][t][metric], snapshot['legs'][b][t][metric])
                      for t in common if snapshot['legs'][a][t][metric] is not None
                      and snapshot['legs'][b][t][metric] is not None]
            mean_a = statistics.mean(x for x,y in paired)
            mean_b = statistics.mean(y for x,y in paired)
            effect = abs(mean_a-mean_b) if metric == 'quality' else abs(float(np.log(max(mean_a,1e-12)/max(mean_b,1e-12))))
            p, sign = signed_rank(differences)
            rows.append({'axis': metric, 'a': a, 'b': b, 'n': len(differences), 'p': p,
                         'winner': a if sign > 0 else b if sign < 0 else '',
                         'loser': b if sign > 0 else a if sign < 0 else '',
                         'effect_intensity': effect, 'median_advantage': statistics.median(differences) * sign})
        holm(rows)
        edges = {(r['winner'], r['loser']) for r in rows if r['p'] < .05 and r['winner']}
        reduced, groups = reduce_edges(dag_nodes, edges)
        for r in rows:
            r['shown'] = (r['winner'], r['loser']) in reduced and r['p'] < .05
        scale = float(np.percentile([r['effect_intensity'] for r in rows if r['shown']],95)) if reduced else 1
        for r in rows:
            r['line_width'] = .45 + 1.05*min(1,r['effect_intensity']/max(scale,1e-12))
        results[metric] = {'comparisons': rows, 'edges': sorted(edges), 'reduced': sorted(reduced),
                           'holm_edges': [(r['winner'], r['loser']) for r in rows if r['p_holm'] < .05]}
        dot = ['digraph G {', 'rankdir=TB;', 'node [shape=box, fontname="DejaVu Sans"];']
        for a in dag_nodes:
            label = LABELS[a] + ('\nPROVISOIRE' if not snapshot['arms'][a]['final'] else '')
            style = ', style="dashed"' if a in DASHED_MODELS else ''
            dot.append(f'{a} [label={json.dumps(label, ensure_ascii=False)}{style}];')
        for a, b in sorted(reduced):
            r = next(r for r in rows if r['winner'] == a and r['loser'] == b)
            dot.append(f'{a} -> {b} [label="p={r["p"]:.4f}; n={r["n"]}", penwidth={r["line_width"]:.3f}];')
        dot.append('}')
        (output / f'{metric}.dot').write_text('\n'.join(dot)+'\n')
    with PdfPages(output / 'comparaisons-modeles.pdf', metadata={'Title': 'Qualité, vitesse et coût des LLM pour la recherche', 'Author': 'Minh Ha Duong', 'Subject': 'Qualité, vitesse et coût ; réduction transitive'}) as pdf:
        fig=plt.figure(figsize=(11.6929,8.2677))
        fig.text(.06,.91,'Qualité, vitesse et coût des LLM pour la recherche',fontsize=22,fontweight='bold')
        fig.text(.06,.85,f'Intercomparaison avec Pi, sur des tickets de projets utilisant Imperial Dragon Harness\n{snapshot["generated_at"][:10]}',fontsize=12)
        fig.text(.06,.045,'minh.ha-duong@cnrs.fr',fontsize=12)
        fig.text(.06,.78,'Dix tickets tirés au hasard dans l’historique des projets de l’auteur.\nDes modèles locaux et hébergés reprennent les mêmes tâches ; trois juges notent les résultats sur 30.\nNous comparons leur qualité, leur durée et leur coût, ainsi que le poids des incidents et des reprises.',
                 fontsize=12,linespacing=1.6,va='top')
        findings=[
            ('Vainqueur du tournoi : Luna 6 medium', 'Luna 6 medium fait jeu égal avec Sol 6.1 low en qualité et vitesse, en moins cher. Limite : la mesure mélange orchestration-codage-revue.'),
            ('Qwen 3.8 Flash-Next xhigh avec Strata domine en non-interactif', 'Pour les tâches non interactives, Qwen 3.8 Flash-Next à effort xhigh, exécuté localement avec Strata, domine ce comparatif.'),
            ('Qwen 3.8 local atteint la qualité des modèles commerciaux hébergés', 'Qwen 3.8 progresse nettement par rapport à Qwen 3.6. Sur ces dix tâches, il atteint en local la qualité des modèles commerciaux hébergés. Cette comparaison utilise toutefois un effort xhigh pour Qwen, contre medium pour les modèles commerciaux de référence. Ce réglage privilégie la qualité au prix d’une verbosité accrue, donc d’une durée plus longue.'),
            ('La lenteur et la sérialisation sur GPU limitent l’interactif en local', 'Sur la workstation de test, la lenteur et la nécessité de sérialiser les tâches sur les GPU limitent fortement l’usage interactif, tandis que les API permettent des flux de travail fortement parallélisés. Les attentes portent sur les modèles locaux éventuellement dérivés de Qwen 4 et Mistral 4, les mises à niveau du matériel et les optimisations quotidiennes du runtime, qui pourraient atténuer ces contraintes.'),
            ('Mistral Large 4 : qualité prometteuse, fiabilité encore pénalisante', 'Mistral Large 4, annoncé le 6 octobre 2026, est prometteur en qualité, mais les incidents d’hébergement et les boucles observées dans son intégration au runtime Pi pénalisent encore sa fiabilité, sa vitesse et son coût.')]
        y=.65
        for heading,text in findings:
            fig.text(.06,y,heading,fontsize=13,fontweight='bold',va='top')
            text = wrap_paragraph(fig, text, 10.5)
            fig.text(.06,y-.03,text,fontsize=10.5,va='top',linespacing=1.35)
            y-=.065 + .025 * len(text.splitlines())
        fig.text(.045,.015,source_text,fontsize=8,color='#475569');pdf.savefig(fig);plt.close(fig)
        scatter_axes = [
            ('quality-cost', 'Qualité / coût', 'cost_usd_mean', 'quality_mean',
             'Coût moyen (USD)', 'Qualité moyenne (/30)'),
            ('quality-speed', 'Qualité / vitesse', 'seconds_mean', 'quality_mean',
             'Durée moyenne (minutes)', 'Qualité moyenne (/30)'),
            ('speed-cost', 'Vitesse / coût', 'cost_usd_mean', 'seconds_mean',
             'Coût moyen (USD)', 'Durée moyenne (minutes)'),
            ('quality-total-cost', f'Qualité / coût total — temps à {hourly_usd:g} USD/(erg·h)', 'total_cost_usd_mean', 'quality_mean',
             'Coût total moyen (USD / erg ; coût direct + délai valorisé)', 'Qualité moyenne (/30)'),
            ('quality-total-cost-010-eur', 'Qualité / coût total — temps à 0,10 EUR/(erg·h)', 'total_cost_eur_010_mean', 'quality_mean',
             'Coût total moyen (EUR / erg ; coût direct + durée valorisée)', 'Qualité moyenne (/30)'),
        ]
        for name, title, xkey, ykey, xlabel, ylabel in scatter_axes:
            fig=plt.figure(figsize=(11.6929,8.2677))
            ax=fig.add_axes([.08,.16,.54,.66])
            fig.suptitle(title,fontsize=20,fontweight='bold',x=.045,ha='left')
            fig.text(.045,.89,'Identités modèle × variante × effort · qualité, coût et durée moyens par ticket, échecs inclus',fontsize=10)
            entries=[]
            frontier=pareto_xy(snapshot['arms'],xkey,ykey,quality_key='quality_mean')
            for a in nodes:
                row=snapshot['arms'][a]
                if row[xkey] is None or row[ykey] is None:continue
                x=row[xkey]/60 if xkey == 'seconds_mean' else row[xkey]
                y=row[ykey]/60 if ykey == 'seconds_mean' else row[ykey]
                color={'mi':'#7c3aed','mr':'#dc2626'}.get(a, '#2563eb' if a in analysis.LOCAL else '#059669')
                provisional=not row['final']
                # Concentric distinct markers preserve exact coordinates when medians coincide.
                marker = {'mi':'D','mr':'o'}.get(a, 'o' if a in analysis.LOCAL else 's')
                size = {'mi':65,'mr':190}.get(a,65)
                ax.scatter(x,y,s=size,marker=marker,
                           facecolors='none' if provisional or a == 'mr' else color,
                           edgecolors=color if a in {'mi','mr'} else '#ea580c' if provisional else color,
                           linewidths=1.7 if a in {'mi','mr'} else 1,
                           linestyles='-',zorder=4 if a == 'mi' else 3)
                if a in frontier:
                    ax.scatter(x,y,s=210,facecolors='none',edgecolors='#b45309',linewidths=1.8,zorder=2)
                entries.append((a,x,y,color,provisional))
            if xkey in {'cost_usd_mean','total_cost_usd_mean','total_cost_eur_010_mean','seconds_mean'}:ax.set_xscale('log')
            if ykey == 'seconds_mean':
                ax.set_yscale('log')
                ax.invert_yaxis()
            if ykey == 'quality_mean':ax.set_ylim(0,32)
            ax.margins(x=.17,y=.15);ax.grid(alpha=.2,which='both');ax.set_xlabel(xlabel,fontsize=10);ax.set_ylabel(ylabel,fontsize=10)
            # Horizontal endpoint cues follow the actual direction of each axis.
            endpoint_words = {'quality_mean': ('Faux', 'Juste'),
                              'seconds_mean': ('Rapide', 'Lent'),
                              'cost_usd_mean': ('Abordable', 'Cher'),
                              'total_cost_usd_mean': ('Abordable', 'Cher'),
                              'total_cost_eur_010_mean': ('Abordable', 'Cher')}
            left, right = endpoint_words[xkey]
            ax.text(0, -.055, left, transform=ax.transAxes, ha='left', va='top', fontsize=9, rotation=0)
            ax.text(1, -.055, right, transform=ax.transAxes, ha='right', va='top', fontsize=9, rotation=0)
            bottom, top = endpoint_words[ykey]
            if ax.yaxis_inverted():
                bottom, top = top, bottom
            ax.text(-.012, -.02, bottom, transform=ax.transAxes, ha='right', va='bottom', fontsize=9, rotation=0)
            ax.text(-.012, 1.02, top, transform=ax.transAxes, ha='right', va='top', fontsize=9, rotation=0)
            # Deterministic label placement in display coordinates, with leader lines.
            fig.canvas.draw(); renderer=fig.canvas.get_renderer(); boxes=[]
            point_boxes=[]
            for _,x,y,_,_ in entries:
                px,py=ax.transData.transform((x,y))
                point_boxes.append(Bbox.from_extents(px-13,py-13,px+13,py+13))
            bounds=ax.get_window_extent(renderer)
            for a,x,y,color,provisional in sorted(entries,key=lambda item:(not (name == 'quality-speed' and item[0] == 'b2'),item[0] not in frontier,item[2],item[1])):
                annotation=None
                offsets=[(dx,dy) for radius in range(15,226,10)
                         for dx,dy in [(radius,radius),(-radius,radius),(radius,-radius),(-radius,-radius),
                                       (0,radius),(0,-radius),(radius,0),(-radius,0),
                                       (radius/2,radius),(-radius/2,radius),(radius/2,-radius),(-radius/2,-radius)]]
                if name in {'quality-cost', 'quality-speed', 'quality-total-cost', 'quality-total-cost-010-eur'} and a in {'c', 'c2'}:
                    preferred = [(22, 20), (30, 28)] if a == 'c' else [(-22, -20), (-30, -28)]
                    offsets = preferred + offsets
                if name == 'quality-speed' and a == 'b2':
                    offsets = [(45,35),(55,45),(65,55)] + [(dx,dy) for dx,dy in offsets if dx > 0 and dy > 0]
                if name == 'quality-speed' and a == 'e2':
                    offsets = [(-45, 55), (-55, 70), (-65, 85), (-85, 100)] + offsets
                if a in {'mi','mr'}:
                    offsets = ([(0,35),(0,50),(-55,35)] if a == 'mi' else [(0,-35),(0,-50),(55,-35)]) + offsets
                placed=False
                for dx,dy in offsets:
                    if annotation:annotation.remove()
                    label=(DISPLAY_CODES.get(a,a)+' · '+LABELS[a]) if a in frontier else {'mi':'Mistral Idéal','mr':'Mistral beta'}.get(a,DISPLAY_CODES.get(a,a))+("*" if provisional else "")
                    annotation=ax.annotate(label,(x,y),xytext=(dx,dy),textcoords='offset points',
                                           fontsize=7 if a in frontier else 9,ha='center',va='center',
                                           color=color if a in {'mi','mr'} else '#92400e' if a in frontier else '#ea580c' if provisional else color,
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
                color={'mi':'#7c3aed','mr':'#dc2626'}.get(a, '#ea580c' if not snapshot['arms'][a]['final'] else '#2563eb' if a in analysis.LOCAL else '#059669')
                fig.text(.665,.81-i*min(.041, .72/len(nodes)),DISPLAY_CODES.get(a,a)+('*' if not snapshot['arms'][a]['final'] else ''),fontsize=9,fontweight='bold',color=color,va='top')
                fig.text(.70,.81-i*min(.041, .72/len(nodes)),description,fontsize=7.4,va='top',linespacing=1.1,fontweight='bold' if a in frontier else 'normal')
            if name == 'quality-total-cost-010-eur':
                fig.text(.045,.855,'Par erg moyen : coût direct en USD / 1,08 + 0,10 × durée / 3 600 (secondes) ; puis moyenne. DNF inclus.',fontsize=8)
            if name == 'quality-total-cost':
                fig.text(.045,.855,f'Par erg moyen : coût total = coût direct + {hourly_usd:g} × durée / 3 600 ; puis moyenne. Durée en secondes, DNF inclus.',fontsize=8)
            fig.text(.045,.045,'Bleu : local ; vert : hébergé ; orange / creux / * : provisoire. Mistral : losange violet = Idéal, cercle rouge = beta. Coût et durée en échelle logarithmique.\n'
                     'Coût local = électricité seule ; coût hébergé = API.',fontsize=8)
            fig.text(.045,.015,source_text,fontsize=8,color='#475569');pdf.savefig(fig);fig.savefig(output/f'{name}.png',dpi=160);plt.close(fig)
        for metric, (title, direction, units) in AXES.items():
            edges = set(map(tuple, results[metric]['reduced']))
            _, groups = reduce_edges(dag_nodes, edges)
            membership = {v: i for i, g in enumerate(groups) for v in g}
            ranks = dict.fromkeys(range(len(groups)), 0)
            for _ in range(len(groups)):
                for a, b in edges:
                    if membership[a] != membership[b]:
                        ranks[membership[b]] = max(ranks[membership[b]], ranks[membership[a]] + 1)
            layers = {}
            for a in dag_nodes:
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
            best, worse = AXIS_WORDS[metric]
            fig.text(.045,.89,f'{best} en haut · flèche vers {worse} · Wilcoxon apparié exact · p < 0,05 bilatéral',fontsize=10)
            widths = {(r['winner'],r['loser']):r['line_width'] for r in results[metric]['comparisons']}
            for a, b in sorted(edges):
                ax.add_patch(FancyArrowPatch(positions[a], positions[b], arrowstyle='-|>', mutation_scale=9,
                                            color='#64748b', linewidth=widths[a,b], shrinkA=32, shrinkB=34,
                                            connectionstyle='arc3,rad=0.04', zorder=1))
            for a, (x,y) in positions.items():
                provisional = not snapshot['arms'][a]['final']
                ax.text(x,y,LABELS[a]+ ('\nPROVISOIRE' if provisional else ''),ha='center',va='center',fontsize=7.3,
                        bbox={'boxstyle':'round,pad=.4','facecolor':'#fff7ed' if provisional else '#eff6ff',
                              'edgecolor':'#ea580c' if provisional else '#2563eb','linestyle':'--' if provisional or a in DASHED_MODELS else '-'},zorder=2)
            ax.set_xlim(-.015,1.015);ax.set_ylim(-.02,1.02);ax.axis('off')
            summary=results[metric]
            fig.text(.045,.075,'Ces flèches sont significatives deux à deux ; dix tickets ne suffisent pas à garantir le classement complet à 95 %.',fontsize=9)
            fig.text(.045,.045,'L’épaisseur des flèches traduit l’intensité de l’effet. Absence de flèche ≠ équivalence.\n'
                     'Un chemin indirect ne constitue pas un nouveau test significatif. Détails p et n dans le CSV et les fichiers DOT.',fontsize=8)
            fig.text(.045,.015,source_text,fontsize=8,color='#475569');pdf.savefig(fig);fig.savefig(output/f'{metric}.png',dpi=160);plt.close(fig)
        fig=plt.figure(figsize=(11.6929,8.2677));fig.text(.06,.91,'Méthode et périmètre',fontsize=20,fontweight='bold')
        paragraphs=[
            "Échantillon aléatoire de 10 tickets tiré dans l’historique des projets de l’auteur.\nChaque modèle reprend les mêmes tâches depuis leur état antérieur à la résolution,\navec les consignes du projet et une limite de deux heures par tentative.",
            "Pi fournit le runtime d’agent : accès au modèle, appels d’outils et gestion de la session. Les tickets proviennent de projets utilisant Imperial Dragon Harness (IDH). Le prompt demande de respecter les consignes historiques de chaque dépôt (AGENTS.md, tickets/AGENTS.md et règles associées). Pour évaluer chaque modèle séparément, le tournoi désactive les revues externes et les panels Gaze, review-pr et verify-gate : le modèle réalise les tâches, exécute les contrôles mécaniques et effectue sa propre revue. Les trois juges interviennent seulement après la réalisation. Il s’agit donc d’une évaluation avec Pi et les consignes des projets, pas du workflow IDH complet.",
            "Notation des résultats sur 30 selon le système de la boxe : trois juges partent de 10\net déduisent des points pour les fautes selon leur sévérité : −3, −2, −1 ou −0,5 point.\nLes juges examinent le travail sans connaître le modèle qui l’a produit. Une absence\nde résultat exploitable vaut zéro ; une impossibilité correctement expliquée est jugée normalement.",
            "Le juge principal est Gemini 3.1 Pro Preview ; les deux autres sont Grok 4.3 et MiniMax M2.5.\nLes résultats conservés du premier cycle ont été jugés par Gemini 3.1 Pro Preview,\nDeepSeek V4 Pro et Kimi K3. Les notes sont additionnées, sans pondération entre juges.",
            "Les modèles locaux tournent sur une Lenovo ThinkStation P620 : Ryzen Threadripper PRO\n3945WX, 128 Go de RAM, deux GPU RTX A4000 + RTX 3060 (28 Go de VRAM au total).\nLe coût local estime l’électricité à 600 W et 0,23 €/kWh, sans amortissement du matériel.\nLes coûts API sont ceux des tokens consommés ; conversion commune : 1,08 USD pour 1 EUR.",
            "Les nuages de points présentent les moyennes par ticket de qualité, durée et coût.\nChaque ticket représente un erg moyen. La valeur du délai est exprimée par erg et par heure, en USD/(erg·h) ou EUR/(erg·h), et non comme un salaire horaire.\nMistral Idéal retient le dernier résultat réussi de chaque ticket. Mistral beta additionne\nles coûts et durées de tous ses essais, interruptions comprises, et garde la meilleure note.\nSes coûts sont répartis selon les tokens facturés ; les nouveaux essais restent estimés.\nLa frontière de Pareto exclut les séries incomplètes et les qualités moyennes inférieures à 15/30.",
            "Sur les trois graphes acycliques, les flèches comparent les résultats\nticket par ticket par un test de Wilcoxon apparié, bilatéral, au seuil de 5 %.\nElles vont vers le résultat moins juste, plus lent ou plus cher.\nLes flèches redondantes par transitivité sont retirées pour faciliter la lecture.\nL’absence de flèche ne prouve pas l’équivalence ; un chemin indirect n’est pas un test supplémentaire.",
            "Le seuil de 5 % vaut pour chaque comparaison, sans garantie simultanée pour tout le graphe.\nLa correction de Holm contrôle le risque de faux positifs lié aux comparaisons multiples.\nAvec dix tickets, aucune différence ne franchit ce seuil plus exigeant : les écarts détectés\ndeux à deux ne constituent donc pas un classement global garanti à 95 %.\nLes astérisques signalent les séries provisoires ; Mistral beta a un contour pointillé dans les DAG.\nQwen 3, Qwen 3.6 et GPT-6 Sol figurent seulement dans les nuages de points.",
        ]
        paragraphs.append("Limite : cette évaluation confie à un seul modèle l’ensemble du travail : orchestration,\nréalisation et revue de sa propre production. Elle mesure donc sa capacité à mener\nune tâche de bout en bout, plutôt que les performances d’un harnais qui choisit\ndifférents modèles selon les rôles et confie les revues à des modèles distincts pour\nréduire les erreurs corrélées. Les trois juges externes évaluent le résultat final ;\nils ne participent pas à sa réalisation.")
        paragraphs.append("Limite : sur le ticket 0874, la dernière tentative directe avec Mistral a atteint le plafond de deux heures, malgré 195 réponses API réussies. Le modèle a longuement exploré le projet puis multiplié les tests, avec des modules et un hook manquants dans l’environnement. Le disjoncteur de répétitions identiques ne détecte pas cette dérive à commandes variables. Le résultat réussi via OpenRouter remplace ce ticket dans la série idéale ; Mistral beta conserve les coûts et durées des tentatives directes échouées et ajoute ceux du remplacement. La série Mistral combine donc deux filières d’hébergement. Le coût OpenRouter est celui enregistré pour ce run ; les coûts directs suivent la calibration de la facture Mistral.")
        paragraphs.append("La sélection des candidats est purement ad hoc, sans prétention à l’exhaustivité.\nQuels modèles, variantes ou runtimes souhaiteriez-vous voir dans le prochain comparatif ?\nVos suggestions et retours sont bienvenus à minh.ha-duong@cnrs.fr.")
        y=.84
        for index,text in enumerate(paragraphs):
            if index == 6:
                fig.text(.045,.015,source_text,fontsize=8,color='#475569');pdf.savefig(fig);plt.close(fig)
                fig=plt.figure(figsize=(11.6929,8.2677))
                fig.text(.06,.91,'Méthode : comparaisons et limites',fontsize=20,fontweight='bold')
                y=.84
            text = wrap_paragraph(fig, text, 9.5)
            fig.text(.06,y,text,fontsize=9.5,va='top',linespacing=1.35)
            y-=len(text.splitlines())*.0215+.023
            if index == 5:
                fig.text(.06,y,'• Pi : github.com/earendil-works/pi',fontsize=9,color='#2563eb',va='top',url='https://github.com/earendil-works/pi')
                fig.text(.06,y-.03,'• IDH : github.com/MinhHaDuong/ImperialDragonHarness',fontsize=9,color='#2563eb',va='top',url='https://github.com/MinhHaDuong/ImperialDragonHarness')
                y-=.07
        fig.text(.045,.015,source_text,fontsize=8,color='#475569');pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(11.6929,8.2677))
        fig.text(.06,.92,'Annexe : résultats par modèle',fontsize=20,fontweight='bold')
        columns=['Modèle · variante / moteur · effort','Réussis / 10','Qualité\nmoyenne /30','Durée moyenne\n(min / ticket)','Coût moyen\n(USD / ticket)']
        table_rows=[]
        for arm in nodes:
            row=snapshot['arms'][arm]
            parts=LABELS[arm].split('\n')
            identity=DISPLAY_CODES.get(arm,arm)+' · '+parts[0]+'\n'+parts[1]+' · '+parts[2]
            def display(value):
                return '—' if value is None else f'{value:.2f}'.replace('.', ',')
            table_rows.append([identity,f'{row["ok"]} / {row["expected"]}',display(row['quality_mean']),
                               display(row['seconds_mean']/60 if row['seconds_mean'] is not None else None),display(row['cost_usd_mean'])])
        ax=fig.add_axes([.06,.16,.88,.68]);ax.axis('off')
        table=ax.table(cellText=table_rows,colLabels=columns,colWidths=[.49,.10,.12,.145,.145],cellLoc='center',bbox=[0,0,1,1])
        table.auto_set_font_size(False);table.set_fontsize(8)
        for (r,c),cell in table.get_celld().items():
            cell.set_edgecolor('#cbd5e1');cell.set_linewidth(.5)
            if r == 0:
                cell.set_facecolor('#e2e8f0');cell.set_text_props(weight='bold')
            else:
                cell.set_facecolor('#f8fafc' if r % 2 else 'white')
                if c == 0:cell.set_text_props(ha='left')
        note='Moyennes par ticket, échecs inclus ; les séries incomplètes portent sur les tickets évalués. Coût local : électricité seule. Mistral Idéal : dix succès, dont 0874 via OpenRouter. Mistral beta : mêmes notes, coûts et durées de toutes les tentatives directes, plus le remplacement OR de 0874. « Réussis » compte les tickets livrés, pas le nombre de tentatives.'
        fig.text(.06,.12,wrap_paragraph(fig,note,9),fontsize=9,va='top',linespacing=1.35)
        fig.text(.045,.015,source_text,fontsize=8,color='#475569');pdf.savefig(fig);plt.close(fig)
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
    parser.add_argument('--time-value', type=float, default=1.0, help='USD per erg-hour of delivery delay; each benchmark ticket represents one average erg')
    args=parser.parse_args()
    if args.time_value < 0:parser.error('time value must be nonnegative')
    args.output.mkdir(parents=True,exist_ok=True)
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
    if not args.snapshot:
        mspec = importlib.util.spec_from_file_location('mistral_series', Path(__file__).with_name('tournament-mistral-series.py'))
        mistral = importlib.util.module_from_spec(mspec)
        mspec.loader.exec_module(mistral)
        mistral.add_series(snapshot, args.arena)
    snapshot['time_value_usd_per_erg_hour'] = args.time_value
    (args.output/'snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    results=render(args.output,snapshot)
    (args.output/'snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    for axis,r in results.items():print(axis,len(r['edges']),'significant;',len(r['reduced']),'shown;',len(r['holm_edges']),'Holm')


if __name__=='__main__':main()
