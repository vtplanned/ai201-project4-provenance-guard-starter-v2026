"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures ───────────────────────────────────────────────────────
#
# Directions, written down because the combining step depends on them:
#   sentence_length_spread  HIGH = uneven sentences = more human
#   type_token_ratio        HIGH = varied vocabulary = more human
#   punctuation_density     HIGH = lots of non-full-stop punctuation = more human
# `style_signal` flips each one so the final number reads "higher = more AI".

# Below this many sentences a spread means nothing, so style_signal ignores it.
MIN_SENTENCES_FOR_SPREAD = 3
# Type-token ratio is measured over windows this long so a 300-word text isn't
# punished for repeating "the" more than a 60-word one.
TTR_WINDOW = 50


def sentence_length_spread(text: str) -> float:
    """
    Coefficient of variation of sentence length: stdev / mean, in words.

    Roughly 0.0 for sentences that march in step, 0.6 and up for lumpy human
    prose. A single sentence has no spread, so it returns 0.0; style_signal
    checks the sentence count itself and doesn't treat that 0.0 as evidence.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return round(statistics.stdev(lengths) / mean, 4) if mean else 0.0


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, averaged over 50-word windows (a moving
    average type-token ratio). Texts shorter than one window use the plain ratio.
    """
    w = words(text)
    if not w:
        return 0.0
    if len(w) <= TTR_WINDOW:
        return round(len(set(w)) / len(w), 4)
    step = max(1, TTR_WINDOW // 2)
    ratios = [
        len(set(w[i:i + TTR_WINDOW])) / TTR_WINDOW
        for i in range(0, len(w) - TTR_WINDOW + 1, step)
    ]
    return round(sum(ratios) / len(ratios), 4)


# Everything except the full stop and the apostrophe. Commas, semicolons,
# colons, dashes, brackets, quotes, question and exclamation marks all vary more
# between writers than full stops do.
_PUNCT = re.compile(r"[,;:!?\u2014\u2013()\"\u201c\u201d\u2026]|(?<=\s)-(?=\s)|--")


def punctuation_density(text: str) -> float:
    """Non-full-stop punctuation marks per word."""
    n = len(words(text))
    if n == 0:
        return 0.0
    return round(len(_PUNCT.findall(text)) / n, 4)


def _ramp(value: float, human_end: float, ai_end: float) -> float:
    """Map a raw measure onto 0 (human end) .. 1 (AI end), clipped, linear."""
    t = (value - human_end) / (ai_end - human_end)
    return min(max(t, 0.0), 1.0)


# (human_end, ai_end) for each measure: the raw value that scores 0.0 and 1.0.
# Chosen from the calibration texts in the README, not from theory.
SPREAD_RANGE = (0.75, 0.25)
TTR_RANGE = (0.90, 0.65)
PUNCT_RANGE = (0.14, 0.04)

# How much each measure counts inside the style score. Sentence rhythm is the
# strongest of the three; the other two are weaker and noisier.
STYLE_WEIGHTS = {"spread": 0.5, "ttr": 0.25, "punct": 0.25}


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0-1 score. **Higher means more likely AI.**

    Each measure is flipped where needed and scaled to 0-1 with `_ramp`, then
    the three are averaged with STYLE_WEIGHTS. If the text has fewer than
    MIN_SENTENCES_FOR_SPREAD sentences the spread has nothing to say, so it
    drops out and the other two are re-weighted instead of a fake 0.0 pulling
    the score toward AI.
    """
    parts = {
        "ttr": _ramp(type_token_ratio(text), *TTR_RANGE),
        "punct": _ramp(punctuation_density(text), *PUNCT_RANGE),
    }
    if len(sentences(text)) >= MIN_SENTENCES_FOR_SPREAD:
        parts["spread"] = _ramp(sentence_length_spread(text), *SPREAD_RANGE)

    total = sum(STYLE_WEIGHTS[k] for k in parts)
    score = sum(STYLE_WEIGHTS[k] * v for k, v in parts.items()) / total
    return round(score, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    
