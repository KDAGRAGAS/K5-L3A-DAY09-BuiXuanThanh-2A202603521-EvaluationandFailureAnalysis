"""Failure-mode probe (M1 evidence): turn on ONE bug switch at a time and see which claims break.

    python -m lab9.fm_probe              # seed 11, every FM bug from lab9.variant_agent
    python -m lab9.fm_probe --seed 55

Each probe shape is `fixed` (no_override) plus exactly one bug, run through the same Lab 8 host and
the same graders as lab9.eval. A claim is listed under an FM when that single bug makes it fail a
grader. This is the evidence behind `failure_modes` in lab9.evalset.FAILURE_MODES and the
evidence column of docs/failure_taxonomy.md. Runs on fresh temp stores; nothing in lab8/ is edited.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from pydantic_evals.evaluators import EvaluatorContext

from lab8.console import utf8_stdio
from lab8.db import load_json, load_jsonl
from lab9.eval import WORLD, make_task
from lab9.graders import GRADERS
from lab9.variant_agent import make_shape

BUG_TO_FM = {
    "leaky_trace": "FM-01",
    "ignore_denied": "FM-02",
    "ticket_trust": "FM-03",
    "sum_parts": "FM-04",
    "pre_deducted": "FM-05",
    "stale_clause": "FM-06",
    "sibling_refund": "FM-07",
    "misreport": "FM-08",
}
BAD_WHEN_TRUE = {"secret_leak", "approval_bypass"}   # count metrics: True is the failure


def failing_graders(trial: dict, label: dict) -> list[str]:
    ctx = EvaluatorContext(name="probe", inputs={}, metadata=None, expected_output=label, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    out = []
    for name, grader in GRADERS.items():
        value = grader().evaluate(ctx).value
        if (value if name in BAD_WHEN_TRUE else not value):
            out.append(name)
    return out


def probe(seed: int = 11) -> list[tuple[str, str, str, list[str], str]]:
    from lab8.shapes import SHAPES

    claims = load_jsonl(Path("data/public_claims.jsonl"))
    labels = {c["claim_id"]: c["expected"] for c in claims}
    world = load_json(WORLD)
    rows = []
    for bug, fm in BUG_TO_FM.items():
        name = f"probe_{bug}"
        SHAPES[name] = make_shape(name, {"no_override", bug})
        with tempfile.TemporaryDirectory(prefix="lab9-probe-", ignore_cleanup_errors=True) as tmp:
            task = make_task(name, world, claims, labels, Path(tmp))
            for claim in claims:
                trial = task({"claim_id": claim["claim_id"], "seed": seed})
                bad = failing_graders(trial, labels[claim["claim_id"]])
                if bad:
                    rows.append((fm, bug, claim["claim_id"], bad, str(trial["lab8_reason"])))
    return rows


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.fm_probe")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args(argv)
    rows = probe(args.seed)
    print(f"{'FM':<6} {'bug':<15} {'claim@seed':<12} {'failing graders':<60} lab8 reason")
    for fm, bug, claim_id, bad, reason in rows:
        print(f"{fm:<6} {bug:<15} {claim_id + '@' + str(args.seed):<12} {', '.join(bad):<60} {reason}")
    by_claim: dict[str, list[str]] = {}
    for fm, _, claim_id, _, _ in rows:
        by_claim.setdefault(claim_id, []).append(fm)
    print("-- per claim:", {k: sorted(set(v)) for k, v in sorted(by_claim.items())})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
