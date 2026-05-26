# deslop eval harness

Local-runnable harness to measure whether the `deslop` skill is actually
reducing slop, without over-correcting into clipped/lifeless prose.

## Layout

```
eval/
├── prompts/prompts.json     # the eval set (21 prompts, 4 modes, 5 thin/calibration tests)
├── outputs/<run-id>/        # generations: one .txt per prompt + meta.json
├── reports/<run-id>.md      # comparison reports (baseline vs treated)
└── harness/
    ├── tics.py              # curated regex tics, kept in sync with SKILL.md
    ├── score.py             # deterministic metrics (no API)
    ├── generators.py        # backends: stub | echo | anthropic | claude_cli
    ├── run.py               # CLI to generate outputs
    ├── report.py            # CLI to diff two runs into a markdown report
    └── judge.py             # optional judge-model pass (Anthropic API)
```

## What we measure

Deterministic (no API):
- **Length & shape:** word/sentence/paragraph counts, mean sentence length and stddev.
- **Surface tells:** em-dash density (per 300w), counts and rates for each of the 11 curated tics.
- **Structure:** bullet count, short-bullet count, heading count.
- **Lexical:** type-token ratio (repetition proxy).
- **N-gram comparison:** top bigrams/trigrams across the run, used to spot regressions (n-grams more common in treated than baseline).
- **Over-correction guardrail:** flags any output where mean sentence length collapses below 10 words with stddev below 4, OR where over 60% of sentences are under 6 words.

Optional (judge model, costs API calls):
- `slop_score` (1-10): how slop-y does the output read?
- `lifelessness_score` (1-10): has it been over-corrected into clipped fragments? **This is the trap we're guarding against.**
- `top_issue`: one-line free-text diagnosis.

## Backends

| Backend | When to use | Setup |
|---|---|---|
| `claude_cli` | **Recommended for local iteration.** Uses your existing Claude Code auth, no API key. | `npm install -g @anthropic-ai/claude-code` and `/login` |
| `anthropic` | Production-grade evaluation against any Claude model with explicit control. | `pip install anthropic` + `export ANTHROPIC_API_KEY=...` |
| `stub` | Plumbing tests with hand-written outputs. No model needed. | Drop `.txt` files in a directory |
| `echo` | Sanity-check the orchestrator. Returns the prompt back. | Nothing |

## Workflow — claude_cli (recommended for local iteration)

```bash
# 1. Baseline once (no skill)
python -m harness.run baseline --backend claude_cli --label v0

# 2. Treated (current SKILL.md as system prompt)
python -m harness.run treated --backend claude_cli --label iter-01

# 3. Diff
python -m harness.report \
  --baseline outputs/baseline-<ts>-v0 \
  --treated  outputs/treated-<ts>-iter-01

# 4. (Optional) Judge pass — costs Anthropic API tokens
python -m harness.judge outputs/treated-<ts>-iter-01

# 5. Read the report, refine SKILL.md, re-run step 2 with --label iter-02.
```

## Workflow — Anthropic API

For full control over the model and parameters:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m harness.run baseline --backend anthropic --model claude-opus-4-7 --label v0
python -m harness.run treated  --backend anthropic --model claude-opus-4-7 --label iter-01
python -m harness.report --baseline outputs/baseline-<ts>-v0 --treated outputs/treated-<ts>-iter-01
python -m harness.judge outputs/treated-<ts>-iter-01
```

## Plumbing tests (no model, no API)

The stub backend reads pre-written outputs from disk. Useful for
validating the scoring pipeline against hand-written examples or for
testing harness changes without burning model time:

```bash
mkdir -p samples/baseline samples/treated
# hand-write outputs as samples/baseline/qa-01-postgres-vs-dynamo.txt
# and samples/treated/qa-01-postgres-vs-dynamo.txt
python -m harness.run baseline --backend stub --stub-dir samples/baseline --only qa-01-postgres-vs-dynamo
python -m harness.run treated  --backend stub --stub-dir samples/treated  --only qa-01-postgres-vs-dynamo
python -m harness.report --baseline outputs/baseline-... --treated outputs/treated-...
```

## Interpreting the report

The report has six sections. Read them in this order:

1. **Aggregate metrics.** Quick read on what moved. `total_tic_rate_per_1kw` is the headline number for slop reduction.
2. **Per-tic deltas.** Which tics actually dropped. If a tic didn't drop, the rule for it isn't landing — find out why.
3. **Calibration test scoreboard.** The thin prompts. If these don't shrink, the calibration rule failed regardless of what else moved.
4. **Over-correction watchlist.** Read every flagged output by hand. If the skill is shipping fragment-heavy garbage, the metrics will say "less slop" but the writing is worse.
5. **N-gram regressions.** Patterns that are *new* in treated. Sometimes the skill displaces one tic into another — this is how you catch it.
6. **Per-prompt detail.** For drilling into specific failures.

A successful iteration looks like: tic rates drop ≥30%, calibration tests pass, over-correction watchlist stays empty, sentence stddev within ~20% of baseline, no new n-gram regressions.

## Reply-only audit (Claude Code env contamination)

If you generate via `claude_cli` and your session has an active output-style
(like `explanatory`), every output will include extra meta-prose (e.g.
`★ Insight ───` blocks) that inflates word counts and pollutes tic scores.
Strip them before measuring:

```python
import re
text = re.sub(r"`★ Insight ─+`.*?`─+`", "", text, flags=re.DOTALL)
```

The numbers we cite for the iteration 0 result (~-52% words, -79% tics on
Claude) are reply-only — they're what a production API deployment would see.

## What's deliberately not here

- No fixed scoring threshold for "good enough." Slop is a moving target; the right question is whether the *next* iteration improves on the previous one.
- No ground-truth outputs to grade against. Slop is distributional; there's no single right answer.
- No automated CI. This is a development loop, not a regression gate.
- No local-model backend (MLX/Ollama). Earlier iterations showed weaker open-weight models don't follow long system prompts faithfully enough for the eval to be informative. The skill is designed for Claude-class models.
