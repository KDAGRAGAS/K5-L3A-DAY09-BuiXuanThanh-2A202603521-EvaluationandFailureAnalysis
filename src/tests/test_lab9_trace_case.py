"""Trace case C-002@11 (docs/trace_case.md): FM-03 ticket_trust.

seeded_regression lets the ticket ("trễ 5 ngày") override the DB fact delay_days=2 at event 3
(model_override), then refunds 20.000đ that the label says must be denied. The same claim@seed on
`fixed` keeps the DB fact and is denied. Run: python -m pytest -q -m student -o addopts= -k trace_case
"""
import pytest

pytestmark = pytest.mark.student


def _grade(trial, label):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9 import graders

    ctx = EvaluatorContext(name="C-002@11", inputs={}, metadata=None, expected_output=label, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    return {name: g().evaluate(ctx).value for name, g in graders.GRADERS.items()}


def _case(shape):
    from lab9.trace_case import investigate

    case = investigate(shape, "C-002", 11)
    return case["trial"], case["label"]


def test_trace_case_c002_first_wrong_step_is_model_override():
    trial, label = _case("seeded_regression")
    kinds = [e.get("kind") for e in trial["events"]]
    first_bad = kinds.index("model_override")
    assert kinds[:first_bad] == ["handoff", "investigator"]          # steps 1-2 read the DB correctly
    assert trial["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2
    assert trial["events"][first_bad]["payload"] == {"delay_days": 5}  # step 3: ticket overrides DB
    scores = _grade(trial, label)
    assert scores["db_fact_kept"] is False
    assert scores["refund_amount_correct"] is False                    # ledger 20000, label 0
    assert trial["lab8_pass"] is False


def test_trace_case_c002_fixed_keeps_db_fact():
    trial, label = _case("fixed")
    assert all(e.get("kind") != "model_override" for e in trial["events"])
    scores = _grade(trial, label)
    assert scores["db_fact_kept"] is True and scores["refund_amount_correct"] is True
    assert trial["snapshot"]["refund_vnd"] == 0 and trial["lab8_pass"] is True
