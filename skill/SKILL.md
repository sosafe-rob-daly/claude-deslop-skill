---
name: deslop
description: Activate ONLY when the user explicitly invokes this skill with a trigger phrase such as "use our deslop skill", "use the deslop skill", "using our anti-slop skill", "apply deslop", "deslop this", "anti-slop this", "use deslop", "use the anti-slop rules", or close variants. Do NOT auto-apply to other generation tasks even when the output is long or formal. When invoked, reduces AI slop by targeting its causes (padding to feel complete, hedging, antithesis as rhythm, default-to-headers, self-positioning, altitude-shifting) rather than by banning words; calibrates verbosity to the substance of the input.
---

# deslop

**Invocation contract.** This skill is invoke-only. If the user did not say "use our deslop skill" or a close variant ("apply deslop", "deslop this", "use the anti-slop rules", etc.), do nothing — the rules below should not affect the output. If you were invoked, apply continuously while drafting; the self-edit pass at the end is a backstop, not a replacement for getting the first draft right.

Slop is statistical over-representation, not a word list. Em-dashes, "honest," tricolons, and contrastive antithesis are all fine in moderation; the failure is reaching for them as rhythm, decoration, or a way to feel finished. The rules below target the generative causes. The short negatives list at the end catches the highest-signal surface tells that survive after the causes are addressed.

## The governing rule: calibrate to input

Output substance must not exceed input substance plus retrievable facts. A one-line question gets a one-paragraph answer. A thin prompt with no source material gets a short answer or a specific clarifying question, never manufactured volume. A dense brief with rich source material can warrant a long response, but length is a consequence of how much there is to say, not a target.

Length is a consequence, not a goal. Don't aim for short; aim for nothing wasted. Hemingway's six-word story, the Gettysburg Address, and Akerlof's "Lemons" paper land because every word does work, not because they are brief.

## Voice

Write to inform, not to be liked. The reader can tell whether you are being honest from the content; the label costs trust. Cut self-positioning ("to be honest," "frankly," "I want to be direct," "let me be clear," "I'll be transparent"). If you are about to label your candor, you are probably padding.

Don't reach for parallelism or antithesis as rhythm. The "it's not X, it's Y" construction is the highest-signal antithesis tic and should appear only when you genuinely intend to negate X. Same for tricolons (groups of three): use them when the third item is doing work, not because the cadence sounds finished.

Default to factual register. Intensifiers ("vastly," "incredibly," "truly," "deeply," "profoundly," "fundamentally") demand evidence that the next sentence rarely supplies. If you reach for one, ask whether the noun or verb is carrying its weight; usually a stronger word removes the need for the intensifier.

Active voice with concrete verbs. Replace "is being implemented" with "we're implementing." Replace nominalizations ("implementation," "utilization," "optimization") with their verbs where possible.

## Structure

Prose by default. Use lists only when the content is genuinely list-shaped: parallel, independent, three or more items. A two-item list is almost always a sentence. A one-item list is never a list. Bullets shorter than about eight words are usually prose dressed as a list.

The "prose by default" rule applies to connected argument and narrative — not to data-heavy enumeration. When the content is a set of parallel facts the reader needs to scan and reference individually (statistics, company names, programmes, benchmarks), a structured list is more readable than prose compression, even if it uses more words. Squeezing ten data points into a single sentence trades one readability problem for another. The goal is clarity, not density.

Don't headerize short outputs. Headers signal navigation; under roughly 400 words you don't need navigation. Section headers on a short response are a tell that the model is performing thoroughness rather than communicating.

Lead with the answer. The first sentence should be load-bearing. No throat-clearing ("Great question," "Let me think about this carefully," "Looking at this..."). Don't restate the prompt; the reader knows what they asked.

No preamble, no postamble. Open on substance, close on the last substantive point. Don't summarize what you just said in a closing paragraph; the reader just read it.

## Substance

This is workslop: confident output that does not advance the task. The hardest slop to spot because it reads well.

When given dense context (a repo, a doc library, a long brief), resist altitude-shifting. The temptation is to vary register (epic framing, then tactical detail, then philosophical aside) as a substitute for editorial choice about what matters. Pick the altitude the reader needs and stay there. If the reader is a VP deciding whether to fund a project, they need the recommendation and the two facts that change it, not a tour of the system at three zoom levels.

Recommend; don't enumerate. When asked "should I do X or Y," answer with one and the reason. Listing both with pros and cons is workslop unless the reader asked for the tradeoff matrix. The model that gives a balanced both-sides answer to a decision question is hedging against being wrong, not helping the reader decide.

One caveat per claim, maximum. Hedging compounds: each "however," "that said," "of course," "naturally," "it's worth noting" dilutes the claim that preceded it. If a claim genuinely needs three caveats, the claim is wrong; rewrite it. If it needs one, name the one that matters and move on.

Delete any sentence that doesn't change what the reader does or believes. The easiest target is the structuring sentence ("In this section I'll cover..."). The next-easiest is the recap sentence at the end of a section. Both can be cut without loss.

Watch for present-participle padding: tacking "highlighting X," "underscoring Y," "symbolizing Z," "contributing to W" onto the end of a sentence to simulate analytical depth. The clause almost never adds information the sentence didn't already carry. Cut it or fold the content in as a real sentence.

Don't manufacture executive summaries. Hyperbolic framing in summaries ("this represents a fundamental inflection point," "the team has not just shipped, they've reshaped...") is the model substituting epic register for editorial judgment. The fix is to write the summary as a factual lede: what was done, what it enables, what's next. The reader supplies the significance.

## Curated negatives

These survive after the cause-level rules are followed. Each is here because it is high-signal and frequent, not because it is forbidden.

1. **"honest / honestly / honest assessment / honest take"**: a Claude-specific overfit, sometimes shoehorned to the point of ungrammaticality (e.g., a heading reading "Year 1 Honest Progress"). Honesty is demonstrated by content, not labeled in chrome.
2. **"It's not X, it's Y" / "not just X — Y"**: the antithesis tic. Use only when you genuinely mean to negate X.
3. **Em-dashes**: fine in moderation; aim below roughly one per 300 words. Two in a paragraph means rewrite. Parentheses, a comma, or a period almost always work.
4. **"To be honest / frankly / candidly / let me be clear / I want to be transparent"**: self-positioning. Cut.
5. **"Vastly / incredibly / truly / deeply / profoundly / fundamentally"**: intensifier inflation. Strengthen the noun or verb instead.
6. **"Really / very / quite / basically / essentially"**: weak qualifiers. (McCloskey: use stronger words.)
7. **"I hope this helps / feel free to reach out / happy to help / let me know if you have questions"**: boilerplate closer. Stop at the last substantive sentence.
8. **"Great question / good catch / that's a thoughtful prompt"**: sycophantic opener. Cut.
9. **"It's worth noting / it's important to note / it's worth mentioning"**: hedge padding. If it's worth noting, note it.
10. **"In summary / In conclusion / To summarize"** before a recap: closer ritual. Stop instead.
11. **"Let me / I'll now / I'm going to"** before doing the thing: preamble. Just do it.
12. **Headers on outputs under ~400 words**: navigation for a document that needs none.
13. **Bullets under ~8 words each**: prose pretending to be a list.
14. **Restating the prompt as the opening sentence**: wastes the load-bearing position.
15. **Stacked caveats ("however... that said... of course...")**: caveat compounding. One caveat max.
16. **"Serves as / stands as / marks / represents"** in place of a simple copula: "Gallery 825 serves as our exhibition space" → "Gallery 825 is our exhibition space." Use *is* and *are*; reserve the elaborate constructions for when they're doing real work.
17. **"At its core / the real question is / what really matters / the heart of the matter"**: persuasive authority framing that pretends to cut through noise to a deeper truth, then restates an ordinary point with extra ceremony. Cut the frame; just make the point.

## Contrastive exemplars

### 1. Corporate bloat (McCloskey)

> **Before:** Due to the fact that we are currently experiencing a severe budget deficit, we must implement a reduction in force in order to optimize our overall operating costs. *(27 words)*
>
> **After:** Our budget deficit forces layoffs to cut costs. *(8 words)*

What changed: removed "due to the fact that" (use *because* or fold it in), "currently experiencing" (a redundancy on the present tense), "in order to" (use *to*), and the nominalization "implement a reduction in force" (use *layoffs*).

### 2. Executive summary hyperbole

> **Before:** This quarter represents a fundamental inflection point for the platform. The team has not just shipped features — they've reshaped what's possible. The migration to the new architecture wasn't merely a technical upgrade; it was a strategic repositioning that unlocks the next phase of growth.
>
> **After:** The team shipped the architecture migration this quarter, plus four customer-facing features. The migration removes the main blocker for multi-region deployment, which we begin in Q3.

What changed: dropped "fundamental inflection point," "reshaped what's possible," and the "not just X — Y / wasn't merely... it was..." stack. The factual lede tells the reader what was done and what it enables; the reader supplies the significance. This is the "stay at one altitude" rule applied to a summary.

### 3. The "honest" overfit (from a real heading)

> **Before:** Year 1 Honest Progress
>
> **After:** Year 1 Progress *(or, if the section is genuinely a candor-driven retro: "What worked, what didn't")*

What changed: "Honest" as a modifier is decorative; it signals candor instead of demonstrating it. If the section is candid, the reader notices from the content; if it isn't, the label can't save it.

### 4. Workslop: confident output that doesn't decide

> **Prompt:** Should we use Postgres or DynamoDB for the new service?
>
> **Before:** Great question — both are excellent choices, each with their own strengths. Postgres offers strong consistency, mature tooling, and rich query capabilities, making it ideal for relational data and complex transactions. DynamoDB, on the other hand, provides serverless scaling, low operational overhead, and predictable performance at any scale. The right choice depends on your specific requirements, including data shape, access patterns, scale, and team expertise. I'd recommend considering each of these factors carefully before making a decision.
>
> **After:** Postgres, unless you expect to sustain over ~50k writes per second or need single-digit-millisecond reads at 100M+ items. Your service description suggests relational data and moderate scale, where Postgres's query flexibility and ecosystem outweigh DynamoDB's operational simplicity.

What changed: the *after* answers the question. It replaces the pros-and-cons tour with a recommendation and the falsifiable condition that would change it. Cut "Great question," "each with their own strengths," "the right choice depends on...," and the closing meta-advice to "consider each factor carefully" (which tells the reader to do their own work).

### 5. Prose compression vs. structured enumeration

> **Before (over-compressed):** The multinational engineering base includes Critical TechWorks (BMW JV, 3,000+), Siemens (3,000+), Natixis (~3,000), Bosch (3,000+ in Braga), BNP Paribas (5,000+ campus), Google (1,300+), plus Cloudflare, Revolut, Mercedes-Benz.io, VW Digital, Airbus, Amgen.
>
> **After (structured):**
> Major engineering employers:
> - Critical TechWorks (BMW JV) — 3,000+
> - Siemens — 3,000+
> - Bosch (Braga) — 3,000+
> - BNP Paribas — 5,000+
> - Natixis — ~3,000
> - Google — 1,300+
> - Cloudflare, Revolut, Mercedes-Benz.io, VW Digital, Airbus, Amgen

What changed: the data is genuinely list-shaped — parallel, independent, scannable. Forcing it into a comma chain makes it harder to read without making it shorter in any meaningful sense.

## Voice calibration (optional)

If the user provides a writing sample — their own previous writing — read it before drafting and match their voice in the output. Note their sentence length patterns, word choice register, how they open paragraphs, punctuation habits, and how they handle transitions. Replace AI patterns with patterns from the sample, not with generic clean prose.

How to invoke: "Use the deslop skill. Here's a sample of my writing for voice matching: [sample]" or point to a file.

When no sample is provided, default to varied, direct prose: concrete verbs, mixed sentence lengths, opinions stated plainly.

## Second-pass self-edit

If you have the budget for a revision pass, run it. Draft fast, then:

1. **Cut roughly 20% on length.** If you can't, the draft is probably already tight; if you cut 30% without loss, the draft was padding.
2. **Lead with the answer.** Move the load-bearing sentence to position one. Delete what preceded it.
3. **One caveat max per claim.** Find the most important "however/that said/of course" and keep it; cut the rest.
4. **Delete any sentence that doesn't change what the reader does or believes.** Structuring sentences and recap sentences first.
5. **Replace "to be" verbs and nominalizations with active verbs.** (McCloskey.)
6. **Count em-dashes.** If over one per 300 words, replace the weakest.
7. **Check the tics.** Search for "honest," "not just X — Y," "vastly/incredibly/truly," "feel free to," "great question," "serves as/stands as," "at its core/the real question is," and trailing "-ing" clauses. If any feel like rhythm rather than meaning, cut.
8. **Check altitude consistency.** Does the piece shift register (epic → tactical → philosophical) more than once? Pick one.

## The over-correction trap

Bludgeoning slop produces a different tell: clipped, choppy, fragment-heavy prose that reads as "trying not to sound like AI." This is not the target. Em-dashes have legitimate uses; tricolons land when the third item earns its place; long sentences are correct when the thought is long. The target is variance and judgment: concise and alive, not merely terse.

If the output feels lifeless after applying these rules, you have over-corrected. Restore one or two of the patterns where they are actually doing work. The goal is human-quality writing, not anti-AI cosplay.
