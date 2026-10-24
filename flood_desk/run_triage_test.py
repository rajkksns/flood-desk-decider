"""Run the Flood Desk draft against the labelled test set.

Usage (from the kit folder on your PC, after copying decision_draft.py into agent/ as a
separate file, or with the draft folder on PYTHONPATH):

    python run_triage_test.py                # tuning split only (10 messages)
    python run_triage_test.py --final        # also score the held-out split (5 messages)

Rule: tune only on the tuning split. Run --final once, when you are done tuning, and report
that number as-is in the article.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # kit root, so decider_kit can be imported
from decision_draft import LeadTriage  # noqa: E402

from decider_kit import Decider  # noqa: E402


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(triage: LeadTriage, rows: list[dict]) -> dict:
    results = []
    for row in rows:
        v = triage.route(row["message"])
        results.append({"id": row["id"], "label": row["label"], "pred": v.category,
                        "conf": round(v.confidence, 3), "action": v.action,
                        "correct": v.category == row["label"]})
    acc = sum(r["correct"] for r in results) / len(results)
    return {"accuracy": round(acc, 3), "n": len(results), "rows": results}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="also score the held-out split")
    args = ap.parse_args()

    rows = load(HERE / "test_set.jsonl")
    tune = [r for r in rows if r["split"] == "tune"]
    holdout = [r for r in rows if r["split"] == "holdout"]
    triage = LeadTriage(Decider())

    out = {"tune": run(triage, tune)}
    if args.final:
        out["holdout"] = run(triage, holdout)

    for name, res in out.items():
        print(f"\n== {name}: accuracy {res['accuracy']:.0%} on {res['n']} messages")
        for r in res["rows"]:
            mark = "ok " if r["correct"] else "MISS"
            print(f"  {mark} {r['id']}  label={r['label']:<22} pred={r['pred']:<22} "
                  f"conf={r['conf']:.2f} action={r['action']}")
        if name == "tune":
            confusions = Counter((r["label"], r["pred"]) for r in res["rows"] if not r["correct"])
            if confusions:
                print("  misses:", dict(confusions))

    (HERE / "last_run.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved to {HERE / 'last_run.json'}")


if __name__ == "__main__":
    main()
