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

It also supports **voice calibration**: pass a sample of your own writing with
the invocation and it will match your voice rather than defaulting to generic
clean prose.

> "Rewrite this using the deslop skill. Here's a sample of my writing: [sample]"

See `skill/SKILL.md` for the full rules.

## Install as a Claude Code skill

```bash
mkdir -p ~/.claude/skills/deslop
cp skill/SKILL.md ~/.claude/skills/deslop/SKILL.md
```

Then in any Claude Code session, invoke with a trigger phrase:

> "Write a Q4 strategy memo using our deslop skill"
> "Reply to this customer email. Apply deslop."

## Measured effect (Claude Opus 4.6, 21-prompt eval set)

| Metric | Baseline | Treated | Δ |
|---|---|---|---|
| Words (avg per output) | 530 | 256 | **-52%** |
| Slop tic count (avg per output) | 0.9 | 0.4 | **-50%** |
| Headers (avg per output) | 10.9 | 1.3 | **-88%** |
| Bullets (avg per output) | 12.0 | 1.6 | **-87%** |
| Calibration tests passed | — | — | **4/5** |
| Over-correction guardrail trips | — | — | **0** |

All 21 prompts scored. No over-correction flagged. See `eval/reports/` for the
full per-prompt and per-tic breakdown.

The skill is designed for Claude-class models. Open-weight models with weaker
system-prompt adherence follow the rules less faithfully.

## Run the eval yourself

```bash
cd eval

# Generate baseline (no skill) and treated (with SKILL.md as system prompt)
# via SoSafe AI Platform (Bedrock, EU region) — requires VPN + AI_PLATFORM_API_KEY
AI_PLATFORM_API_KEY=<key> python3 -m harness.run baseline --backend sosafe --model claude-opus-4.6 --label opus-4.6
AI_PLATFORM_API_KEY=<key> python3 -m harness.run treated  --backend sosafe --model claude-opus-4.6 --label iter-01

# Or via direct Anthropic API (requires ANTHROPIC_API_KEY)
pip install anthropic
python3 -m harness.run baseline --backend anthropic --model claude-opus-4-7 --label v0
python3 -m harness.run treated  --backend anthropic --model claude-opus-4-7 --label iter-01

# Diff them
python3 -m harness.report --baseline outputs/baseline-<ts>-<label> \
                           --treated  outputs/treated-<ts>-<label>
```

**Current baseline:** Claude Opus 4.6 via SoSafe AI Platform (Bedrock, EU). Regenerate the
baseline if you switch models — the treated run must use the same model as baseline.

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
