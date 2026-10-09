#!/usr/bin/env python3
"""Append the ticket-1046 analyses to the FR/EN report from cleared inputs only."""

import csv
import itertools
import json
import math
import re
import statistics

import matplotlib.pyplot as plt

PAIRS = [
    ("H1", "e2", "g"),
    ("H2-a", "l", "a"),
    ("H2-b", "l", "b"),
    ("H2-b2", "l", "b2"),
    ("H2-b3", "l", "b3"),
    ("H2-c", "l", "c"),
    ("H2-c2", "l", "c2"),
    ("Sol effort", "e2", "e3"),
    ("Opus effort", "d2", "d"),
    ("Local / hosted", "b2", "e3"),
    ("GLM / Flash", "f", "j"),
    ("IQ3_S / Q2_0", "b2", "b3"),
    ("Haiku / Sonnet", "n", "g"),
]
CLUSTERS = {
    "ASSURANCE": ["d"],
    "MILIEU SOLIDE": ["e2", "e3", "g", "f"],
    "ECONOMIQUES": ["l", "n", "i", "j", "k"],
    "LOCAL-PRIVE": ["b2", "b3", "a"],
    "BANNIS": ["c", "c2"],
}


def analyze(snapshot, signed_rank, holm, original_results=None):
    """Full 20-identity family, distinct from the original 17-identity DAG family."""
    rows = []
    cached = {
        metric: {frozenset((r["a"], r["b"])): r["p"] for r in axis["comparisons"]}
        for metric, axis in (original_results or {}).items()
    }
    legs = snapshot["legs"]
    for a, b in itertools.combinations(sorted(legs), 2):
        common = sorted(set(legs[a]) & set(legs[b]))
        row = {"a": a, "b": b, "n": len(common), "tickets": common}
        q = [legs[a][t]["quality"] - legs[b][t]["quality"] for t in common]
        row.update(
            wins=sum(v > 0 for v in q),
            ties=q.count(0),
            losses=sum(v < 0 for v in q),
            quality_difference_mean=statistics.mean(q),
            quality_difference_median=statistics.median(q),
        )
        row["pareto_ticket_wins"] = sum(
            legs[a][t]["quality"] >= legs[b][t]["quality"]
            and legs[a][t]["seconds"] <= legs[b][t]["seconds"]
            and legs[a][t]["cost_usd"] <= legs[b][t]["cost_usd"]
            and any(
                legs[a][t][m] != legs[b][t][m]
                for m in ("quality", "seconds", "cost_usd")
            )
            for t in common
        )
        row["faster"] = sum(
            legs[a][t]["seconds"] < legs[b][t]["seconds"] for t in common
        )
        row["cheaper"] = sum(
            legs[a][t]["cost_usd"] < legs[b][t]["cost_usd"] for t in common
        )
        row["seconds_ratio_median"] = statistics.median(
            legs[a][t]["seconds"] / legs[b][t]["seconds"] for t in common
        )
        row["cost_ratio_median"] = statistics.median(
            legs[a][t]["cost_usd"] / legs[b][t]["cost_usd"] for t in common
        )
        row["quality_differences"] = q
        for metric in ("quality", "seconds", "cost_usd"):
            differences = [legs[a][t][metric] - legs[b][t][metric] for t in common]
            prior = cached.get(metric, {}).get(frozenset((a, b)))
            row[metric + "_p"] = signed_rank(differences)[0] if prior is None else prior
        rows.append(row)
    for metric in ("quality", "seconds", "cost_usd"):
        family = [{"p": r[metric + "_p"]} for r in rows]
        holm(family)
        for r, v in zip(rows, family):
            r[metric + "_p_holm_190"] = v["p_holm"]
    return rows


def oriented(rows, a, b, snapshot):
    row = next(r for r in rows if {r["a"], r["b"]} == {a, b})
    if row["a"] == a:
        return row
    legs = snapshot["legs"]
    common = row["tickets"]
    out = dict(
        row,
        a=a,
        b=b,
        wins=row["losses"],
        losses=row["wins"],
        quality_difference_mean=-row["quality_difference_mean"],
        quality_difference_median=-row["quality_difference_median"],
        quality_differences=[-v for v in row["quality_differences"]],
    )
    out["faster"] = sum(legs[a][t]["seconds"] < legs[b][t]["seconds"] for t in common)
    out["cheaper"] = sum(
        legs[a][t]["cost_usd"] < legs[b][t]["cost_usd"] for t in common
    )
    out["seconds_ratio_median"] = statistics.median(
        legs[a][t]["seconds"] / legs[b][t]["seconds"] for t in common
    )
    out["cost_ratio_median"] = statistics.median(
        legs[a][t]["cost_usd"] / legs[b][t]["cost_usd"] for t in common
    )
    out["pareto_ticket_wins"] = sum(
        legs[a][t]["quality"] >= legs[b][t]["quality"]
        and legs[a][t]["seconds"] <= legs[b][t]["seconds"]
        and legs[a][t]["cost_usd"] <= legs[b][t]["cost_usd"]
        and any(
            legs[a][t][m] != legs[b][t][m] for m in ("quality", "seconds", "cost_usd")
        )
        for t in common
    )
    return out


def frontier3(snapshot):
    arms = {
        a: r
        for a, r in snapshot["arms"].items()
        if r["final"] and r["quality_mean"] >= 15
    }

    def dominates(x, y):
        return (
            x["quality_mean"] >= y["quality_mean"]
            and x["seconds_mean"] <= y["seconds_mean"]
            and x["cost_usd_mean"] <= y["cost_usd_mean"]
            and any(
                x[m] != y[m] for m in ("quality_mean", "seconds_mean", "cost_usd_mean")
            )
        )

    return sorted(
        a
        for a, r in arms.items()
        if not any(dominates(v, r) for b, v in arms.items() if b != a)
    )


def french_spacing(text):
    """Bind French high punctuation, guillemets and digit groups with U+00A0."""
    text = re.sub(r" ([:;?!»])", "\u00a0\\1", text)
    text = text.replace("« ", "«\u00a0")
    return re.sub(r"(?<=\d) (?=\d{3}\b)", "\u00a0", text)


def append_report(
    pdf, snapshot, results, output, labels, signed_rank, holm, wrap, language="fr"
):
    en = language == "en"

    def tr(fr, eng):
        return eng if en else french_spacing(fr)

    def number(v, digits=2):
        text = f"{v:.{digits}f}"
        return text if en else text.replace(".", ",")

    rows = analyze(snapshot, signed_rank, holm, results)
    payload = {
        "scope": "All 190 pairs of 20 report identities, Holm separately by axis; distinct from 136-pair DAG family.",
        "selected_pairs": PAIRS,
        "comparisons": rows,
        "pareto3_mean_quality_floor15": frontier3(snapshot),
        "grid_clusters": CLUSTERS,
    }
    (output / "appendix-analysis.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
    with (output / "paired-differences.csv").open("w") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "comparison",
                "a",
                "b",
                "ticket",
                "quality_a_minus_b",
                "minutes_a_minus_b",
                "seconds_a_over_b",
                "cost_usd_a_minus_b",
                "cost_a_over_b",
            ]
        )
        for name, a, b in PAIRS:
            for ticket in sorted(snapshot["legs"][a]):
                x, y = snapshot["legs"][a][ticket], snapshot["legs"][b][ticket]
                writer.writerow(
                    [
                        name,
                        a,
                        b,
                        ticket,
                        x["quality"] - y["quality"],
                        (x["seconds"] - y["seconds"]) / 60,
                        x["seconds"] / y["seconds"],
                        x["cost_usd"] - y["cost_usd"],
                        x["cost_usd"] / y["cost_usd"],
                    ]
                )

    def page(title, subtitle=""):
        fig = plt.figure(figsize=(11.6929, 8.2677))
        title_size = 20
        while len(wrap(fig, title, title_size).splitlines()) > 1 and title_size > 14:
            title_size -= 1
        fig.text(0.06, 0.925, title, fontsize=title_size, fontweight="bold", va="top")
        if subtitle:
            fig.text(
                0.06,
                0.865,
                wrap(fig, subtitle, 10),
                fontsize=10,
                va="top",
                color="#475569",
                linespacing=1.3,
            )
        return fig

    def finish(fig, name=None):
        fig.text(
            0.045,
            0.025,
            tr(
                "Complément 1046 - 9 octobre 2026",
                "Ticket 1046 supplement - October 9, 2026",
            ),
            fontsize=8,
            color="#475569",
        )
        fig.text(
            0.955,
            0.025,
            str(pdf.get_pagecount() + 1),
            ha="right",
            fontsize=8,
            color="#475569",
        )
        pdf.savefig(fig)
        if name:
            fig.savefig(output / (name + ".png"), dpi=160)
        plt.close(fig)

    def prose(fig, blocks, y=0.78, fontsize=11):
        for heading, text in blocks:
            if heading:
                fig.text(0.06, y, heading, fontsize=13, fontweight="bold", va="top")
                y -= 0.035
            rendered = wrap(fig, text, fontsize)
            fig.text(0.06, y, rendered, fontsize=fontsize, va="top", linespacing=1.4)
            y -= len(rendered.splitlines()) * 0.026 + 0.035
        if y < 0.065:
            raise ValueError("Supplement prose overflows page")

    def table(fig, headers, data, bbox, widths=None, size=9):
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        widths = widths or [1 / len(headers)] * len(headers)
        widths = [w / sum(widths) for w in widths]
        wrapped_headers = [
            wrap(fig, str(t), size, width=bbox[2] * w * 0.86)
            for t, w in zip(headers, widths)
        ]
        wrapped_data = [
            [
                wrap(fig, str(t), size, width=bbox[2] * w * 0.86)
                for t, w in zip(row, widths)
            ]
            for row in data
        ]
        all_rows = [wrapped_headers] + wrapped_data
        heights = [max(t.count("\n") + 1 for t in row) for row in all_rows]
        if sum(heights) * size * 1.2 / 595 + len(heights) * 0.006 > bbox[3]:
            raise ValueError("Table cannot fit at readable font size")
        obj = ax.table(
            cellText=wrapped_data,
            colLabels=wrapped_headers,
            cellLoc="left",
            colLoc="left",
            bbox=bbox,
            colWidths=widths,
        )
        obj.auto_set_font_size(False)
        obj.set_fontsize(size)
        for (i, j), cell in obj.get_celld().items():
            cell.set_height(bbox[3] * heights[i] / sum(heights))
        for (i, j), cell in obj.get_celld().items():
            cell.set_edgecolor("#cbd5e1")
            cell.set_linewidth(0.4)
            cell.set_facecolor("#e2e8f0" if i == 0 else "#f1f5f9" if i % 2 else "white")
            if i == 0:
                cell.get_text().set_fontweight("bold")
        return obj

    fig = page(
        tr(
            "Analyses complémentaires et guide de choix",
            "Supplementary analyses and situation guide",
        ),
        tr(
            "Résultats figés du 8 octobre ; complément rédigé le 9 octobre. Guide relu par un relecteur délégué (Fable) à la demande de l’auteur.",
            "October 8 frozen results; supplement prepared October 9. Guide reviewed by a delegated Fable reviewer at the author’s request.",
        ),
    )
    prose(
        fig,
        [
            (
                tr("Résumé exécutif", "Executive summary"),
                tr(
                    "H1 ne se vérifie pas : Sol low n’est pas plus rapide que Sonnet medium. H2 est hétérogène : Luna a une durée moyenne inférieure aux six configurations locales, mais l’égalité de qualité n’est pas démontrée et IQ3_S garde une meilleure moyenne. Les différences d’effort ne prouvent pas une dominance de qualité. Les groupes de routage sont des choix opérationnels, pas des clusters statistiques estimés.",
                    "H1 does not hold: Sol low is not faster than Sonnet medium. H2 is mixed: Luna has lower mean time than all six local setups, but equal quality is not established and IQ3_S retains a higher mean score. Effort comparisons do not establish quality dominance. Routing groups are operational choices, not fitted statistical clusters.",
                ),
            ),
            (
                tr("Sommaire du rapport complété", "Contents of the completed report"),
                tr(
                    "Pages 1-12 : synthèse, résultats, cinq nuages, trois DAG, méthode et limites. Page 14 : grille, médianes et Pareto 3D. Pages 15-16 : verdicts appariés. Pages 17-21 : distributions de treize comparaisons. Page 22 : analyse des classes. Page 23 : événements historiques et corrections. Pages 24-25 : guide situationnel, quotas et tarification. Page 26 : provenance et couverture du ticket.",
                    "Pages 1-12: summary, results, five scatterplots, three DAGs, methods and limits. Page 14: grid, medians and 3D Pareto. Pages 15-16: paired verdicts. Pages 17-21: distributions for thirteen comparisons. Page 22: routing classes. Page 23: historical outcomes and corrections. Pages 24-25: situation guide, quotas and pricing. Page 26: provenance and ticket coverage.",
                ),
            ),
            (
                tr("Statut de diffusion", "Publication status"),
                tr(
                    "Préparé par ChatGPT puis finalisé par Claude Opus 5.5, à la demande de Ha-Duong Minh. La branche de revue est autorisée ; aucune fusion, publication du billet ou diffusion Tchap/Reddit n’est autorisée. Message : aucun classement ne survit à la correction de Holm ; choisir d’abord selon les contraintes (confidentialité, délai, budget, GPU, quotas), puis selon le compromis observé. Le guide ci-dessous n’est pas une décision de routage appliquée.",
                    "Prepared by ChatGPT, then finalized by Claude Opus 5.5, at the request of Ha-Duong Minh. A review branch is authorized; no merge, blog publication or Tchap/Reddit distribution is authorized. Message: no ranking survives Holm correction; choose by constraints first (privacy, latency, budget, GPU, quotas), then by the observed trade-off. The following guide is not an applied routing decision.",
                ),
            ),
        ],
        fontsize=11,
    )
    finish(fig)

    fig = page(
        tr(
            "Grille et frontière de Pareto en trois dimensions",
            "Grid and three-dimensional Pareto frontier",
        ),
        tr(
            "Médianes marginales : elles ne remplacent pas les différences appariées. Chaque identité comprend modèle, effort et runtime.",
            "Marginal medians do not replace paired differences. Each identity includes model, effort and runtime.",
        ),
    )
    order = list(snapshot["arms"])
    data = []
    for a in order:
        r = snapshot["arms"][a]
        # Keep concise configuration identities, resolved in the original legends.
        data.append(
            [
                a,
                labels[a].split("\n")[0],
                number(r["quality_median"]),
                number(r["quality_mean"]),
                number(r["seconds_median"] / 60),
                number(r["cost_usd_median"], 4),
            ]
        )
    table(
        fig,
        [
            tr("Série", "Arm"),
            tr("Configuration (effort : légendes)", "Setup (effort: legends)"),
            tr("Q méd.", "Q med."),
            tr("Q moy.", "Q mean"),
            tr("Min méd.", "Min med."),
            tr("USD méd.", "USD med."),
        ],
        data,
        [0.06, 0.22, 0.88, 0.56],
        [0.05, 0.44, 0.10, 0.10, 0.10, 0.11],
        8.5,
    )
    frontier = ", ".join(frontier3(snapshot))
    fig.text(
        0.06,
        0.17,
        wrap(
            fig,
            tr(
                f"Pareto 3D sur les moyennes, séries complètes avec qualité ≥15/30 : {frontier}. Une série est dominée si une autre est au moins aussi bonne en qualité, au plus aussi longue et aussi chère, avec une amélioration stricte. Il s’agit d’une frontière descriptive, sans garantie statistique.",
                f"3D Pareto on means, complete series with quality ≥15/30: {frontier}. A series is dominated when another has at least its quality and no higher time or cost, with one strict improvement. This is a descriptive frontier, without statistical guarantee.",
            ),
            10,
        ),
        fontsize=10,
        va="top",
    )
    finish(fig)

    selected = [(name, oriented(rows, a, b, snapshot)) for name, a, b in PAIRS]
    for index, subset in enumerate([selected[:7], selected[7:]]):
        fig = page(
            tr("Verdicts appariés : H1 et H2", "Paired verdicts: H1 and H2")
            if index == 0
            else tr(
                "Effort, variantes et comparaisons inter-camps",
                "Effort, variants and cross-camp comparisons",
            ),
            tr(
                "Lecture A / B : gains de qualité, égalités, pertes ; médiane ΔQ ; ratios médians A/B. Ratio <1 = moins de ressources.",
                "Read A / B: quality wins, ties, losses; median ΔQ; median A/B ratios. Ratio <1 means fewer resources.",
            ),
        )
        data = []
        for name, r in subset:
            data.append(
                [
                    name + " " + r["a"] + "/" + r["b"],
                    f"{r['wins']}/{r['ties']}/{r['losses']}",
                    number(r["quality_difference_median"]),
                    number(r["seconds_ratio_median"]),
                    number(r["cost_ratio_median"]),
                    number(r["quality_p"], 4),
                    number(r["quality_p_holm_190"], 4),
                    str(r["pareto_ticket_wins"]),
                ]
            )
        table(
            fig,
            [
                tr("Question : A/B", "Question: A/B"),
                "G/E/P" if not en else "W/T/L",
                "ΔQ",
                tr("Durée", "Time"),
                tr("Coût", "Cost"),
                "p Q",
                "Holm Q",
                tr("Dom. /10", "Dom. /10"),
            ],
            data,
            [0.06, 0.48, 0.88, 0.31],
            [0.26, 0.12, 0.10, 0.10, 0.10, 0.09, 0.11, 0.12],
            9,
        )
        blocks = (
            [
                (
                    "H1",
                    tr(
                        "Hypothèse initiale : Sol 6.1 low domine Sonnet medium sur les trois axes. Les moyennes donnent +1,30 point en qualité et un coût inférieur, mais une durée supérieure. La domination conjointe postulée n’est pas observée ; aucune équivalence ou supériorité de qualité n’est établie.",
                        "Original hypothesis: Sol 6.1 low dominates Sonnet medium on all three axes. Means show +1.30 quality points and lower cost, but longer time. The asserted joint dominance is not observed; quality equivalence or superiority is not established.",
                    ),
                ),
                (
                    "H2",
                    tr(
                        "Luna est plus rapide sur 10/10 tickets face à a, b, b2 et b3, sur 6/10 face à c et 9/10 face à c2. La qualité dépend du comparateur : sa moyenne dépasse celles des anciennes configurations, mais reste inférieure à IQ3_S. Sans marge d’équivalence préenregistrée, « qualité égale » ne peut pas être confirmé. « Coût négligeable » n’avait pas de seuil numérique.",
                        "Luna is faster on 10/10 tasks against a, b, b2 and b3, on 6/10 against c and 9/10 against c2. Quality depends on the comparator: its mean exceeds older setups but is below IQ3_S. Without a preregistered equivalence margin, equal quality cannot be confirmed. Negligible cost had no numerical threshold.",
                    ),
                ),
            ]
            if index == 0
            else [
                (
                    tr("Axes d’effort", "Effort axes"),
                    tr(
                        "Sol low et medium : les notes gagnent et perdent selon le ticket ; low est plus rapide sur 9/10 et moins cher sur 10/10. Opus low réduit durée et coût, avec une qualité moyenne inférieure (21,45 contre 23,70). Un test non significatif ne justifie pas de dire « à parité ». Les différences inter-cycles peuvent aussi mêler panel et environnement.",
                        "Sol low versus medium: quality wins and losses vary by task; low is faster on 9/10 and cheaper on 10/10. Opus low reduces time and cost, with lower mean quality (21.45 vs 23.70). A nonsignificant test does not justify parity. Cross-cycle differences may also involve panel and environment.",
                    ),
                ),
                (
                    tr("Interprétation", "Interpretation"),
                    tr(
                        "Dom. /10 compte les tickets où A est au moins aussi bon sur les trois axes avec une amélioration stricte, pas un test de supériorité. Holm Q porte ici sur toutes les 190 paires des 20 identités, séparément par axe ; les DAG originaux gardent leur famille de 136. Aucune des deux familles ne produit de différence corrigée. Les autres colonnes p sont disponibles dans appendix-analysis.json.",
                        "Dom. /10 counts tasks where A is no worse on all axes and strictly better on at least one; it is not a superiority test. Holm Q here covers all 190 pairs of 20 identities, separately by axis; original DAGs retain their 136-pair family. Neither family yields corrected differences. Other p columns are available in appendix-analysis.json.",
                    ),
                ),
            ]
        )
        prose(fig, blocks, y=0.41, fontsize=10)
        finish(fig)

    # Exactly 13 comparisons: 3 rows per page, 5 pages. Every dot is a paired ticket.
    group_starts = [0, 3, 6, 9, 11, 13]
    for group_index, (start, end) in enumerate(zip(group_starts, group_starts[1:])):
        subset = PAIRS[start:end]
        fig = page(
            tr(
                "Distributions des différences appariées",
                "Distributions of paired differences",
            ),
            tr(
                "Dix points par comparaison. ΔQ = A-B ; ressources : log2(A/B). Zéro = égalité ; à gauche = A plus rapide/moins cher.",
                "Ten points per comparison. ΔQ = A-B; resources: log2(A/B). Zero means equal; left means A faster/cheaper.",
            ),
        )
        gs = fig.add_gridspec(
            len(subset),
            3,
            left=0.10,
            right=0.96,
            top=0.77,
            bottom=0.13,
            hspace=0.6,
            wspace=0.34,
        )
        for i, (name, a, b) in enumerate(subset):
            tickets = sorted(snapshot["legs"][a])
            xs = [snapshot["legs"][a][t] for t in tickets]
            ys = [snapshot["legs"][b][t] for t in tickets]
            values = [
                [x["quality"] - y["quality"] for x, y in zip(xs, ys)],
                [math.log2(x["seconds"] / y["seconds"]) for x, y in zip(xs, ys)],
                [math.log2(x["cost_usd"] / y["cost_usd"]) for x, y in zip(xs, ys)],
            ]
            for j, v in enumerate(values):
                ax = fig.add_subplot(gs[i, j])
                ax.axvline(0, color="#94a3b8", lw=0.9)
                ax.scatter(
                    v,
                    [0.45 + 0.025 * (k % 4) for k in range(10)],
                    s=24,
                    c="#2563eb",
                    alpha=0.8,
                )
                ax.plot([statistics.median(v)] * 2, [0.34, 0.63], c="#f97316", lw=2)
                ax.set_ylim(0.2, 0.8)
                ax.set_yticks([])
                ax.grid(axis="x", alpha=0.18)
                ax.set_title(
                    [
                        tr("Qualité : ΔQ", "Quality: ΔQ"),
                        tr("Durée : log2(A/B)", "Time: log2(A/B)"),
                        tr("Coût : log2(A/B)", "Cost: log2(A/B)"),
                    ][j],
                    fontsize=9,
                )
                if j == 0:
                    ax.set_ylabel(name + "\n" + a + " / " + b, fontsize=9)
                for spine in ("top", "right", "left"):
                    ax.spines[spine].set_visible(False)
                ax.tick_params(labelsize=8)
        fig.text(
            0.06,
            0.075,
            tr(
                "Orange : médiane des différences ou des log-ratios. Données par ticket : paired-differences.csv. Aucun intervalle d’équivalence n’est estimé.",
                "Orange: median of differences or log-ratios. Per-ticket data: paired-differences.csv. No equivalence interval is estimated.",
            ),
            fontsize=9,
        )
        finish(fig, "paired-distributions-" + str(group_index + 1))

    fig = page(
        tr(
            "Classes de routage : lecture critique de la grille",
            "Routing classes: a critical reading of the grid",
        ),
        tr(
            "Groupes repris de skills/route/grid.json ; catégories opérationnelles, non issues d’un clustering statistique.",
            "Groups from skills/route/grid.json; operational categories, not fitted statistical clusters.",
        ),
    )
    data = []
    for name, arms in CLUSTERS.items():
        r = [snapshot["arms"][a] for a in arms]
        data.append(
            [
                name,
                ", ".join(arms),
                number(min(x["quality_mean"] for x in r))
                + " - "
                + number(max(x["quality_mean"] for x in r)),
                number(min(x["seconds_mean"] / 60 for x in r))
                + " - "
                + number(max(x["seconds_mean"] / 60 for x in r)),
                number(min(x["cost_usd_mean"] for x in r), 3)
                + " - "
                + number(max(x["cost_usd_mean"] for x in r), 3),
            ]
        )
    table(
        fig,
        [
            tr("Classe historique", "Historical class"),
            tr("Séries", "Arms"),
            tr("Q moy. /30", "Mean Q /30"),
            tr("Minutes moy.", "Mean minutes"),
            tr("USD moyens", "Mean USD"),
        ],
        data,
        [0.06, 0.53, 0.88, 0.25],
        [0.23, 0.22, 0.18, 0.18, 0.19],
        10,
    )
    prose(
        fig,
        [
            (
                tr(
                    "Ce que les groupes n’établissent pas",
                    "What these groups do not establish",
                ),
                tr(
                    "« Assurance » ne garantit pas la fiabilité ; « milieu solide » et « économiques » ont des moyennes de qualité qui se chevauchent. Les modèles locaux ne forment pas une famille homogène : génération, quantification et effort changent. Les libellés « bannis » sont une posture de routage de l’auteur, soutenue par de faibles notes dans ce test, pas une interdiction générale.",
                    "Assurance does not guarantee reliability; solid-middle and economical groups overlap in mean quality. Local setups are not homogeneous: generation, quantization and effort differ. The banned label is an author routing posture supported by low scores here, not a general ban.",
                ),
            ),
            (
                tr(
                    "Éléments hors classes et notices périmées",
                    "Unassigned identities and stale notices",
                ),
                tr(
                    "b, d2 et e ne sont pas affectés par ces groupes ; mL/mA sont deux périmètres d’une même extension Mistral, pas deux modèles. Les notices de j/k disent encore « rejeu en cours », alors que l’instantané courant est final avec un échec retenu chacun. Le rapport utilise l’instantané, sans modifier silencieusement la politique de routage.",
                    "b, d2 and e are not assigned to these groups; mL/mA are two accounting scopes of one Mistral extension, not two models. j/k notes still say replay underway, while the current snapshot is final with one retained failure each. The report uses the snapshot without silently changing routing policy.",
                ),
            ),
        ],
        y=0.46,
        fontsize=10,
    )
    finish(fig)

    fig = page(
        tr(
            "Les 19 événements historiques, en trois classes",
            "The 19 historical outcomes, in three classes",
        ),
        tr(
            "141/160 OK et 19 non-OK avant le rejeu b2 ; 142/160 OK et 18 non-OK ensuite. Ne pas confondre tentatives et matrice finale.",
            "141/160 OK and 19 non-OK before the b2 replay; 142/160 OK and 18 non-OK after it. Attempts are not final matrix outcomes.",
        ),
    )
    incidents = [
        (
            "DNF",
            4,
            "0874-a, 0874-b3, 0333-j, 0211-k",
            tr(
                "Plafond 7200 s ; les quatre échecs restent à zéro.",
                "7200 s cap; all four failures remain zero.",
            ),
        ),
        (
            "VOID-EMPTY",
            1,
            "0333-b2",
            tr(
                "Pause demandée pour libérer le GPU ; archivée ; rejeu 30/30.",
                "Requested pause to free GPU; archived; replay 30/30.",
            ),
        ),
        (
            "VOID-EMPTY",
            1,
            "0470-c2",
            tr(
                "Absence de livraison valide ; zéro conservé.",
                "No valid deliverable; zero retained.",
            ),
        ),
        (
            "VOID-EMPTY",
            4,
            "0233-j, 0452-j, 0874-j, 1372-j",
            tr(
                "Erreurs 403 de quota OpenRouter ; attribution au modèle retirée.",
                "OpenRouter quota 403 errors; model attribution withdrawn.",
            ),
        ),
        (
            "VOID-EMPTY",
            3,
            "0452-k, 0673-k, 1372-k",
            tr(
                "Même correction quota ; les rejeux figurent dans la série actuelle.",
                "Same quota correction; replays in current series.",
            ),
        ),
        (
            "DNF-PROVIDER",
            6,
            "h (SpaceBunny)",
            tr(
                "Endpoint 404, fournisseur indisponible ; série exclue.",
                "Endpoint 404, provider unavailable; series excluded.",
            ),
        ),
    ]
    table(
        fig,
        [
            tr("Classe initiale", "Initial class"),
            tr("Nombre", "Count"),
            tr("Identifiants", "Identifiers"),
            tr("Diagnostic et traitement", "Diagnosis and treatment"),
        ],
        incidents,
        [0.06, 0.47, 0.88, 0.32],
        [0.17, 0.08, 0.32, 0.43],
        9,
    )
    prose(
        fig,
        [
            (
                tr("Corrections de causalité", "Attribution corrections"),
                tr(
                    "Sur les neuf VOID-EMPTY historiques, un est une interruption de l’auteur, sept sont des incidents de quota et un est une absence de livraison retenue. La classe initiale de verdict n’est donc pas une cause. Les six identifiants individuels de h ne sont pas conservés dans les sources publiques consultées : seul leur compte documenté est rapporté.",
                    "Of nine historical VOID-EMPTY outcomes, one is an author interruption, seven are quota incidents and one is a retained non-delivery. An initial verdict class is not a cause. The six individual h identifiers are absent from the public sources inspected; only the documented count is reported.",
                ),
            ),
            (
                tr("État actuel", "Current state"),
                tr(
                    "Les cinq échecs retenus dans les séries courantes sont les quatre timeouts et 0470-c2. Le total historique 19 n’est pas le nombre d’échecs du rapport courant. Mistral et Haiku sont des extensions distinctes de cette matrice historique. Source : journal du 6 octobre et ses deux corrections, plus snapshot.json.",
                    "The five retained failures in current series are the four timeouts and 0470-c2. Historical 19 is not the failure count in the current report. Mistral and Haiku are distinct extensions of that historical matrix. Source: October 6 journal and its two corrections, plus snapshot.json.",
                ),
            ),
        ],
        y=0.40,
        fontsize=10,
    )
    finish(fig)

    fig = page(
        tr(
            "Guide de choix : contraintes avant classement",
            "Situation guide: constraints before ranking",
        ),
        tr(
            "Relu par un relecteur délégué (Fable) à la demande de l’auteur. Ce guide ne vaut ni autorisation de transfert de données ni politique de routage appliquée.",
            "Reviewed by a delegated Fable reviewer at the author’s request. This guide is neither data-transfer authorization nor an applied routing policy.",
        ),
    )
    scenarios = [
        (
            tr(
                "Contenu non autorisé à sortir / hors ligne",
                "Uncleared content / offline",
            ),
            tr(
                "Local obligatoire dans ce cas ; IQ3_S si la durée convient, sinon différer ou réduire la tâche. Aucun score ne lève la contrainte de confidentialité.",
                "Local required in this case; IQ3_S if time permits, otherwise defer or reduce the task. Scores do not override confidentiality.",
            ),
        ),
        (
            tr(
                "Interaction, résultat attendu vite",
                "Interactive, short wait preferred",
            ),
            tr(
                "Sonnet : 2,09 min en moyenne (médiane 1,13) ; Opus low : 3,03 (2,82) ; Haiku : 6,11 (3,03) ; Luna : 5,02 (3,84). Valeurs observées, pas des délais garantis ; Sonnet et Opus low ne sont pas séparés, même nominalement (p = 0,16).",
                "Sonnet: 2.09 min mean (1.13 median); Opus low: 3.03 (2.82); Haiku: 6.11 (3.03); Luna: 5.02 (3.84). Observed values, not guaranteed times; Sonnet/Opus low is not separated even nominally (p = 0.16).",
            ),
        ),
        (
            tr("Volume, budget API réduit", "Bulk work, small API budget"),
            tr(
                "Luna : 0,0388 USD en moyenne, 0,0278 en médiane par ticket. Haiku : 0,1257 moyen, 0,0228 médian ; la moyenne porte le risque de queue des longues tâches et du tarif ×5 au-delà de 100 000 tokens de prompt. Écart de coût apparié non significatif même nominalement (p = 0,36 ; Haiku moins cher sur 5/10).",
                "Luna: USD 0.0388 mean, 0.0278 median per ticket. Haiku: 0.1257 mean, 0.0228 median; the mean carries the tail risk from long tasks and the 5x rate above 100k prompt tokens. Paired cost difference not even nominal (p = 0.36, Haiku cheaper on 5/10).",
            ),
        ),
        (
            tr("Travail asynchrone, GPU disponible", "Asynchronous, GPU available"),
            tr(
                "IQ3_S : 26,20/30, 46,11 min. Préserver un créneau GPU ; le test n’évalue pas le débit multiutilisateur ni une autre machine. Meilleure moyenne locale ; les écarts aux autres séries locales sont nominaux seulement.",
                "IQ3_S: 26.20/30, 46.11 min. Reserve a GPU window; the test does not measure multiuser throughput or another machine. Best local mean; gaps to other local arms are nominal only.",
            ),
        ),
        (
            tr("GPU occupé", "GPU busy"),
            tr(
                "Si le contenu est autorisé, choisir dans les lignes délai ou budget ; sinon attendre. La pause de 0333-b2 est une libération du GPU demandée par l’auteur (rejeu 30/30), pas une défaillance du modèle.",
                "If content is cleared, pick from the latency or budget rows; otherwise wait. The 0333-b2 pause was an author-requested GPU release (replay 30/30), not a model failure.",
            ),
        ),
        (
            tr("Coût de reprise important", "Retries matter"),
            tr(
                "Budgéter toutes les tentatives et le jugement, pas seulement le dernier succès. Mistral mA couvre 26 des 35 tentatives conservées, pas la facture de la campagne. Pour Haiku, le jugement (1,48 USD) a coûté plus que les runs candidats (1,26).",
                "Budget every attempt and the judging, not just the last success. Mistral mA covers 26 of 35 preserved attempts, not the campaign bill. For Haiku, judging (USD 1.48) cost more than the candidate runs (1.26).",
            ),
        ),
    ]
    table(
        fig,
        [
            tr("Situation", "Situation"),
            tr("Choix proposé et limite", "Proposed choice and limit"),
        ],
        scenarios,
        [0.06, 0.22, 0.88, 0.57],
        [0.29, 0.71],
        10,
    )
    a, b = snapshot["arms"]["n"], snapshot["arms"]["g"]
    threshold = (b["cost_usd_mean"] - a["cost_usd_mean"]) / (
        (a["seconds_mean"] - b["seconds_mean"]) / 3600
    )
    fig.text(
        0.06,
        0.16,
        wrap(
            fig,
            tr(
                f"Exemple Haiku/Sonnet : en valorisant le délai linéairement, leurs coûts totaux moyens sont égaux vers {number(threshold)} USD par heure de délai et par ticket (l’erg·h du rapport). Au-dessus, Sonnet est moins cher en coût total valorisé ; au-dessous, Haiku. Cela ignore la différence de qualité (nominale seulement, p = 0,42) et n’exprime pas une préférence de l’auteur.",
                f"Haiku/Sonnet example: with linear delay valuation, mean total costs cross at about USD {number(threshold)} per hour of delay per ticket (the report’s erg·h). Above this, Sonnet has lower valued total cost; below it, Haiku. This ignores the quality difference (nominal only, p = 0.42) and does not state an author preference.",
            ),
            10,
        ),
        fontsize=10,
        va="top",
    )
    finish(fig)

    fig = page(
        tr(
            "Guide : heures creuses, quotas et disponibilité",
            "Guide: off-peak, quotas and availability",
        ),
        tr(
            "Tarification vérifiée le 9 octobre 2026 ; séparer les tarifs du guide et les coûts historiques figés du tournoi.",
            "Pricing checked October 9, 2026; guide rates are separate from frozen historical tournament costs.",
        ),
    )
    prose(
        fig,
        [
            (
                tr(
                    "DeepSeek direct : planifier le flexible",
                    "Direct DeepSeek: schedule flexible work",
                ),
                tr(
                    "La documentation officielle indique des tarifs creux égaux à la moitié des tarifs pleins. Pics du lundi au vendredi : 01:00-04:00 et 06:00-10:00 UTC, hors jours fériés chinois ; autres heures, week-ends et jours fériés chinois en creux. Utiliser UTC, pas une heure parisienne fixe qui changerait avec l’heure d’été. Pour Flash, entrée hors cache : 0,15/0,30 USD par million, sortie : 0,60/1,20 ; cache lu : 0,003/0,006. Ces tarifs ne s’appliquent pas automatiquement à un revendeur.",
                    "Official documentation gives off-peak rates at half of peak. Peaks Monday-Friday: 01:00-04:00 and 06:00-10:00 UTC, excluding Chinese public holidays; other hours, weekends and Chinese public holidays are off-peak. Use UTC rather than a fixed Paris hour that changes with DST. Flash cache-miss input: USD 0.15/0.30 per million; output: 0.60/1.20; cache hit: 0.003/0.006. Reseller pricing need not match.",
                ),
            ),
            (
                tr("Mesure et comptabilité", "Measurement and accounting"),
                tr(
                    "Les événements par requête ne sont pas réaudités ici. L’heure de fin d’une tâche peut être un proxy imparfait si elle traverse un changement tarifaire. Le guide ne réévalue pas rétroactivement les points du tournoi ; il faut comparer la facture fournisseur à l’estimation du client pour une nouvelle campagne.",
                    "Per-request events are not reaudited here. Task finish time can be an imperfect proxy when a task crosses a rate boundary. This guide does not retrospectively reprice tournament points; compare provider billing with client estimates for a new campaign.",
                ),
            ),
            (
                tr(
                    "Quotas et caps : préserver aussi les juges",
                    "Quotas and caps: protect the judges too",
                ),
                tr(
                    "Le journal rapporte un manque de crédits OpenAI, un plafond mensuel OpenRouter passé de 40 à 60 USD et un endpoint gratuit retiré. Le plafond OpenRouter a bloqué le panel entier, dont les trois juges utilisaient ce fournisseur. Avant une nouvelle campagne : vérifier crédits, caps, limites de concurrence (DeepSeek : Flash 2 500, Pro 500) et budget des juges ; réserver une marge ; conserver les traces d’incident et distinguer erreur fournisseur et erreur du modèle.",
                    "The journal records depleted OpenAI credits, an OpenRouter monthly cap raised from USD 40 to 60, and a withdrawn free endpoint. The OpenRouter cap stalled the entire panel, whose three judges used that provider. Before a new campaign: check credits, caps, concurrency limits (DeepSeek: Flash 2,500, Pro 500) and judge budget; reserve headroom; preserve incident evidence and distinguish provider and model errors.",
                ),
            ),
        ],
        fontsize=10.5,
    )
    fig.text(
        0.06,
        0.10,
        tr(
            "Source officielle DeepSeek (consultée le 9 octobre) : api-docs.deepseek.com/quick_start/pricing/",
            "Official DeepSeek source (accessed October 9): api-docs.deepseek.com/quick_start/pricing/",
        ),
        fontsize=9,
        color="#2563eb",
        url="https://api-docs.deepseek.com/quick_start/pricing/",
    )
    finish(fig)

    fig = page(
        tr(
            "Provenance et critères de sortie de 1046",
            "Provenance and ticket 1046 exit criteria",
        ),
        tr(
            "Compléments calculés depuis ~/arena (padme) ; l’instantané public donne les mêmes chiffres. Aucun contenu de tâche privée n’est inclus.",
            "Supplements computed from ~/arena (padme); the public snapshot gives the same numbers. No private task content is included.",
        ),
    )
    prose(
        fig,
        [
            (
                tr("Reproduction", "Reproduction"),
                tr(
                    "Le générateur original appelle tournament-report-completion.py pour ajouter les pages 13-26 dans les deux langues. Les distributions et tests sont recalculés depuis l’instantané produit à partir de ~/arena (snapshot.json) ; appendix-analysis.json conserve toutes les 190 paires et paired-differences.csv les 130 observations des treize comparaisons présentées. Les données numériques de base et les 136 tests par axe des DAG sont inchangés.",
                    "The original generator calls tournament-report-completion.py to append pages 13-26 in both languages. Distributions and tests are recomputed from the snapshot built from ~/arena (snapshot.json); appendix-analysis.json retains all 190 pairs and paired-differences.csv the 130 observations of thirteen displayed comparisons. Base numeric data and the DAG 136 tests per axis are unchanged.",
                ),
            ),
            (
                tr(
                    "Sources et limites de traçabilité",
                    "Sources and traceability limits",
                ),
                tr(
                    "Instantané public figé e352f74… : résultats retenus, audits de tentatives et coûts Mistral/Haiku. Grille : skills/route/grid.json. Hypothèses : ticket 1024, entrée du 5 octobre à 08:40Z. Événements : journal du 6 octobre et corrections. Le 9 octobre, le générateur relancé en mode --arena sur les archives privées (padme) reproduit à l’identique tests.json, comparisons.csv et toutes les valeurs des séries ; l’instantané public ajoute seulement les métadonnées comptables de Haiku 5.5. La sélection aléatoire et les factures originales ne sont pas réauditées. Les six incidents h sont documentés en nombre, sans identifiants inventés.",
                    "Frozen public snapshot e352f74…: retained results, attempt audits and Mistral/Haiku costs. Grid: skills/route/grid.json. Hypotheses: ticket 1024, October 5 at 08:40Z. Outcomes: October 6 journal and corrections. On October 9 the generator rerun in --arena mode on the private archives (padme) reproduced tests.json, comparisons.csv and every series value identically; the public snapshot only adds Haiku 5.5 accounting metadata. Random selection and original invoices are not reaudited. Six h incidents are reported as a count without invented identifiers.",
                ),
            ),
            (
                tr("État des critères de sortie", "Exit criteria status"),
                tr(
                    "Contenu demandé : graphes, grille, verdicts H1/H2, effort, inter-camps, distributions, classes, événements et guide désormais présents. Reproduction publique et finition contrôlées. Le guide a été relu par un relecteur délégué (Fable) sur instruction de l’auteur, et ses corrections appliquées. Ce rapport constitue l’analyse appariée demandée par le parent 1024. Le contenu des tickets d’origine n’est pas exporté.",
                    "Requested content is now present: plots, grid, H1/H2 verdicts, effort, cross-camp comparisons, distributions, classes, outcomes and guide. Public reproduction and layout are checked. The guide was reviewed by a delegated Fable reviewer on the author’s instruction, and its corrections applied. This report is the paired-analysis write-up required by parent 1024. Original task content is not exported.",
                ),
            ),
        ],
        fontsize=10.5,
    )
    finish(fig)
