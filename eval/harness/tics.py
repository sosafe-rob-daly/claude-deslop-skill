"""Curated negatives matching SKILL.md's list. Each tic is the regex form,
paired with the rule it tests and a short reason. Counts are case-insensitive
unless the pattern is intentionally case-sensitive.

Keep this in sync with SKILL.md "Curated negatives" section. The eval reports
on each of these per output, so they double as the empirical check on which
rules are actually working.
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Tic:
    id: str
    label: str
    pattern: re.Pattern
    rule: str  # one-line description of why it's a tic


TICS: tuple[Tic, ...] = (
    Tic(
        "honest",
        '"honest" framing',
        re.compile(r"\bhonest(ly|\s+(assessment|take|truth|opinion))?\b", re.IGNORECASE),
        "Claude over-deploys 'honest' to the point of ungrammaticality. Demonstrate, don't label.",
    ),
    Tic(
        "antithesis",
        '"not just X, Y" antithesis',
        re.compile(r"\bnot\s+(just|merely|only)\b[^.!?]{1,80}?\b(but|—|,)", re.IGNORECASE),
        "Antithesis as rhythm. Use only when you genuinely intend to negate X.",
    ),
    Tic(
        "self_positioning",
        "self-positioning phrases",
        re.compile(
            r"\b(to be honest|frankly|candidly|let me be (clear|direct|honest)|i want to be (transparent|clear|direct)|in all honesty)\b",
            re.IGNORECASE,
        ),
        "Self-positioning. If honest, the reader can tell from content.",
    ),
    Tic(
        "intensifier_inflation",
        "intensifier inflation",
        re.compile(
            r"\b(vastly|incredibly|truly|deeply|profoundly|fundamentally|remarkably|extraordinarily|tremendously)\b",
            re.IGNORECASE,
        ),
        "Intensifier inflation. Strengthen the noun/verb instead.",
    ),
    Tic(
        "weak_qualifiers",
        "weak qualifiers",
        re.compile(r"\b(really|very|quite|basically|essentially|literally|actually)\b", re.IGNORECASE),
        "McCloskey: weak qualifiers. Use stronger words.",
    ),
    Tic(
        "boilerplate_closers",
        "boilerplate closers",
        re.compile(
            r"\b(i hope this helps|feel free to (reach out|ask|contact)|happy to help|let me know if you have (any )?questions|please don't hesitate to)\b",
            re.IGNORECASE,
        ),
        "Boilerplate closer. Stop at the last substantive sentence.",
    ),
    Tic(
        "sycophancy",
        "sycophantic openers",
        re.compile(
            r"\b(great question|good catch|thoughtful (question|prompt)|excellent (question|point)|that's a (great|fantastic|wonderful) (question|point))\b",
            re.IGNORECASE,
        ),
        "Sycophantic opener. Cut.",
    ),
    Tic(
        "worth_noting",
        '"worth noting" hedge padding',
        re.compile(r"\b(it'?s\s+(worth|important)\s+(noting|mentioning|to note)|worth\s+(noting|mentioning) that)\b", re.IGNORECASE),
        "Hedge padding. If it's worth noting, just note it.",
    ),
    Tic(
        "closer_ritual",
        '"in summary/conclusion" recap ritual',
        re.compile(r"\b(in\s+(summary|conclusion|short)|to\s+(summarize|conclude|sum up)|overall,)\b", re.IGNORECASE),
        "Closer ritual that repeats what was just said.",
    ),
    Tic(
        "preamble",
        "preamble before doing the thing",
        re.compile(r"\b(let me|i'?ll now|i'?m going to|i will now|let's (start|begin) by|first,?\s+(let me|i'?ll))\b", re.IGNORECASE),
        "Preamble. Just do it.",
    ),
    Tic(
        "stacked_caveats",
        "stacked caveats (per output)",
        re.compile(r"\b(however|that said|having said that|on the other hand|with that said|nevertheless|nonetheless|of course|naturally)\b", re.IGNORECASE),
        "Each caveat dilutes the prior claim. One per output is fine; stacking is the tell.",
    ),
)


def count_tics(text: str) -> dict[str, int]:
    """Return raw counts for each tic id."""
    return {t.id: len(t.pattern.findall(text)) for t in TICS}


def count_em_dashes(text: str) -> int:
    """Count em-dash (U+2014) occurrences. Excludes the ASCII double-hyphen."""
    return text.count("—")
