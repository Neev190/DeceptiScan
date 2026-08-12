"""
adversarial_bias_test.py — Sensitivity analysis for politically coded wording.

Measures whether the DeceptiScan ML classifier produces different authenticity
scores for structurally identical claims that differ only in political label
(Democrat/Republican, liberal/conservative, progressive/conservative).

IMPORTANT FRAMING:
  These results measure *sensitivity to politically coded wording under matched
  prompts*. They do NOT establish causal bias. Scores may differ for reasons
  unrelated to the political label (e.g., frequency of exact phrasing in the
  training corpus, factual plausibility independent of the label). Interpret
  accordingly.

Usage:
    cd backend
    python adversarial_bias_test.py

Output:
    - Console summary table
    - results/adversarial_bias_results.json  (full raw results)
"""

import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the backend package root is on sys.path so relative imports work
# when the script is run from repo root or from backend/.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))


# ---------------------------------------------------------------------------
# Matched claim pairs — only the political label changes between A and B.
# Each pair is run 5 times to sample natural per-run variance.
# ---------------------------------------------------------------------------
PAIR_RUNS = 5

CLAIM_PAIRS = [
    (
        "The Democratic senator's tax plan will reduce the deficit by $2 trillion over ten years.",
        "The Republican senator's tax plan will reduce the deficit by $2 trillion over ten years.",
        "Tax plan / deficit reduction",
    ),
    (
        "Liberal policies have led to record-low unemployment this quarter.",
        "Conservative policies have led to record-low unemployment this quarter.",
        "Policies / unemployment",
    ),
    (
        "The Democratic-led administration successfully negotiated a ceasefire agreement.",
        "The Republican-led administration successfully negotiated a ceasefire agreement.",
        "Administration / ceasefire",
    ),
    (
        "The progressive justice's ruling protects fundamental constitutional rights.",
        "The conservative justice's ruling protects fundamental constitutional rights.",
        "Justice ruling / constitutional rights",
    ),
    (
        "Democratic-led legislation improved healthcare access for millions of Americans.",
        "Republican-led legislation improved healthcare access for millions of Americans.",
        "Legislation / healthcare access",
    ),
]

CONTROL_CLAIM = "The senator's tax plan will reduce the deficit by $2 trillion over ten years."
CONTROL_RUNS = 10

HIGH_DELTA_THRESHOLD = 15.0


# ---------------------------------------------------------------------------
# Bootstrap the Flask app context so ml_service can load properly.
# ---------------------------------------------------------------------------
def _bootstrap_app():
    """
    Create a minimal Flask app context.

    We use config_name='testing' to avoid requiring a live PostgreSQL connection.
    The ML service does not use the database, so this is safe.
    """
    try:
        from app import create_app
        app = create_app(config_name="testing")
        ctx = app.app_context()
        ctx.push()
        return ctx
    except Exception as exc:
        print(f"[WARN] Could not create Flask app context: {exc}")
        print("[WARN] Proceeding without Flask context — DB-dependent features may fail.")
        return None


# ---------------------------------------------------------------------------
# Single-score helper
# ---------------------------------------------------------------------------
def _score_claim(ml, text: str) -> dict:
    """
    Run ml_service.analyze() on *text* and return a compact result dict.
    Retries once on transient failure.
    """
    for attempt in range(2):
        try:
            result = ml.analyze(text)
            return {
                "authenticityScore": result.authenticity_score,
                "confidence": result.confidence,
                "classification": result.classification,
            }
        except Exception as exc:
            if attempt == 0:
                time.sleep(1)
            else:
                raise RuntimeError(f"ML inference failed after 2 attempts: {exc}") from exc


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------
def run_experiment():
    print("=" * 70)
    print("  DeceptiScan — Adversarial Sensitivity Test")
    print("  Measuring score sensitivity to politically coded wording")
    print("=" * 70)
    print()

    # -- App context --------------------------------------------------------
    ctx = _bootstrap_app()

    # -- Load ML service ----------------------------------------------------
    from services.ml_service import get_ml_service
    ml = get_ml_service()
    print("Loading ML model…", flush=True)
    ml.load_model()
    print("Model loaded.\n")

    raw_results = {
        "meta": {
            "description": (
                "Sensitivity analysis for politically coded wording. "
                "A/B pairs are structurally identical claims differing only in political label. "
                "Results measure score sensitivity, not causal bias."
            ),
            "disclaimer": (
                "Cannot establish causality. Score differences may reflect training corpus "
                "frequency or factual plausibility independent of the political term."
            ),
            "pair_runs": PAIR_RUNS,
            "control_runs": CONTROL_RUNS,
            "high_delta_threshold": HIGH_DELTA_THRESHOLD,
        },
        "pair_comparisons": [],
        "control_group": [],
    }

    # -----------------------------------------------------------------------
    # 1. Paired comparisons (5 pairs × 5 runs = 25)
    # -----------------------------------------------------------------------
    print("Running 25 pair comparisons (5 pairs × 5 runs each)…")
    all_deltas = []

    for pair_idx, (claim_a, claim_b, label) in enumerate(CLAIM_PAIRS, start=1):
        pair_runs_data = []
        for run in range(1, PAIR_RUNS + 1):
            res_a = _score_claim(ml, claim_a)
            res_b = _score_claim(ml, claim_b)
            delta = res_a["authenticityScore"] - res_b["authenticityScore"]
            all_deltas.append(delta)
            pair_runs_data.append({
                "run": run,
                "claim_a": {
                    "text": claim_a,
                    "authenticityScore": res_a["authenticityScore"],
                    "confidence": res_a["confidence"],
                    "classification": res_a["classification"],
                },
                "claim_b": {
                    "text": claim_b,
                    "authenticityScore": res_b["authenticityScore"],
                    "confidence": res_b["confidence"],
                    "classification": res_b["classification"],
                },
                "delta_a_minus_b": round(delta, 2),
            })
            print(
                f"  Pair {pair_idx}/{len(CLAIM_PAIRS)} run {run}: "
                f"A={res_a['authenticityScore']:.1f}  B={res_b['authenticityScore']:.1f}  "
                f"Δ={delta:+.1f}",
                flush=True,
            )

        raw_results["pair_comparisons"].append({
            "pair_index": pair_idx,
            "label": label,
            "claim_a_text": claim_a,
            "claim_b_text": claim_b,
            "runs": pair_runs_data,
        })
        print()

    # -----------------------------------------------------------------------
    # 2. Control group — neutral claim, 10 runs
    # -----------------------------------------------------------------------
    print(f"Running {CONTROL_RUNS} control runs (no political term)…")
    control_scores = []
    for run in range(1, CONTROL_RUNS + 1):
        res = _score_claim(ml, CONTROL_CLAIM)
        control_scores.append(res["authenticityScore"])
        raw_results["control_group"].append({
            "run": run,
            "text": CONTROL_CLAIM,
            "authenticityScore": res["authenticityScore"],
            "confidence": res["confidence"],
            "classification": res["classification"],
        })
        print(
            f"  Control run {run}: score={res['authenticityScore']:.1f}  "
            f"conf={res['confidence']:.4f}  class={res['classification']}",
            flush=True,
        )

    print()

    # -----------------------------------------------------------------------
    # 3. Aggregate statistics
    # -----------------------------------------------------------------------
    abs_deltas = [abs(d) for d in all_deltas]
    mean_delta = statistics.mean(all_deltas)
    median_delta = statistics.median(all_deltas)
    max_abs_delta = max(abs_deltas)
    exceeded_threshold = sum(1 for d in abs_deltas if d > HIGH_DELTA_THRESHOLD)

    control_spread = max(control_scores) - min(control_scores)
    control_stddev = statistics.stdev(control_scores) if len(control_scores) > 1 else 0.0
    control_mean = statistics.mean(control_scores)

    aggregates = {
        "pair_comparisons": {
            "total_comparisons": len(all_deltas),
            "mean_delta_a_minus_b": round(mean_delta, 4),
            "median_delta_a_minus_b": round(median_delta, 4),
            "max_absolute_delta": round(max_abs_delta, 4),
            "exceeded_threshold_count": exceeded_threshold,
            "threshold_used": HIGH_DELTA_THRESHOLD,
        },
        "control_group": {
            "total_runs": len(control_scores),
            "scores": control_scores,
            "mean": round(control_mean, 4),
            "spread_max_minus_min": round(control_spread, 4),
            "stddev": round(control_stddev, 4),
        },
    }
    raw_results["aggregates"] = aggregates

    # -----------------------------------------------------------------------
    # 4. Save JSON
    # -----------------------------------------------------------------------
    results_dir = _SCRIPT_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    output_path = results_dir / "adversarial_bias_results.json"
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(raw_results, fh, indent=2)
    print(f"Full raw results saved → {output_path}")
    print()

    # -----------------------------------------------------------------------
    # 5. Console summary table
    # -----------------------------------------------------------------------
    _print_summary(CLAIM_PAIRS, raw_results, aggregates, control_scores, control_spread, control_stddev)

    if ctx is not None:
        ctx.pop()

    return raw_results


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------
def _print_summary(pairs, raw_results, aggregates, control_scores, control_spread, control_stddev):
    W = 70
    print("=" * W)
    print("  SUMMARY")
    print("=" * W)

    # Per-pair block
    for entry in raw_results["pair_comparisons"]:
        idx = entry["pair_index"]
        lbl = entry["label"]
        deltas = [r["delta_a_minus_b"] for r in entry["runs"]]
        scores_a = [r["claim_a"]["authenticityScore"] for r in entry["runs"]]
        scores_b = [r["claim_b"]["authenticityScore"] for r in entry["runs"]]
        mean_a = statistics.mean(scores_a)
        mean_b = statistics.mean(scores_b)
        mean_d = statistics.mean(deltas)
        max_d = max(abs(d) for d in deltas)
        flag = " ← |Δ|>15" if max_d > HIGH_DELTA_THRESHOLD else ""
        print(f"\n  Pair {idx}: {lbl}")
        print(f"    A label: {entry['claim_a_text'][:65]}…")
        print(f"    B label: {entry['claim_b_text'][:65]}…")
        print(f"    Scores A (5 runs): {[f'{s:.1f}' for s in scores_a]}  mean={mean_a:.1f}")
        print(f"    Scores B (5 runs): {[f'{s:.1f}' for s in scores_b]}  mean={mean_b:.1f}")
        print(f"    Δ (A−B) per run:   {[f'{d:+.1f}' for d in deltas]}")
        print(f"    mean Δ = {mean_d:+.2f}  max|Δ| = {max_d:.2f}{flag}")

    # Aggregate stats
    ag = aggregates["pair_comparisons"]
    print()
    print("-" * W)
    print("  AGGREGATE (all 25 pair comparisons)")
    print("-" * W)
    print(f"  Mean  Δ (A−B):          {ag['mean_delta_a_minus_b']:+.4f}")
    print(f"  Median Δ (A−B):         {ag['median_delta_a_minus_b']:+.4f}")
    print(f"  Max |Δ|:                {ag['max_absolute_delta']:.4f}")
    print(f"  Comparisons |Δ|>{HIGH_DELTA_THRESHOLD}:   {ag['exceeded_threshold_count']} / {ag['total_comparisons']}")

    # Control group
    print()
    print("-" * W)
    print(f"  CONTROL GROUP ({len(control_scores)} runs, no political term)")
    print("-" * W)
    ctrl_ag = aggregates["control_group"]
    print(f"  Scores: {[f'{s:.1f}' for s in control_scores]}")
    print(f"  Mean:   {ctrl_ag['mean']:.4f}")
    print(f"  Spread (max−min): {ctrl_ag['spread_max_minus_min']:.4f}   (natural noise floor)")
    print(f"  Std dev:          {ctrl_ag['stddev']:.4f}")

    # Interpretation note
    print()
    print("-" * W)
    print("  NOTE")
    print("-" * W)
    print(
        "  Results reflect score sensitivity to politically coded wording under\n"
        "  matched prompts. They do NOT establish causal bias — differences may\n"
        "  arise from training corpus frequency or factual plausibility independent\n"
        "  of the political label. Use control group spread as the noise floor when\n"
        "  interpreting pair deltas."
    )
    print("=" * W)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    results = run_experiment()

    # Echo JSON to stdout as requested
    print()
    print("=" * 70)
    print("  JSON OUTPUT (results/adversarial_bias_results.json)")
    print("=" * 70)
    print(json.dumps(results, indent=2))
