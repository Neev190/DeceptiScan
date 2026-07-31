"""
Threshold justification script for Phase 2 retrieval layer.

Queries find_similar_claims() against 20 statements from the LIAR test split
and reports the full similarity score distribution for top-3 results.
Run AFTER build_retrieval_corpus.py and with the Flask backend DB accessible.

Usage:
    cd d:/DeceptiScan/backend
    DATABASE_URL=postgresql://deceptiscan:password@localhost:5432/deceptiscan \\
        python ml_training/threshold_test.py

Output is printed to stdout and can be piped to a file for documentation.
"""
import sys as _sys
_PYLIBS = r"D:\pylibs"
if _PYLIBS in _sys.path:
    _sys.path.remove(_PYLIBS)
_sys.path.insert(0, _PYLIBS)

import os
import sys
import logging
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(1, str(BACKEND_DIR))

logging.basicConfig(level=logging.WARNING)  # suppress noise during threshold test

# 20 statements drawn from the LIAR test split
# These are held-out data — NOT in the training corpus.
TEST_STATEMENTS = [
    "Says the Keystone XL pipeline would create only 35 permanent jobs.",
    "The number of illegal immigrants in the United States is 30 million people.",
    "Obamacare is the biggest tax increase in the history of the United States.",
    "The unemployment rate is not really 5.6 percent.",
    "Under President Obama, America has lost 7.3 million jobs.",
    "Wisconsin is number one in the nation in new business startups.",
    "The Affordable Care Act is a government takeover of health care.",
    "Mitt Romney supported the bailout of the big banks.",
    "Crime is rising in the United States.",
    "Ronald Reagan raised taxes 11 times while president.",
    "The government wastes $125 billion per year in improper payments.",
    "Hillary Clinton wants to give illegal immigrants free health care.",
    "500,000 manufacturing jobs were created in the last three years.",
    "Under the president's budget, the deficit will never fall below a trillion dollars.",
    "There are 50,000 homeless veterans in the United States.",
    "The US spends more money per student on education than almost any other country.",
    "Planned Parenthood performs over 300,000 abortions per year.",
    "The top 1 percent pay 40 percent of all taxes.",
    "Medicare and Medicaid together cost more than the entire defense budget.",
    "Two thirds of American households with children do not have guns.",
]


def run_threshold_test():
    from app import create_app
    from services.retrieval_service import RetrievalService

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://deceptiscan:password@localhost:5432/deceptiscan"
    )
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    svc = RetrievalService()
    svc.load_model()

    all_scores = []

    print("\n" + "=" * 70)
    print("LIAR TEST-SPLIT THRESHOLD JUSTIFICATION")
    print("Querying 20 held-out statements against the training corpus")
    print("=" * 70)

    with app.app_context():
        for i, stmt in enumerate(TEST_STATEMENTS, 1):
            results = svc.find_similar_claims(stmt, k=3)
            scores = [r["similarity_score"] for r in results]
            all_scores.extend(scores)

            print(f"\n[{i:02d}] Query: \"{stmt[:70]}...\"" if len(stmt) > 70
                  else f"\n[{i:02d}] Query: \"{stmt}\"")
            if results:
                for j, r in enumerate(results, 1):
                    print(f"      #{j} sim={r['similarity_score']:.4f}  "
                          f"[{r['label']}]  \"{r['statement_text'][:60]}...\"")
            else:
                print("      (no results above threshold of 0.0 — all filtered)")

    if all_scores:
        all_scores.sort(reverse=True)
        print("\n" + "=" * 70)
        print("SCORE DISTRIBUTION (across all top-3 results, N=" + str(len(all_scores)) + ")")
        print("=" * 70)
        print(f"  Max    : {max(all_scores):.4f}")
        print(f"  Min    : {min(all_scores):.4f}")
        print(f"  Mean   : {sum(all_scores)/len(all_scores):.4f}")
        # Percentile breakdown
        n = len(all_scores)
        for pct in [10, 25, 50, 75, 90]:
            idx = int(n * (1 - pct / 100))
            idx = max(0, min(idx, n - 1))
            print(f"  P{pct:02d}   : {all_scores[idx]:.4f}")
        print()
        print("  All scores (sorted descending):")
        print("  " + ", ".join(f"{s:.4f}" for s in all_scores))
        print("\n" + "=" * 70)
        print("ACTION: Review the distribution above and pick the cutoff where")
        print("scores 'fall off a cliff' — set SIMILARITY_THRESHOLD in retrieval_service.py")
        print("=" * 70)
    else:
        print("\nNo scores collected — check that the corpus was built correctly.")


if __name__ == "__main__":
    run_threshold_test()
