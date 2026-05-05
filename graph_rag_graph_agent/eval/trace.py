"""Extract diagnostic trace data from a LangGraph agent's message list.

This module is read-only: it inspects the messages produced by a ReAct
invocation and pulls out tool-call metadata, Cypher-specific telemetry, and
recursion-limit signals so the eval can attribute failures to causes
(extraction vs. agent reasoning vs. step budget) rather than relying on
qualitative inspection.

It does NOT modify agent behaviour.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# langgraph's prebuilt ReAct emits this exact AI message when the model still
# wants to call tools but the recursion budget has been exhausted. Detecting
# it lets us attribute these as "step-limit refusals" rather than wrong
# answers per se. Source: langgraph.prebuilt.chat_agent_executor.
RECURSION_LIMIT_MARKER = "Sorry, need more steps to process this request."

_ROW_COUNT_RE = re.compile(r"\((\d+)\s+rows?\)")
_NOTE_LINE_RE = re.compile(r"^NOTE:.*$", re.MULTILINE)
_OUTPUT_PREVIEW_CHARS = 240
# v5: detect when an alias-aware tool (reach / neighbourhood / resolve_entity)
# folded sibling spellings into the result. The signal is one of three
# distinct phrases the tools emit; count any tool output that contained
# at least one as an "alias-folded call".
_ALIAS_SIGNAL_RE = re.compile(r"aliases unioned:|aliases of '")
# v6: detect when the agent invoked the `set_difference` negation guard
# rail and got a populated diff back (rather than an error). Symmetric
# to the alias signal above; lets the report quantify lever-1 adoption
# for v6 the way v5 quantifies it for alias unioning.
_SET_DIFF_SIGNAL_RE = re.compile(r"^set_difference:", re.MULTILINE)
# v7: count get_section_content invocations as the PageIndex paradigm's
# adoption signal - the analogue of v5's alias-folded calls and v6's
# set_difference calls.
_PAGEINDEX_SECTION_TOOL = "get_section_content"
# v8: router-agent sub-agent delegation tools. Each call records the
# paradigm the meta-router chose for that turn. `router_primary` is the
# paradigm the router consulted FIRST (a coarse "router picked X" signal
# for the report), while `router_calls` is the full per-paradigm tally.
_ROUTER_TOOL_TO_PARADIGM = {
    "ask_rag": "rag",
    "ask_graph": "graph",
    "ask_pageindex": "pageindex",
}


@dataclass
class ToolCallRecord:
    name: str
    args_summary: str
    output_chars: int
    output_preview: str


@dataclass
class CypherCallRecord:
    query: str
    row_count: int | None
    preflight_notes: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class AgentTraceSummary:
    tool_call_count: int
    tool_calls: list[ToolCallRecord]
    cypher_calls: list[CypherCallRecord]
    find_rel_types_like_args: list[str]
    find_rel_types_like_calls: dict[str, bool]
    hit_recursion_limit: bool
    step_at_first_relevant_match: int | None
    # v5 instrumentation: count tool outputs where alias siblings were
    # folded in (reach / neighbourhood / resolve_entity emit a marker
    # line when more than one node-name spelling contributed). Lets the
    # report show "lever 1 fired N times" alongside the find_rel_types_like
    # coverage count.
    aliases_used_calls: int = 0
    # v6 instrumentation: count tool outputs from the `set_difference`
    # negation guard rail (lever 1 in v6). Includes both successful and
    # error outputs - the marker fires on every non-cap-error invocation -
    # so the report can show adoption per question.
    set_difference_calls: int = 0
    # v7 instrumentation: count `get_section_content` calls (the PageIndex
    # agent's body-text-fetch tool). Paradigm-symmetric to v5's
    # aliases_used_calls and v6's set_difference_calls - lets the report
    # quantify how many sections the PageIndex agent navigated to per
    # question.
    pageindex_section_calls: int = 0
    # v8 instrumentation: per-paradigm sub-agent delegation counts from
    # the router agent's ReAct loop. `router_calls` keys are
    # {"rag", "graph", "pageindex"}; `router_primary` is the first
    # paradigm consulted on the question (None if the router didn't
    # call any sub-agent, e.g. a refusal or scratchpad-only turn).
    router_calls: dict[str, int] = field(default_factory=dict)
    router_primary: str | None = None


def _summarise_args(args: Any) -> str:
    if isinstance(args, dict):
        try:
            return json.dumps(args, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(args)
    return str(args)


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _parse_row_count(output: str) -> int | None:
    """Parse `(N rows)` / `(N row)` from a `run_cypher` tool output.

    Returns None if no row-count footer is present (e.g. the tool returned
    an ERROR string rather than a result table).
    """
    matches = _ROW_COUNT_RE.findall(output)
    if not matches:
        return None
    return int(matches[-1])


def _extract_preflight_notes(output: str) -> list[str]:
    return _NOTE_LINE_RE.findall(output)


def _is_cypher_error(output: str) -> str | None:
    if output.startswith("ERROR"):
        return output.splitlines()[0]
    return None


def _expected_entity_appears(output: str, expected_entities: list[str]) -> bool:
    if not expected_entities:
        return False
    haystack = output.lower()
    return any(ent and ent.lower() in haystack for ent in expected_entities)


_STEM_PREFIX_LEN = 4


def _stem(token: str) -> str:
    """Return a coarse stem - first `_STEM_PREFIX_LEN` chars, lowercased.

    This is intentionally crude: we just want "managed", "manages", "manage",
    "managing" to share a stem so concept matching tolerates the inflection
    differences between English question phrasing and the LLM's tool args.
    """
    return token.lower()[:_STEM_PREFIX_LEN]


def _stems(text: str) -> set[str]:
    return {_stem(t) for t in re.split(r"\W+", text) if len(t) >= 3}


def _coverage_for_concept(concept: str, find_rel_args: list[str]) -> bool:
    """True iff `concept` was probed via find_rel_types_like.

    A concept like "depends on" matches a tool arg of "depend" or "dependency"
    via shared word stems (first 4 letters, lowercased). This is intentionally
    fuzzy: the point is to detect "did the agent ever ask the schema what
    spellings express this concept?", not exact arg matching.
    """
    stems_a = _stems(concept)
    if not stems_a:
        stems_a = {_stem(concept)}
    for arg in find_rel_args:
        stems_b = _stems(arg)
        if not stems_b:
            stems_b = {_stem(arg)}
        if stems_a & stems_b:
            return True
    return False


def extract_trace(
    messages: list[Any],
    expected_entities: list[str] | None = None,
    concepts_in_question: list[str] | None = None,
) -> AgentTraceSummary:
    """Pull diagnostic data out of a ReAct message list.

    Args:
        messages: the `result["messages"]` list returned by `agent.invoke`.
        expected_entities: from the gold question; used to locate the first
            tool output where any expected entity appeared.
        concepts_in_question: from the gold question; used to score
            find_rel_types_like coverage per concept.
    """
    expected_entities = expected_entities or []
    concepts_in_question = concepts_in_question or []

    pending: dict[str, dict[str, Any]] = {}
    tool_calls: list[ToolCallRecord] = []
    cypher_calls: list[CypherCallRecord] = []
    find_rel_types_like_args: list[str] = []
    step_at_first_relevant_match: int | None = None
    hit_recursion_limit = False
    aliases_used_calls = 0
    set_difference_calls = 0
    pageindex_section_calls = 0
    router_calls: dict[str, int] = {"rag": 0, "graph": 0, "pageindex": 0}
    router_primary: str | None = None

    tool_index = 0
    for msg in messages:
        msg_type = getattr(msg, "type", None)

        if msg_type == "ai":
            content = _content_to_text(getattr(msg, "content", "") or "")
            if content.strip() == RECURSION_LIMIT_MARKER:
                hit_recursion_limit = True
            for tc in getattr(msg, "tool_calls", []) or []:
                tcid = tc.get("id")
                pending[tcid] = {
                    "name": tc.get("name", "?"),
                    "args": tc.get("args", {}),
                }

        elif msg_type == "tool":
            tcid = getattr(msg, "tool_call_id", None)
            info = pending.pop(tcid, None) or {
                "name": getattr(msg, "name", "?"),
                "args": {},
            }
            output = _content_to_text(getattr(msg, "content", "") or "")
            args_summary = _summarise_args(info.get("args"))
            tool_calls.append(
                ToolCallRecord(
                    name=info["name"],
                    args_summary=args_summary,
                    output_chars=len(output),
                    output_preview=output[:_OUTPUT_PREVIEW_CHARS],
                )
            )

            if info["name"] == "run_cypher":
                args = info.get("args") or {}
                query = args.get("query", "") if isinstance(args, dict) else ""
                err = _is_cypher_error(output)
                cypher_calls.append(
                    CypherCallRecord(
                        query=query,
                        row_count=None if err else _parse_row_count(output),
                        preflight_notes=_extract_preflight_notes(output),
                        error=err,
                    )
                )
            elif info["name"] == "find_rel_types_like":
                args = info.get("args") or {}
                concept_arg = args.get("concept", "") if isinstance(args, dict) else ""
                if isinstance(concept_arg, str) and concept_arg:
                    find_rel_types_like_args.append(concept_arg)

            if info["name"] in ("reach", "neighbourhood", "resolve_entity") and (
                _ALIAS_SIGNAL_RE.search(output)
            ):
                aliases_used_calls += 1

            if info["name"] == "set_difference" and _SET_DIFF_SIGNAL_RE.search(output):
                set_difference_calls += 1

            if info["name"] == _PAGEINDEX_SECTION_TOOL:
                pageindex_section_calls += 1

            paradigm = _ROUTER_TOOL_TO_PARADIGM.get(info["name"])
            if paradigm is not None:
                router_calls[paradigm] += 1
                if router_primary is None:
                    router_primary = paradigm

            if step_at_first_relevant_match is None and _expected_entity_appears(
                output, expected_entities
            ):
                step_at_first_relevant_match = tool_index
            tool_index += 1

    find_rel_types_like_calls = {
        c: _coverage_for_concept(c, find_rel_types_like_args)
        for c in concepts_in_question
    }

    return AgentTraceSummary(
        tool_call_count=len(tool_calls),
        tool_calls=tool_calls,
        cypher_calls=cypher_calls,
        find_rel_types_like_args=find_rel_types_like_args,
        find_rel_types_like_calls=find_rel_types_like_calls,
        hit_recursion_limit=hit_recursion_limit,
        step_at_first_relevant_match=step_at_first_relevant_match,
        aliases_used_calls=aliases_used_calls,
        set_difference_calls=set_difference_calls,
        pageindex_section_calls=pageindex_section_calls,
        router_calls=router_calls,
        router_primary=router_primary,
    )


def trace_to_dict(trace: AgentTraceSummary) -> dict[str, Any]:
    return asdict(trace)
