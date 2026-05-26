"""Generate a comparison report between a baseline run and a treated run.

Reads all .txt outputs from both run directories, scores each, and
produces a markdown report with:
  - aggregate metrics (mean across all prompts, baseline vs treated)
  - per-prompt deltas (length, tic count, over-correction flag)
  - top n-grams that are NEWLY or MORE over-represented in treated
    (regressions) and those that have DROPPED (improvements)
  - calibration test scoreboard (do thin prompts shrink?)
  - over-correction watchlist (which outputs tripped the guardrail)

Usage:
  python -m harness.report --baseline outputs/baseline-... --treated outputs/treated-...
  python -m harness.report --baseline ... --treated ... --out reports/iter-01.md
"""

from __future__ import annotations
import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

from .score import score_text, over_correction_flag
from .tics import TICS


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_PATH = REPO_ROOT / "eval" / "prompts" / "prompts.json"
REPORTS_DIR = REPO_ROOT / "eval" / "reports"


def _load_prompts() -> dict[str, dict]:
    return {p["id"]: p for p in json.loads(PROMPTS_PATH.read_text())["prompts"]}


def _score_run(run_dir: Path) -> dict[str, dict]:
    """Score every .txt output in a run directory. Returns {prompt_id: metrics}."""
    out = {}
    for f in sorted(run_dir.glob("*.txt")):
        out[f.stem] = score_text(f.read_text())
    return out


def _aggregate(scored: dict[str, dict]) -> dict:
    """Mean across prompts for the scalar metrics we care about."""
    if not scored:
        return {}
    keys = [
        "word_count",
        "em_dashes_per_300w",
        "total_tic_count",
        "total_tic_rate_per_1kw",
        "mean_sentence_len",
        "sentence_len_stddev",
        "short_sentence_fraction",
        "type_token_ratio",
        "bullet_count",
        "heading_count",
    ]
    return {k: statistics.mean(s[k] for s in scored.values()) for k in keys}


def _aggregate_tics(scored: dict[str, dict]) -> dict[str, float]:
    """Mean per-prompt tic count for each tic id."""
    if not scored:
        return {}
    out = {}
    for t in TICS:
        out[t.id] = statistics.mean(s["tic_counts"][t.id] for s in scored.values())
    return out


def _aggregate_ngrams(scored: dict[str, dict], key: str = "top_content_bigrams", top_k: int = 30) -> Counter:
    """Sum n-gram counts across all outputs in a run."""
    c: Counter = Counter()
    for s in scored.values():
        for ng, n in s[key]:
            c[ng] += n
    return c


def _format_delta(b: float, t: float, fmt: str = ".2f", lower_is_better: bool = True) -> str:
    delta = t - b
    arrow = "↓" if delta < 0 else ("↑" if delta > 0 else "→")
    good = (delta < 0) == lower_is_better and delta != 0
    flag = "  " if delta == 0 else ("✓" if good else "✗")
    pct = f" ({delta / b * 100:+.0f}%)" if b else ""
    return f"{b:{fmt}} → {t:{fmt}} {arrow}{pct} {flag}"


def build_report(baseline_dir: Path, treated_dir: Path) -> str:
    prompts = _load_prompts()
    b_scored = _score_run(baseline_dir)
    t_scored = _score_run(treated_dir)

    common = sorted(set(b_scored) & set(t_scored))
    only_b = sorted(set(b_scored) - set(t_scored))
    only_t = sorted(set(t_scored) - set(b_scored))

    if not common:
        return f"# No common outputs between {baseline_dir.name} and {treated_dir.name}\n"

    b_agg = _aggregate({k: b_scored[k] for k in common})
    t_agg = _aggregate({k: t_scored[k] for k in common})
    b_tics = _aggregate_tics({k: b_scored[k] for k in common})
    t_tics = _aggregate_tics({k: t_scored[k] for k in common})

    # n-gram regressions/improvements (content bigrams give a cleaner signal)
    b_ng = _aggregate_ngrams({k: b_scored[k] for k in common})
    t_ng = _aggregate_ngrams({k: t_scored[k] for k in common})
    all_ng = set(b_ng) | set(t_ng)
    diffs = sorted(((ng, t_ng[ng] - b_ng[ng]) for ng in all_ng), key=lambda x: x[1])
    regressions = [(ng, d) for ng, d in diffs[::-1] if d > 1][:15]
    improvements = [(ng, d) for ng, d in diffs if d < -1][:15]

    # over-correction watch
    flagged = []
    for pid in common:
        flag, reason = over_correction_flag(t_scored[pid])
        if flag:
            flagged.append((pid, reason))

    # calibration test scoreboard
    calib_ids = [pid for pid, p in prompts.items() if p.get("calibration_test")]
    calib_rows = []
    for pid in calib_ids:
        if pid not in common:
            continue
        bw = b_scored[pid]["word_count"]
        tw = t_scored[pid]["word_count"]
        # for thin prompts, the right answer is "short or clarifying question"
        # we flag pass if treated is at most 60% of baseline length and under 120 words
        passed = tw <= max(40, int(bw * 0.6)) and tw <= 120
        calib_rows.append((pid, bw, tw, passed))

    # build the markdown
    lines: list[str] = []
    lines.append(f"# deslop eval report")
    lines.append("")
    lines.append(f"- **Baseline:** `{baseline_dir.name}` ({len(b_scored)} outputs)")
    lines.append(f"- **Treated:** `{treated_dir.name}` ({len(t_scored)} outputs)")
    lines.append(f"- **Common prompts scored:** {len(common)}")
    if only_b or only_t:
        lines.append(f"- ⚠ Missing in treated: {only_b} | Missing in baseline: {only_t}")
    lines.append(f"- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("## Aggregate metrics (mean across all prompts)")
    lines.append("")
    lines.append("| Metric | Baseline → Treated | Direction |")
    lines.append("|---|---|---|")
    rows = [
        ("Word count", "word_count", ".0f", True),
        ("Em-dashes per 300w", "em_dashes_per_300w", ".2f", True),
        ("Total tic count", "total_tic_count", ".1f", True),
        ("Tic rate per 1kw", "total_tic_rate_per_1kw", ".2f", True),
        ("Mean sentence length (w)", "mean_sentence_len", ".1f", False),
        ("Sentence length stddev", "sentence_len_stddev", ".1f", False),
        ("Short sentence fraction", "short_sentence_fraction", ".2f", False),
        ("Type-token ratio", "type_token_ratio", ".3f", False),
        ("Bullet count", "bullet_count", ".1f", True),
        ("Heading count", "heading_count", ".1f", True),
    ]
    for label, key, fmt, lower_is_better in rows:
        lines.append(f"| {label} | {_format_delta(b_agg[key], t_agg[key], fmt, lower_is_better)} | {'lower better' if lower_is_better else 'preserve'} |")
    lines.append("")
    lines.append("_Sentence length stddev and type-token ratio are the **over-correction guardrails**: if they drop sharply alongside the tic counts, the skill is producing lifeless prose rather than better prose._")
    lines.append("")

    lines.append("## Per-tic deltas (mean count per output)")
    lines.append("")
    lines.append("| Tic | Baseline | Treated | Δ |")
    lines.append("|---|---|---|---|")
    tic_lookup = {t.id: t for t in TICS}
    for tic_id in sorted(b_tics, key=lambda k: -(b_tics[k] - t_tics[k])):
        d = t_tics[tic_id] - b_tics[tic_id]
        sign = "✓" if d < 0 else ("✗" if d > 0 else "→")
        lines.append(f"| {tic_lookup[tic_id].label} | {b_tics[tic_id]:.2f} | {t_tics[tic_id]:.2f} | {d:+.2f} {sign} |")
    lines.append("")

    lines.append("## Calibration test scoreboard (thin prompts)")
    lines.append("")
    if calib_rows:
        lines.append("| Prompt | Baseline words | Treated words | Pass? |")
        lines.append("|---|---|---|---|")
        for pid, bw, tw, passed in calib_rows:
            mark = "✓ pass" if passed else "✗ FAIL"
            lines.append(f"| `{pid}` | {bw} | {tw} | {mark} |")
        passed_count = sum(1 for _, _, _, p in calib_rows if p)
        lines.append("")
        lines.append(f"**{passed_count}/{len(calib_rows)} thin prompts handled correctly.** Pass = treated ≤ 60% baseline AND treated ≤ 120 words.")
    else:
        lines.append("_No calibration-test prompts in this run._")
    lines.append("")

    lines.append("## Over-correction watchlist")
    lines.append("")
    if flagged:
        for pid, reason in flagged:
            lines.append(f"- `{pid}` — {reason}")
        lines.append("")
        lines.append("These outputs may be over-corrected (clipped/staccato). Inspect them before treating the iteration as a win.")
    else:
        lines.append("_None flagged._")
    lines.append("")

    lines.append("## N-gram regressions (more common in treated, possible new slop tics)")
    lines.append("")
    if regressions:
        for ng, d in regressions:
            lines.append(f"- `{' '.join(ng)}`  (+{d:.0f})")
    else:
        lines.append("_None significant._")
    lines.append("")

    lines.append("## N-gram improvements (less common in treated)")
    lines.append("")
    if improvements:
        for ng, d in improvements:
            lines.append(f"- `{' '.join(ng)}`  ({d:.0f})")
    else:
        lines.append("_None significant._")
    lines.append("")

    lines.append("## Per-prompt detail")
    lines.append("")
    lines.append("| Prompt | Mode | Baseline w | Treated w | Δ tics | Over-corrected? |")
    lines.append("|---|---|---|---|---|---|")
    for pid in common:
        meta = prompts.get(pid, {})
        bw = b_scored[pid]["word_count"]
        tw = t_scored[pid]["word_count"]
        dtics = t_scored[pid]["total_tic_count"] - b_scored[pid]["total_tic_count"]
        oc, _ = over_correction_flag(t_scored[pid])
        oc_mark = "⚠" if oc else ""
        lines.append(f"| `{pid}` | {meta.get('mode', '?')} | {bw} | {tw} | {dtics:+d} | {oc_mark} |")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--treated", type=Path, required=True)
    p.add_argument("--out", type=Path, help="optional output path; defaults to reports/<treated-id>.md")
    args = p.parse_args(argv)

    for d in (args.baseline, args.treated):
        if not d.exists():
            print(f"Run directory not found: {d}", file=sys.stderr)
            return 2

    report = build_report(args.baseline, args.treated)

    if args.out is None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        args.out = REPORTS_DIR / f"{args.treated.name}.md"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report)
    print(f"Report written: {args.out}")
    print()
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
