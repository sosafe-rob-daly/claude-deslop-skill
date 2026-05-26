"""Optional judge-model pass. Separate from deterministic scoring because
judge results are noisy, expensive, and shouldn't be on the hot loop.

The judge rates each output on two axes:
  slop_score (1-10): 1 = clean human-quality, 10 = worst AI padding/slop
  lifelessness_score (1-10): 1 = alive/varied, 10 = clipped/robotic
  top_issue: short string describing the dominant problem

These two axes are intentionally separate. The whole point of the
over-correction trap is that low slop != good writing. Optimizing for
slop_score alone produces lifelessness_score regressions.

Default judge model is claude-haiku-4-5 (cheap, fast, capable enough
for this task). Smaller models (e.g. Qwen 2.5 7B) tend to be too
lenient at this quality level; a Sonnet-class judge is the floor for
reliable discrimination on already-clean outputs.

Usage:
  python -m harness.judge <run_dir>
  python -m harness.judge <run_dir> --model claude-sonnet-4-6
"""

from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

from .generators import AnthropicGenerator, Generator


JUDGE_SYSTEM_PROMPT = """You rate AI-generated writing on two independent axes.

slop_score (1-10): How much does this output suffer from AI slop -- padding to feel complete, hedging to avoid being wrong, sycophancy, boilerplate openers/closers, over-deployed em-dashes, "honest" framing, "it's not X, it's Y" antithesis as rhythm, hyperbolic framing, restating the prompt, recapping at the end?
  1 = clean human writing, no slop signals
  10 = textbook AI slop on every dimension

lifelessness_score (1-10): How clipped, robotic, or over-corrected does the writing feel? Has it lost natural rhythm? Are sentences uniformly short? Has the writer stripped legitimate em-dashes, tricolons, and longer sentences to the point that the prose feels like an anti-AI cosplay?
  1 = alive, varied, natural rhythm
  10 = stilted, fragmenty, "trying not to sound like AI"

These are independent. A piece can score low on both (good) or score low on slop AND high on lifelessness (the over-correction failure mode we want to avoid).

top_issue: one short sentence (under 20 words) describing the dominant problem. If none, "none".

Output ONLY valid JSON, no preamble: {"slop_score": int, "lifelessness_score": int, "top_issue": "..."}"""


def _extract_json(body: str) -> dict:
    """Parse the judge model's response. Strips common code fences and noise."""
    body = body.strip()
    if body.startswith("```"):
        body = body.split("```")[1]
        if body.startswith("json"):
            body = body[4:]
        body = body.strip()
    if not body.startswith("{"):
        start = body.find("{")
        end = body.rfind("}")
        if start >= 0 and end > start:
            body = body[start : end + 1]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"slop_score": -1, "lifelessness_score": -1, "top_issue": f"PARSE_FAIL: {body[:120]}"}


def judge_one(gen: Generator, text: str) -> dict:
    user_msg = f"Output to rate:\n\n---\n{text}\n---"
    response = gen.generate(user_msg, system=JUDGE_SYSTEM_PROMPT)
    return _extract_json(response)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--model", default="claude-haiku-4-5-20251001", help="judge model id (default: claude-haiku-4-5)")
    p.add_argument("--only", help="comma-separated prompt IDs")
    args = p.parse_args(argv)

    if not args.run_dir.exists():
        print(f"Run dir not found: {args.run_dir}", file=sys.stderr)
        return 2

    gen = AnthropicGenerator(model=args.model, max_tokens=200, temperature=0)

    wanted = set(args.only.split(",")) if args.only else None
    results: dict[str, dict] = {}
    for f in sorted(args.run_dir.glob("*.txt")):
        if wanted and f.stem not in wanted:
            continue
        text = f.read_text()
        if not text.strip():
            continue
        try:
            res = judge_one(gen, text)
        except Exception as e:
            print(f"  {f.stem}: FAILED ({e})")
            results[f.stem] = {"slop_score": -1, "lifelessness_score": -1, "top_issue": f"REQUEST_FAIL: {e}"}
            continue
        results[f.stem] = res
        slop = res.get("slop_score", "?")
        life = res.get("lifelessness_score", "?")
        issue = res.get("top_issue", "")[:80]
        print(f"  {f.stem}: slop={slop!s:>3}  life={life!s:>3}  {issue}")

    out_path = args.run_dir / "judge.json"
    out_path.write_text(json.dumps({
        "model": args.model,
        "timestamp": time.time(),
        "results": results,
    }, indent=2))
    print(f"\nWritten: {out_path}")

    valid = [r for r in results.values() if isinstance(r.get("slop_score"), int) and r["slop_score"] > 0]
    if valid:
        mean_slop = sum(r["slop_score"] for r in valid) / len(valid)
        mean_life = sum(r["lifelessness_score"] for r in valid) / len(valid)
        print(f"Mean slop: {mean_slop:.2f}   Mean lifelessness: {mean_life:.2f}   (n={len(valid)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
