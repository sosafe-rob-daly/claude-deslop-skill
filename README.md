# claude-deslop-skill

A Claude Code skill that reduces AI slop in long-form prose output by targeting
its generative causes rather than by banning words. Ships with an evaluation
harness for measuring whether the skill is working on your model and prompts.

## What's in the box

```
.
├── skill/SKILL.md       # The skill itself (~125 lines, ~3,250 tokens)
├── eval/                # Build-measure-refine harness
│   ├── prompts/         # 21-prompt eval set spanning 4 output modes
│   ├── harness/         # Scoring, generation backends, reporting
│   ├── outputs/         # (gitignored) one .txt per prompt per run
│   ├── reports/         # (gitignored) markdown diffs of baseline vs treated
│   └── README.md        # Harness docs
└── README.md            # This file
```

## What the skill does

It's **invoke-only**: it activates only when you explicitly say things like:

- "use our deslop skill"
- "apply deslop"
- "deslop this"
- "use the anti-slop rules"

When invoked, it targets the generative causes of AI slop — padding to feel
complete, hedging to avoid being wrong, antithesis as rhythm, default-to-headers,
self-positioning ("to be honest," "let me be direct"), altitude-shifting in
summaries — rather than maintaining a banned-word list. It calibrates output
length to the substance of the input, not to the appearance of completeness.

See `skill/SKILL.md` for the full rules.

## Install as a Claude Code skill

```bash
mkdir -p ~/.claude/skills/deslop
cp skill/SKILL.md ~/.claude/skills/deslop/SKILL.md
```

Then in any Claude Code session, invoke with a trigger phrase:

> "Write a Q4 strategy memo using our deslop skill"
> "Reply to this customer email. Apply deslop."

## Measured effect (Claude, 21-prompt eval set)

Reply-only metrics (Insight-block contamination from Claude Code stripped):

| Metric | Baseline | Treated | Δ |
|---|---|---|---|
| Total reply words | 12,765 | 6,155 | **-52%** |
| Slop tic count (sum) | 33 | 7 | **-79%** |
| Em-dashes per 300w | 4.7 | 1.6 | **-65%** |
| Headers (avg per output) | 4.9 | 1.5 | -70% |
| Bullets (avg per output) | 16.8 | 6.5 | -61% |
| Over-correction guardrail trips | 0 | 0 | none |

19 of 21 prompts produced visibly less sloppy output. No over-correction
flagged. See `eval/reports/` for the full per-prompt and per-tic breakdown.

A parallel test on Qwen 2.5 72B via MLX showed only -13% word reduction and
a calibration regression — open-weight models with shorter system-prompt
adherence don't follow the skill faithfully. The skill is designed for
Claude-class models.

## Run the eval yourself

```bash
cd eval
pip install anthropic   # or skip, if using claude_cli backend

# Generate baseline (no skill) and treated (with SKILL.md as system prompt)
python -m harness.run baseline --backend claude_cli --label v0
python -m harness.run treated  --backend claude_cli --label iter-01

# Diff them
python -m harness.report --baseline outputs/baseline-<ts>-v0 \
                         --treated  outputs/treated-<ts>-iter-01
```

See `eval/README.md` for full backend options and workflow detail.

## Design philosophy

1. **Slop is statistical over-representation, not a word list.** Em-dashes,
   "honest," tricolons are fine in moderation; the failure is reaching for
   them as rhythm.
2. **Target generative causes, not surface symptoms.** One cause-level rule
   beats fifty banned words.
3. **Positive voice specification beats negative blocklists.** A small
   curated negatives list catches the highest-signal surface tells; the
   rest is positive direction.
4. **Separate Voice, Structure, Substance.** Different failure modes,
   different fixes.
5. **Calibrate output to input rigor.** Thin prompts invite padding. Don't
   manufacture volume.
6. **Avoid the over-correction trap.** Bludgeoning slop produces a NEW
   tell — clipped, choppy, "trying not to sound like AI." The target is
   variance and judgment, not terseness.

## License

MIT.
