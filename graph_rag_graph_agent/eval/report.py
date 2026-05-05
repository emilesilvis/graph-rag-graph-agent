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
    tool_calls: dict[str, dict[str, list[int]]] = {
        c: {a: [] for a in agents} for c in cats
    }
    for r in results:
        per_cat[r["category"]][r["agent"]].append(_score(r["verdict"]))
        latency[r["agent"]].append(float(r["latency_seconds"]))
        tcc = int(r.get("tool_call_count", 0) or 0)
        tool_calls[r["category"]][r["agent"]].append(tcc)
    return {
        "per_cat": per_cat,
        "latency": latency,
        "categories": cats,
        "tool_calls": tool_calls,
    }


def _attribution_split(results: list[dict], agents: list[str]) -> dict:
    """Count {agent_ok, agent_miss, extraction_miss, no_oracle} per category.

    Returns a nested dict shape: split[category][agent][status] = count.
    Only meaningful for the graph agent's `extraction_miss` bucket; for RAG
    we still report it for symmetry but the attribution module forces
    `agent_ok` / `agent_miss` based on verdict only.
    """
    cats = sorted({r["category"] for r in results})
    statuses = ["agent_ok", "agent_miss", "extraction_miss", "no_oracle"]
    split: dict[str, dict[str, dict[str, int]]] = {
        c: {a: {s: 0 for s in statuses} for a in agents} for c in cats
    }
    for r in results:
        status = r.get("oracle_status", "no_oracle")
        if status not in statuses:
            status = "no_oracle"
        split[r["category"]][r["agent"]][status] += 1
    return {"split": split, "categories": cats, "statuses": statuses}


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

    # --- Tool-call counts (v3 instrumentation) -----------------------------
    has_tool_data = any(
        any(int(r.get("tool_call_count", 0) or 0) > 0 for r in results if r["agent"] == a)
        for a in agents
    )
    if has_tool_data:
        lines.append("## Tool-call counts")
        lines.append("")
        lines.append(
            "Mean tool calls per question, per category. Higher = the agent "
            "needed more retrieval or refinement steps to answer."
        )
        lines.append("")
        header = "| Category | " + " | ".join(agents) + " |"
        sep = "| --- | " + " | ".join("---" for _ in agents) + " |"
        lines.append(header)
        lines.append(sep)
        for cat in agg["categories"]:
            row = [cat]
            for a in agents:
                counts = agg["tool_calls"][cat][a]
                if counts:
                    row.append(f"{sum(counts) / len(counts):.1f} (n={len(counts)})")
                else:
                    row.append("-")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # --- Failure attribution (v3) ------------------------------------------
    has_oracle_data = any(r.get("oracle_status") for r in results)
    if has_oracle_data:
        attr = _attribution_split(results, agents)
        lines.append("## Failure attribution")
        lines.append("")
        lines.append(
            "Per category and agent, how each row was attributed by the "
            "oracle Cypher. `extraction_miss` = the gold answer is not "
            "reachable from the extracted graph (graph paradigm only); "
            "`agent_miss` = reachable but the agent answered wrong / "
            "partial; `agent_ok` = reachable and the agent answered "
            "correctly; `no_oracle` = the question has no seed_cypher "
            "(answer lives only in the markdown)."
        )
        lines.append("")
        for a in agents:
            lines.append(f"### {a}")
            lines.append("")
            header = "| Category | agent_ok | agent_miss | extraction_miss | no_oracle |"
            lines.append(header)
            lines.append("| --- | --- | --- | --- | --- |")
            totals = {s: 0 for s in attr["statuses"]}
            for cat in attr["categories"]:
                row = [cat]
                for s in attr["statuses"]:
                    n = attr["split"][cat][a][s]
                    totals[s] += n
                    row.append(str(n))
                lines.append("| " + " | ".join(row) + " |")
            tot_row = ["**total**"] + [f"**{totals[s]}**" for s in attr["statuses"]]
            lines.append("| " + " | ".join(tot_row) + " |")
            lines.append("")

    # --- set_difference adoption (graph only, v6) --------------------------
    sd_rows: list[tuple[str, str, int]] = []
    for r in results:
        if r["agent"] != "graph":
            continue
        n_sd = int(r.get("set_difference_calls", 0) or 0)
        if n_sd > 0:
            sd_rows.append((r["question_id"], r["category"], n_sd))
    if sd_rows:
        total_sd_calls = sum(n for _, _, n in sd_rows)
        lines.append("## `set_difference` adoption (graph agent, v6)")
        lines.append("")
        lines.append(
            "Number of `set_difference(candidate_cypher, exclude_cypher)` "
            "tool invocations that produced a populated diff (rather than "
            "an error). Quantifies how often v6's lever 1 (negation guard "
            "rail) actually fired - paradigm-symmetric to v5's "
            "alias-folded calls and v3's `find_rel_types_like` coverage."
        )
        lines.append("")
        lines.append(
            f"Total `set_difference` calls across all questions: "
            f"**{total_sd_calls}** (touched {len(sd_rows)} of "
            f"{sum(1 for r in results if r['agent'] == 'graph')} graph rows)."
        )
        lines.append("")
        lines.append("| Question | Category | set_difference calls |")
        lines.append("| --- | --- | --- |")
        for qid, cat, n in sd_rows:
            lines.append(f"| `{qid}` | {cat} | {n} |")
        lines.append("")

    # --- alias-folded tool calls (graph only, v5) --------------------------
    alias_rows: list[tuple[str, str, int]] = []
    for r in results:
        if r["agent"] != "graph":
            continue
        n_alias = int(r.get("aliases_used_calls", 0) or 0)
        if n_alias > 0:
            alias_rows.append((r["question_id"], r["category"], n_alias))
    if alias_rows:
        total_alias_calls = sum(n for _, _, n in alias_rows)
        lines.append("## Alias-folded tool calls (graph agent, v5)")
        lines.append("")
        lines.append(
            "Number of `reach` / `neighbourhood` / `resolve_entity` calls "
            "where two or more node-name spellings (alias siblings, e.g. "
            "`Auth Service` + `Authentication Service`) were unioned in "
            "the result. Quantifies how often v5's lever 1 (tool-level "
            "alias resolution) actually fired."
        )
        lines.append("")
        lines.append(
            f"Total alias-folded tool calls across all questions: "
            f"**{total_alias_calls}** "
            f"(touched {len(alias_rows)} of "
            f"{sum(1 for r in results if r['agent'] == 'graph')} graph rows)."
        )
        lines.append("")
        lines.append("| Question | Category | alias-folded calls |")
        lines.append("| --- | --- | --- |")
        for qid, cat, n in alias_rows:
            lines.append(f"| `{qid}` | {cat} | {n} |")
        lines.append("")

    # --- find_rel_types_like coverage (graph only, v3) ---------------------
    coverage_rows: list[tuple[str, list[str], dict[str, bool]]] = []
    for r in results:
        if r["agent"] != "graph":
            continue
        concepts = r.get("concepts_in_question") or []
        if not concepts:
            continue
        coverage_rows.append(
            (
                r["question_id"],
                list(concepts),
                dict(r.get("find_rel_types_like_calls") or {}),
            )
        )
    if coverage_rows:
        lines.append("## `find_rel_types_like` coverage (graph agent)")
        lines.append("")
        lines.append(
            "For each gold question that flagged concepts requiring "
            "rel-type unioning, did the graph agent invoke "
            "`find_rel_types_like` for each concept? A concept is matched "
            "fuzzily by token / stem overlap with the tool's `concept` arg."
        )
        lines.append("")
        lines.append("| Question | Concept | Probed? |")
        lines.append("| --- | --- | --- |")
        for qid, concepts, calls in coverage_rows:
            for c in concepts:
                hit = calls.get(c, False)
                lines.append(f"| `{qid}` | {c} | {'yes' if hit else 'no'} |")
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
        # Oracle row (shared across agents for this question).
        any_row = next(iter(cell.values()))
        if any_row.get("oracle_has_oracle"):
            ocount = any_row.get("oracle_row_count", 0)
            lines.append(f"**Oracle Cypher rows:** {ocount}")
            enumeration = any_row.get("oracle_enumeration")
            if enumeration:
                # v6: surface the oracle's collect()-based enumeration so
                # aggregate-question failures (e.g. gold-025 partial 5/9
                # teams) are immediately attributable to extraction or
                # to agent reasoning by inspection.
                lines.append(
                    f"**Oracle enumeration ({len(enumeration)}):** "
                    + ", ".join(enumeration)
                )
            lines.append("")
        elif any_row.get("oracle_cypher") is not None and (
            "oracle_has_oracle" in any_row
        ):
            lines.append("**Oracle Cypher rows:** (no oracle for this question)")
            lines.append("")

        for a in agents:
            if a not in cell:
                continue
            r = cell[a]
            mark = _VERDICT_EMOJI.get(r["verdict"], "?")
            extras: list[str] = []
            tcc = r.get("tool_call_count")
            if tcc:
                extras.append(f"{tcc} tool calls")
            if r.get("hit_recursion_limit"):
                extras.append("hit step cap")
            status = r.get("oracle_status")
            if status and status != "no_oracle":
                extras.append(status)
            extra_str = f" ({', '.join(extras)})" if extras else ""
            lines.append(
                f"- **{a}** [{mark} {r['verdict']}, {r['latency_seconds']:.1f}s]{extra_str} - "
                f"{r['rationale']}"
            )
            answer = r["agent_answer"].strip().replace("\n", " ")
            if len(answer) > 400:
                answer = answer[:400] + "..."
            lines.append(f"    > {answer}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
