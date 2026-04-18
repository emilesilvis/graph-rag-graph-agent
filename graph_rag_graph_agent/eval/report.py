"""Produce a markdown report from a RunSummary."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from graph_rag_graph_agent.config import EVAL_REPORT_PATH, EVAL_RUNS_DIR
from graph_rag_graph_agent.eval.run import RunSummary, TurnResult

_VERDICT_EMOJI = {"correct": "OK", "partial": "~", "wrong": "X"}


def _score(verdict: str) -> float:
    return {"correct": 1.0, "partial": 0.5, "wrong": 0.0}.get(verdict, 0.0)


def _load_summary_dict(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_run_path() -> Path:
    if not EVAL_RUNS_DIR.exists():
        raise RuntimeError(
            f"No eval runs found in {EVAL_RUNS_DIR}. Run the eval first."
        )
    candidates = sorted(EVAL_RUNS_DIR.glob("*.json"))
    if not candidates:
        raise RuntimeError(f"No eval run files in {EVAL_RUNS_DIR}.")
    return candidates[-1]


def _aggregate(results: list[dict], agents: list[str]) -> dict:
    cats = sorted({r["category"] for r in results})
    per_cat: dict[str, dict[str, list[float]]] = {
        c: {a: [] for a in agents} for c in cats
    }
    latency: dict[str, list[float]] = {a: [] for a in agents}
    for r in results:
        per_cat[r["category"]][r["agent"]].append(_score(r["verdict"]))
        latency[r["agent"]].append(float(r["latency_seconds"]))
    return {"per_cat": per_cat, "latency": latency, "categories": cats}


def write_report(
    run_path: Path | None = None,
    out_path: Path | None = None,
) -> Path:
    run_path = run_path or _latest_run_path()
    out_path = out_path or EVAL_REPORT_PATH
    data = _load_summary_dict(run_path)
    agents: list[str] = data["agents"]
    results: list[dict] = data["results"]
    agg = _aggregate(results, agents)

    lines: list[str] = []
    lines.append(f"# Eval report - `{data['run_id']}`")
    lines.append("")
    lines.append(f"- Started: {data['started_at']}")
    lines.append(f"- Questions: {data['question_count']}")
    lines.append(f"- Agents: {', '.join(agents)}")
    lines.append(f"- Source: `{run_path}`")
    lines.append("")

    lines.append("## Accuracy by category")
    lines.append("")
    lines.append(
        "Scores are mean judge grades (correct=1, partial=0.5, wrong=0); "
        "`n` is sample size in that cell."
    )
    lines.append("")
    header = "| Category | " + " | ".join(agents) + " |"
    sep = "| --- | " + " | ".join("---" for _ in agents) + " |"
    lines.append(header)
    lines.append(sep)
    for cat in agg["categories"]:
        row = [cat]
        for a in agents:
            scores = agg["per_cat"][cat][a]
            if scores:
                row.append(f"{sum(scores) / len(scores):.2f} (n={len(scores)})")
            else:
                row.append("-")
        lines.append("| " + " | ".join(row) + " |")
    overall_row = ["**overall**"]
    for a in agents:
        all_scores = [_score(r["verdict"]) for r in results if r["agent"] == a]
        if all_scores:
            overall_row.append(
                f"**{sum(all_scores) / len(all_scores):.2f}** (n={len(all_scores)})"
            )
        else:
            overall_row.append("-")
    lines.append("| " + " | ".join(overall_row) + " |")
    lines.append("")

    lines.append("## Latency")
    lines.append("")
    lat_header = "| Agent | mean (s) | p95 (s) | n |"
    lines.append(lat_header)
    lines.append("| --- | --- | --- | --- |")
    for a in agents:
        lat = sorted(agg["latency"][a])
        if not lat:
            continue
        mean = sum(lat) / len(lat)
        p95 = lat[max(0, int(0.95 * len(lat)) - 1)]
        lines.append(f"| {a} | {mean:.2f} | {p95:.2f} | {len(lat)} |")
    lines.append("")

    lines.append("## Per-question detail")
    lines.append("")
    q_to_results: dict[str, dict[str, dict]] = {}
    for r in results:
        q_to_results.setdefault(r["question_id"], {})[r["agent"]] = r

    for qid in sorted(q_to_results.keys()):
        cell = q_to_results[qid]
        sample = next(iter(cell.values()))
        lines.append(f"### `{qid}` - *{sample['category']}*")
        lines.append("")
        lines.append(f"**Question:** {sample['question']}")
        lines.append("")
        lines.append(f"**Expected:** {sample['expected_answer']}")
        if sample.get("expected_entities"):
            lines.append(f"**Key entities:** {', '.join(sample['expected_entities'])}")
        lines.append("")
        for a in agents:
            if a not in cell:
                continue
            r = cell[a]
            mark = _VERDICT_EMOJI.get(r["verdict"], "?")
            lines.append(
                f"- **{a}** [{mark} {r['verdict']}, {r['latency_seconds']:.1f}s] - "
                f"{r['rationale']}"
            )
            answer = r["agent_answer"].strip().replace("\n", " ")
            if len(answer) > 400:
                answer = answer[:400] + "..."
            lines.append(f"    > {answer}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
