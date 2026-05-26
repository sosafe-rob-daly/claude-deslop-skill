"""Run a generation pass over the prompt set.

Two modes:
  baseline -- no system prompt, captures default model behavior
  treated  -- system prompt = SKILL.md contents, captures with-skill behavior

Outputs are saved to eval/outputs/<run_id>/<prompt_id>.txt
A meta.json records the run config (backend, model, skill hash, timestamps).

Usage examples:
  # Headless Claude Code (uses your existing /login auth, no API key)
  python -m harness.run baseline --backend claude_cli --label v0
  python -m harness.run treated  --backend claude_cli --label iter-01

  # Anthropic API (requires ANTHROPIC_API_KEY)
  python -m harness.run baseline --backend anthropic --label v0
  python -m harness.run treated  --backend anthropic --label iter-01

  # Plumbing test with pre-written outputs (no model, no API)
  python -m harness.run baseline --backend stub --stub-dir samples/baseline
"""

from __future__ import annotations
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from .generators import get_backend, StubGenerator


# Resolve paths relative to the repo root so the CLI works from any cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_PATH = REPO_ROOT / "eval" / "prompts" / "prompts.json"
OUTPUTS_DIR = REPO_ROOT / "eval" / "outputs"
DEFAULT_SKILL_PATH = REPO_ROOT / "skill" / "SKILL.md"


def _load_prompts() -> list[dict]:
    return json.loads(PROMPTS_PATH.read_text())["prompts"]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _run_id(mode: str, label: str | None) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    suffix = f"-{label}" if label else ""
    return f"{mode}-{ts}{suffix}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["baseline", "treated"])
    p.add_argument("--backend", default="stub", help="generator backend: stub|echo|anthropic|claude_cli (default: stub)")
    p.add_argument("--skill", type=Path, default=DEFAULT_SKILL_PATH, help="path to SKILL.md (treated mode only)")
    p.add_argument("--stub-dir", type=Path, help="directory of hand-written outputs (stub backend only)")
    p.add_argument("--only", help="comma-separated prompt IDs to run (default: all)")
    p.add_argument("--label", help="optional suffix for the run id, e.g. 'iter-01'")
    p.add_argument(
        "--model",
        help="model id. Defaults: anthropic=claude-opus-4-7, claude_cli=Claude Code default",
    )
    p.add_argument("--claude-append", action="store_true", help="claude_cli: use --append-system-prompt (keeps Claude Code defaults) instead of --system-prompt (replace)")
    p.add_argument("--temperature", type=float, default=1.0, help="sampling temperature (anthropic backend)")
    p.add_argument("--max-tokens", type=int, default=4096, help="max tokens to generate (anthropic backend)")
    p.add_argument("--timeout", type=int, default=600, help="per-request timeout in seconds (claude_cli backend)")
    args = p.parse_args(argv)

    prompts = _load_prompts()
    if args.only:
        wanted = set(args.only.split(","))
        prompts = [pr for pr in prompts if pr["id"] in wanted]
        if not prompts:
            print(f"No prompts matched --only={args.only}", file=sys.stderr)
            return 2

    system = ""
    skill_hash = None
    if args.mode == "treated":
        if not args.skill.exists():
            print(f"--skill path not found: {args.skill}", file=sys.stderr)
            return 2
        system = args.skill.read_text()
        skill_hash = _hash_text(system)

    backend_kwargs: dict = {}
    if args.backend == "stub":
        if not args.stub_dir:
            print("--stub-dir is required for the stub backend", file=sys.stderr)
            return 2
        backend_kwargs["output_dir"] = args.stub_dir
    elif args.backend == "anthropic":
        if args.model:
            backend_kwargs["model"] = args.model
        backend_kwargs["max_tokens"] = args.max_tokens
        backend_kwargs["temperature"] = args.temperature
    elif args.backend == "claude_cli":
        if args.model:
            backend_kwargs["model"] = args.model
        backend_kwargs["append"] = args.claude_append
        backend_kwargs["timeout_s"] = args.timeout

    gen = get_backend(args.backend, **backend_kwargs)

    run_id = _run_id(args.mode, args.label)
    out_dir = OUTPUTS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve effective model id (the user may have relied on the backend default).
    effective_model = args.model or getattr(gen, "model", None)
    meta = {
        "run_id": run_id,
        "mode": args.mode,
        "backend": args.backend,
        "model": effective_model,
        "temperature": args.temperature if args.backend == "anthropic" else None,
        "claude_append": args.claude_append if args.backend == "claude_cli" else None,
        "skill_hash": skill_hash,
        "timestamp": time.time(),
        "prompt_ids": [pr["id"] for pr in prompts],
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    if args.mode == "treated":
        (out_dir / "system_prompt.md").write_text(system)

    failures = 0
    for pr in prompts:
        if isinstance(gen, StubGenerator):
            gen.set_current_id(pr["id"])
        try:
            out = gen.generate(pr["prompt"], system=system)
        except Exception as e:
            print(f"  [{pr['id']}] FAILED: {e}", file=sys.stderr)
            failures += 1
            continue
        (out_dir / f"{pr['id']}.txt").write_text(out)
        words = len(out.split())
        print(f"  [{pr['id']}] {words}w  ({pr['mode']})")

    print(f"\nRun saved: {out_dir}")
    if failures:
        print(f"{failures} prompt(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
