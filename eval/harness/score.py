"""Deterministic text scoring. No API calls, no model. Pure function:
text in, metrics out.

Metrics produced:
  Length & shape:
    word_count, sentence_count, mean_sentence_len, sentence_len_stddev
    paragraph_count, mean_paragraph_len
  Surface tells:
    em_dashes, em_dashes_per_300w
    tic_counts (raw) + tic_rates (per 1000 words) for each curated tic
    total_tic_rate (sum, per 1000 words) -- single aggregate quality knob
  Structure:
    bullet_count, heading_count
    short_bullets (bullets shorter than 8 words)
  Lexical:
    type_token_ratio (lexical diversity, repetition proxy)
    top_bigrams, top_trigrams (for over-representation diffing across runs)
  Over-correction guardrails:
    sentence_len_stddev   -- collapsing variance => clipped/staccato
    short_sentence_fraction (sentences under 6 words / total)
    -- if mean_sentence_len < 10 AND stddev < 4 the output is probably
       over-corrected toward fragments.
"""

from __future__ import annotations
import re
import statistics
from collections import Counter
from .tics import TICS, count_tics, count_em_dashes


_WORD_RE = re.compile(r"\b[\w']+\b")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")
_PARA_SPLIT_RE = re.compile(r"\n\s*\n")
_BULLET_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+(.*)$", re.MULTILINE)
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE)
_STOPWORDS = frozenset(
    """a an the and or but if then so to of in on for with as by at from is are was were be been being
    this that these those it its i you he she we they them us our your their my me him her his hers theirs
    do does did done have has had having will would could should may might must can not no nor only just
    very really quite about into over under than then thus also too such which who whom whose what when where why how""".split()
)


def _words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def _sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    # naive split that handles the common cases; good enough for slop metrics
    sents = _SENT_SPLIT_RE.split(text)
    return [s.strip() for s in sents if s.strip()]


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def score_text(text: str, top_k_ngrams: int = 20) -> dict:
    words = _words(text)
    word_count = len(words)
    sents = _sentences(text)
    sent_lens = [len(_words(s)) for s in sents]
    paras = [p for p in _PARA_SPLIT_RE.split(text.strip()) if p.strip()]
    para_lens = [len(_words(p)) for p in paras]

    bullets = _BULLET_RE.findall(text)
    headings = _HEADING_RE.findall(text)
    bullet_word_counts = [len(_words(b[1])) for b in bullets]
    short_bullets = sum(1 for n in bullet_word_counts if n < 8)

    em = count_em_dashes(text)
    tic_counts = count_tics(text)
    tic_rates = {k: (1000.0 * v / word_count) if word_count else 0.0 for k, v in tic_counts.items()}

    lower_tokens = [w.lower() for w in words]
    content_tokens = [t for t in lower_tokens if t not in _STOPWORDS and len(t) > 2]
    bigrams = Counter(_ngrams(lower_tokens, 2))
    trigrams = Counter(_ngrams(lower_tokens, 3))
    content_bigrams = Counter(_ngrams(content_tokens, 2))

    ttr = (len(set(lower_tokens)) / len(lower_tokens)) if lower_tokens else 0.0

    short_sent_fraction = (sum(1 for n in sent_lens if n < 6) / len(sent_lens)) if sent_lens else 0.0

    return {
        "word_count": word_count,
        "sentence_count": len(sents),
        "mean_sentence_len": statistics.mean(sent_lens) if sent_lens else 0.0,
        "sentence_len_stddev": statistics.stdev(sent_lens) if len(sent_lens) > 1 else 0.0,
        "short_sentence_fraction": short_sent_fraction,
        "paragraph_count": len(paras),
        "mean_paragraph_len": statistics.mean(para_lens) if para_lens else 0.0,
        "bullet_count": len(bullets),
        "short_bullets": short_bullets,
        "heading_count": len(headings),
        "em_dashes": em,
        "em_dashes_per_300w": (300.0 * em / word_count) if word_count else 0.0,
        "tic_counts": tic_counts,
        "tic_rates_per_1kw": tic_rates,
        "total_tic_count": sum(tic_counts.values()),
        "total_tic_rate_per_1kw": sum(tic_rates.values()),
        "type_token_ratio": ttr,
        "top_bigrams": bigrams.most_common(top_k_ngrams),
        "top_trigrams": trigrams.most_common(top_k_ngrams),
        "top_content_bigrams": content_bigrams.most_common(top_k_ngrams),
    }


def over_correction_flag(metrics: dict) -> tuple[bool, str | None]:
    """Return (is_over_corrected, reason). Heuristic, not definitive.

    Triggers when sentence length has collapsed: low mean AND low variance,
    OR a very high fraction of short sentences.
    """
    m_mean = metrics["mean_sentence_len"]
    m_sd = metrics["sentence_len_stddev"]
    m_short = metrics["short_sentence_fraction"]

    if m_mean < 10 and m_sd < 4 and metrics["sentence_count"] >= 4:
        return True, f"mean sentence length collapsed ({m_mean:.1f}w, stddev {m_sd:.1f}w)"
    if m_short > 0.6 and metrics["sentence_count"] >= 4:
        return True, f"{m_short:.0%} of sentences under 6 words (fragment-heavy)"
    return False, None


def diff_metrics(baseline: dict, treated: dict) -> dict:
    """Compare two scored outputs. Used by the report."""
    def delta(key):
        b, t = baseline.get(key, 0), treated.get(key, 0)
        return {"baseline": b, "treated": t, "delta": t - b, "pct": ((t - b) / b * 100) if b else None}

    tic_diffs = {}
    for tic_id in baseline.get("tic_counts", {}):
        b = baseline["tic_counts"].get(tic_id, 0)
        t = treated["tic_counts"].get(tic_id, 0)
        tic_diffs[tic_id] = {"baseline": b, "treated": t, "delta": t - b}

    return {
        "word_count": delta("word_count"),
        "em_dashes": delta("em_dashes"),
        "em_dashes_per_300w": delta("em_dashes_per_300w"),
        "total_tic_count": delta("total_tic_count"),
        "total_tic_rate_per_1kw": delta("total_tic_rate_per_1kw"),
        "mean_sentence_len": delta("mean_sentence_len"),
        "sentence_len_stddev": delta("sentence_len_stddev"),
        "short_sentence_fraction": delta("short_sentence_fraction"),
        "type_token_ratio": delta("type_token_ratio"),
        "bullet_count": delta("bullet_count"),
        "heading_count": delta("heading_count"),
        "tic_diffs": tic_diffs,
    }
