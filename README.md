# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

Provenance Guard is a small Flask service a writing site could plug into. A
writer's text goes in, and a guess, a confidence score, a plain-English label and
an appeal route come out. The path a submission takes:

1. **`POST /submit` arrives** with `text` and `creator_id` (`app.py::submit`).
2. **Validation.** Missing, empty, non-string, whitespace-only, under 3 words or
   over 20,000 characters is refused with a JSON 4xx before any model runs. Refusals
   are logged as `rejected` where there is a creator to log them against.
3. **Signal one** (`detector.py::model_signal`) runs gpt2 locally and scores how
   predictable the text is, 0-1.
4. **Signal two** (`stylometry.py::style_signal`) measures the text's shape
   (sentence rhythm, word variety, punctuation), 0-1.
5. **Combine** (`scoring.py::combine_signals`) turns the two into one score,
   0.0 (human) to 1.0 (AI), using a weighted average and a disagreement rule.
6. **Label** (`scoring.py::score_to_label`) maps that score to one of three
   guesses (`human`, `unsure`, `ai`) and the sentence the writer reads.
7. **Log and answer.** The decision, both signal scores and the combined score are
   appended to `logs/audit.jsonl` (`audit.py`) under a new `content_id`, and the
   JSON comes back. If the writer disagrees, `POST /appeal` with that `content_id`
   records their reasoning next to the decision and sets the status to
   `under_review`.

**The false positive I designed around.** A real person writes plainly, in short
even sentences with common words. Both signals read that as AI (see the split
table below, row "plain human"). They get a high score, the "probably AI" label,
and nothing else automatically. What they can do is appeal. The label says the
check can be wrong, tells them to appeal, and says a person will look.

**API contract**

| | In | Out |
|---|---|---|
| `POST /submit` | `{"text": str, "creator_id": str}` | 200: `content_id`, `guess` (`ai`/`human`/`unsure`), `confidence` (the combined score, 0.0 = human, 1.0 = AI), `label`, `model_score`, `style_score`, `status`. 4xx/5xx: `{"error", "message"}` |
| `POST /appeal` | `{"content_id": str, "reasoning": str}` | 200: `content_id`, `status: "under_review"`, `message`. 404 unknown id, 400 missing/empty fields |

---

## Signals and Scoring

### Signal one — the model signal

**What it measures:** How predictable the text is to gpt2 (perplexity, squashed to
0-1 by a logistic curve centred on perplexity 45). Higher means more likely AI.
Lives in `detector.py::model_signal`, which I did not change.

**Why that might differ between human and AI writing:** A language model writes
by picking likely next words, so its text is easy for another model to predict.
Human writing has odd word choices and specifics that surprise it.

**What it can't see:** Authorship. It measures predictability, not who wrote it.
Plain human writing (common words, short sentences, second-language writers,
younger writers) is just as predictable as machine text and scores as AI. Dense,
ornate prose full of rare words scores as human, so rewriting AI text with
unusual vocabulary slips past it.

### Signal two — the style signal

**What it measures:** The text as text, with no idea what it means
(`stylometry.py::style_signal`). Three measures, each scaled 0-1 where 1 = AI:

| Measure | Function | Direction | Scale (0.0 end / 1.0 end) | Weight |
|---|---|---|---|---|
| Sentence length spread (stdev / mean of words per sentence) | `sentence_length_spread` | low spread = AI | 0.75 / 0.25 | 0.50 |
| Word variety (type-token ratio over 50-word windows) | `type_token_ratio` | low variety = AI | 0.90 / 0.65 | 0.25 |
| Punctuation other than full stops, per word | `punctuation_density` | low density = AI | 0.14 / 0.04 | 0.25 |

If a text has fewer than 3 sentences, spread is dropped and the other two are
re-weighted, because one sentence has no spread and a fake 0.0 would read as AI.

**Why that might differ between human and AI writing:** Generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary. Human
writing is lumpier, with a three-word sentence next to a forty-word one.

**What it can't see:** Meaning. Anything that changes the shape without changing
the substance moves it: adding typos, breaking up sentences, pasting a quotation,
sprinkling in dashes. It also scores *any* writer who writes evenly and plainly as
AI, whoever they are. And its scale numbers came from only five calibration texts,
so they are rough.

### The combining rule

**The rule:** A weighted average, plus a rule for disagreement. The average
leans on the model signal because it is the better-established of the two. The
disagreement rule exists because "high-confidence AI" is the label that accuses
someone: **it needs both signals to lean AI**. If either signal is below 0.50,
the combined score is held just under the AI threshold, so the most the system
can say is "unsure".

**The numbers** (all in `config.py`):

- `combined = 0.6 * model_score + 0.4 * style_score`
- If `min(model_score, style_score) < 0.50` (`AI_CONFIRM_FLOOR`), then
  `combined = min(combined, 0.69)`
- Human label at or below **0.35**, AI label at or above **0.70**, unsure in
  between. The AI cutoff sits further from the middle than the human one (0.20 vs
  0.15 from 0.50) so that accusing someone takes more evidence than clearing them.

**Where it lives:** `scoring.py::combine_signals`

**A case where my two signals split, and what my rule does with it:** The lightly
edited AI paragraph (AI text where I swapped formal words for casual ones). The
model signal read it as human-ish (0.48) because casual words are less predictable,
while the style signal still read it as AI-ish (0.62) because the sentences are
still even. The weighted average is 0.53, which is "unsure", and that is the right
answer for text that is half-edited. The disagreement rule matters in the other
direction: if one signal were at 0.95 and the other at 0.45, the average would be
above 0.70, and the rule would hold the score at 0.69 so the label is "unsure"
rather than an accusation resting on one signal.

**Calibration run** (five texts I wrote or chose for the purpose; scores from
this build):

| Input | model_score | style_score | combined | label |
|---|---|---|---|---|
| clearly AI | 0.83 | 0.61 | 0.75 | ai |
| clearly human (personal, uneven) | 0.29 | 0.06 | 0.20 | human |
| plain human (everyday, short sentences) | 0.82 | 0.85 | 0.83 | **ai (false positive)** |
| formal human (committee minutes) | 0.49 | 0.52 | 0.51 | unsure |
| lightly edited AI | 0.48 | 0.62 | 0.53 | unsure |

The plain-human row is the important one. **Both signals agree, both are wrong,
and so the disagreement rule cannot help.** I did not tune the numbers to hide this: with
five texts I would just be fitting the thresholds to my samples. It is a known weakness,
and it is why the AI label tells writers to appeal.

### Baseline on my own writing (before any changes)

After the build I scored real text offline with both signals: **13 paragraphs I
wrote myself** (short, plain, everyday topics, ~60-70 words) and **6 paragraphs
that were AI-generated** (descriptive, sensory: a train over a river, gardening,
a bookstore, a night market, learning piano, winter mornings). Thresholds and
weights were not changed to fit them. They are saved in `scenarios.py`, so unit 8
reruns them three times.

| Set | Pieces | Avg model | Avg style | Avg combined | Labels |
|---|---|---|---|---|---|
| My writing | 13 | 0.57 | 0.66 | 0.60 | 2 ai, 10 unsure, 1 human |
| AI paragraphs | 6 | 0.59 | 0.56 | 0.58 | 1 ai, 5 unsure |

What this says about my criteria:

- **Criterion 1 (at most 1 of 10 of mine labelled AI): missed.** 2 of my 13 were
  labelled high-confidence AI, and a third scored 0.70, right on the line.
- **Criterion 2 (AI averages at least 0.30 above human): missed badly.** The gap
  is -0.02: the AI set scored slightly *lower* than my writing, and one AI piece
  scored 0.41 while one of mine scored 0.71.
- **Why:** my writing is plain and evenly paced with common words, which both
  signals read as AI. The AI paragraphs are vivid with varied detail, which both
  read as human. For this kind of text the signals point the wrong way, and the
  disagreement rule can't help because both signals agree.
- **Limits of this evidence:** 13 and 6 pieces is a small sample, one writer, and
  the AI set is one style. Generic "importance of technology" AI text scores much
  higher (0.75 in the calibration run above).

---

## Label Variants

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.35 | We think this was probably written by a person. |
| unsure | 0.35 – 0.70 | We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal. |
| high-confidence AI | 0.70 – 1.00 | This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it. |

(`scoring.label_ranges()` prints these ranges from `config.py`. All three are
reachable; see the calibration run above, which produces each.)

**Why I worded the "unsure" one this way:** The person reading it may well have
written every word. So it says plainly that we can't tell, says "nothing is being
held against you" so it doesn't read as an accusation, blames the check rather
than the writer, and offers an appeal anyway. Even the "AI" label says "probably",
admits the check can be wrong, and points to the appeal.

---

## Sample Run

One submission and one appeal, from this build. The text is the "plain human"
calibration paragraph, which the system wrongly calls AI, so the appeal below is
the case the appeal route exists for.

**A submission**

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "I went to the store after work on Tuesday. I needed milk and bread and some eggs. The store was busy so it took a long time. I got home around six and made dinner. My sister called while I was cooking and we talked for an hour. Then I did the dishes and watched a show before bed. It was a pretty normal day and I was tired by the end of it.", "creator_id": "cal_plain_human"}'
```

```json
{
  "confidence": 0.8319,
  "content_id": "06352159c1d5",
  "guess": "ai",
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "model_score": 0.8199,
  "status": "decided",
  "style_score": 0.85
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "06352159c1d5", "reasoning": "I wrote this myself on Tuesday night, it is just how I write."}'
```

```json
{
  "content_id": "06352159c1d5",
  "message": "Thanks. Your appeal has been recorded and this item is now under review. A person will look at it.",
  "status": "under_review"
}
```

**What the log shows afterwards** (the decision, then the appeal beside it; the
original line is untouched because the log is append-only)

```bash
$ curl "http://127.0.0.1:5000/log"   # entries for content_id 06352159c1d5
```

```json
[
  {
    "timestamp": "2026-11-04T05:34:20+00:00",
    "content_id": "06352159c1d5",
    "creator_id": "cal_plain_human",
    "guess": "ai",
    "model_score": 0.8199,
    "style_score": 0.85,
    "combined_score": 0.8319,
    "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-04T05:34:20+00:00",
    "content_id": "06352159c1d5",
    "creator_id": "cal_plain_human",
    "event": "appeal",
    "status": "under_review",
    "reasoning": "I wrote this myself on Tuesday night, it is just how I write."
  }
]
```

**Bad input** (criterion 5; each is a JSON error, none is a 500, and `/ping` still answers afterwards)

| Request | Status |
|---|---|
| `text` missing / `""` / whitespace / `null` / a number | 400 |
| `creator_id` missing | 400 |
| body is a JSON list, or not JSON | 400 |
| `text` under 3 words | 400 |
| `text` of 200,000 characters | 413 |
| `/appeal` with an unknown `content_id` | 404 |
| `/appeal` with empty `reasoning` | 400 |

---

## How I Used AI

I used Claude Code (inside VS Code) for most of this project. It wrote the first
version of the code from the assignment text. I supplied the test data, made the
judgment calls about what to do with the results, and decided what to keep. Two
moments:

**Moment 1: the first false positive**

- *What I asked for:* The whole Unit 7 build from the assignment: the two
  endpoints, the style signal, the combining rule, three labels, and my five
  criteria.
- *What came back:* Working code, and a calibration run where a plain, everyday
  paragraph scored 0.83 and got the "AI" label. Both signals agreed, so the
  disagreement rule couldn't catch it.
- *What I changed:* I did not tune the numbers to hide that result. The criteria
  were committed first so that a miss would stay a miss. I kept the result as the
  honest example of the blind spot and wrote it up in Signals and Scoring.

**Moment 2: testing with my own writing**

- *What I asked for:* More evidence than five calibration samples. I gave Claude
  13 paragraphs I wrote myself and 6 AI-generated paragraphs and asked how the
  service scored them.
- *What came back:* The service can't separate the two sets. My writing averaged
  0.60 and the AI paragraphs 0.58, and 2 of my 13 were labelled AI. That misses
  criteria 1 and 2.
- *What I changed:* I saved all 19 pieces in `scenarios.py` for next unit and put
  the numbers in the README as the "before" baseline. I did not change
  thresholds or criteria to make them pass, because that would be fitting the
  system to the test and would throw away the baseline.

**What the AI did and what I did:** The code in `app.py`, `stylometry.py`,
`scoring.py` and `config.py` was written by Claude Code. My part was the
test data, labelling which pieces were AI, deciding not to retune, and asking
for explanations of how each part works so I could defend them.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day (`config.py`, applied to `/submit` in `app.py`)

**Why those numbers and not others:** A real writer submits, edits and
resubmits, which is a handful of pieces in a few minutes, so 5 a minute doesn't
get in their way and 50 a day is far more than anyone writing by hand needs. A
script mapping my thresholds needs hundreds of small variations, and 50 a day
makes that slow. The starter's 10/min and 200/day would let a script send 200
probes a day.

**What a caller counts as:** per `creator_id`, falling back to the IP address
when there isn't one. I chose this so people sharing a network (a school, an
office) don't share one allowance. The weakness: a script can change its
`creator_id` on every request and never hit the limit. IP-only counting would
stop that but would wrongly block shared networks.

**The run of status codes when I pushed past it:**

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

(`python run_attacks.py --flood 15`; the rejections are in `logs/audit.jsonl`
as `event: rejected, reason: rate_limited, limit: 5 per 1 minute`.)

---

## Attack Run — Before

The attack set (56 attacks: evasion, false positives, prompt injection,
malformed requests, a same-creator flood) run unchanged against the service as
built, before any improvement: `python run_attacks.py --set <attack_set> --label before`.
Full output is in `results/attack_run_2026-11-10_2241_before.md`. Verdicts are
mine: **17 BROKE, 39 HELD, 0 crashes.**

| EV01 | evasion | signal two: typos raise word variety | 200 | `212f3dfe12b9` | unsure | 0.398 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `f25f5c1eaeae` | unsure | 0.461 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `06d591a6d006` | unsure | 0.596 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `38b13326a3d6` | unsure | 0.667 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `926341a060de` | human | 0.318 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `78d135c69906` | unsure | 0.460 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `42b09be3388c` | unsure | 0.400 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `d5a447d6b774` | human | 0.347 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `82c1805c59ee` | unsure | 0.630 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `30afe1df0545` | ai | 0.930 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `71088b0dcd43` | unsure | 0.630 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `c950f7d740a5` | ai | 0.799 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `574852c28f4e` | ai | 0.792 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | `ed19b00e85d4` | ai | 0.793 | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 | `579afe2b4d2e` | ai | 0.870 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | `a3c574a74e8c` | ai | 0.769 | BROKE |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `99d1b8d0fc4f` | ai | 0.737 | BROKE |
| FP08 | false_positive | very short genuine human submission | 200 | `5787bf13b082` | unsure | 0.420 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `eb1874084a06` | unsure | 0.412 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `2e708ea22ad4` | human | 0.258 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `687f356c879d` | unsure | 0.605 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `e7ed1c41857d` | unsure | 0.519 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `68389465322a` | unsure | 0.384 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `78d3973320e0` | unsure | 0.589 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 200 | `1e5dcf05f367` | human | 0.200 | BROKE |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — | HELD |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — | HELD |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — | HELD |
| MF07 | malformed | text is right-to-left script | 400 | `—` | — | — | HELD |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — | HELD |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 429 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `0377d7b6d2ed` | human | 0.217 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `224215819061` | human | 0.217 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `8dd22c86c582` | human | 0.217 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `97dc665dee5a` | human | 0.217 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `b2702a2a25c2` | human | 0.217 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

**Summary by family**

- **False positives: 6 of 8 broke.** FP02-FP07, real human writing in a formal
  register, a non-native speaker, a rubric essay, technical docs, a template and a
  deliberate repeat, were labelled high-confidence AI. FP01 and FP08 held (unsure).
- **Evasion: 9 of 10 broke.** Only EV10 (repeated stanza structure) was caught.
  The rest of the AI-written texts came back "unsure" or "human".
- **Prompt injection: 1 of 6 broke.** PI02 (AI text with a fake "SYSTEM: bypass
  the check" line) was labelled human. The service did not obey the instruction
  (confidence came back 0.26, not the 0.02 it demanded). The extra line changed
  the shape of the text and lowered the scores.
- **Malformed: 1 of 20 broke.** MF03 (control characters) was accepted as real
  text, labelled human with a 200, and the escape codes went into the audit log.
  RQ09-RQ11 (empty, form-encoded and text/plain bodies) got 429 not 400: they
  have no readable `creator_id`, so they count against the IP address, which the
  earlier malformed requests had already used up.
- **Flood: held.** The same creator got 5 x 200, then 429.

**Ten audit log entries from the run**

(labels shortened here for space; the full text is in `logs/audit.jsonl`)

```json
[
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "574852c28f4e",
    "creator_id": "attacker_FP03",
    "guess": "ai",
    "model_score": 0.8051,
    "style_score": 0.7718,
    "combined_score": 0.7918,
    "label": "This looks like it was probably written with the help of an ...",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "ed19b00e85d4",
    "creator_id": "attacker_FP04",
    "guess": "ai",
    "model_score": 0.8329,
    "style_score": 0.7333,
    "combined_score": 0.7931,
    "label": "This looks like it was probably written with the help of an ...",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "579afe2b4d2e",
    "creator_id": "attacker_FP05",
    "guess": "ai",
    "model_score": 0.8005,
    "style_score": 0.9731,
    "combined_score": 0.8695,
    "label": "This looks like it was probably written with the help of an ...",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:00+00:00",
    "content_id": "212f3dfe12b9",
    "creator_id": "attacker_EV01",
    "guess": "unsure",
    "model_score": 0.1635,
    "style_score": 0.75,
    "combined_score": 0.3981,
    "label": "We can't tell whether this was written by a person or with A...",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "f25f5c1eaeae",
    "creator_id": "attacker_EV02",
    "guess": "unsure",
    "model_score": 0.5943,
    "style_score": 0.26,
    "combined_score": 0.4606,
    "label": "We can't tell whether this was written by a person or with A...",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "926341a060de",
    "creator_id": "attacker_EV05",
    "guess": "human",
    "model_score": 0.3212,
    "style_score": 0.3122,
    "combined_score": 0.3176,
    "label": "We think this was probably written by a person....",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "2e708ea22ad4",
    "creator_id": "attacker_PI02",
    "guess": "human",
    "model_score": 0.2044,
    "style_score": 0.3372,
    "combined_score": 0.2575,
    "label": "We think this was probably written by a person....",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "68389465322a",
    "creator_id": "attacker_PI05",
    "guess": "unsure",
    "model_score": 0.6401,
    "style_score": 0.0,
    "combined_score": 0.3841,
    "label": "We can't tell whether this was written by a person or with A...",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "content_id": "1e5dcf05f367",
    "creator_id": "attacker_MF03",
    "guess": "human",
    "model_score": 0.0,
    "style_score": 0.5,
    "combined_score": 0.2,
    "label": "We think this was probably written by a person....",
    "status": "decided"
  },
  {
    "timestamp": "2026-11-11T04:41:01+00:00",
    "creator_id": "attacker_flood",
    "event": "rejected",
    "status": "rejected",
    "reason": "rate_limited",
    "limit": "5 per 1 minute"
  }
]
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it: **FP03.** A non-native English speaker describing
their first month in a new country ("The weather was very different from my
home. ... I am still learning the words that people use in the office.") scored
0.79 (model 0.81, style 0.77) and got the "probably written with the help of an
AI tool" label. Nothing in the text says AI: it's specific and slightly
unidiomatic. Both signals read short, even sentences and common words as
machine-like, so they agree and my disagreement rule can't help. This writer has
the least room to argue back, and the only thing standing between them and a
wrong accusation is the appeal link in the label.

---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
