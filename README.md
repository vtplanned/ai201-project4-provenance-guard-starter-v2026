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
  `combined = min(combined, 0.79)` (one hundredth under the AI threshold; 0.69 before the Unit 8 change)
- Human label at or below **0.35**, AI label at or above **0.80** (it was 0.70 until the Unit 8
  improvement), unsure in between. The AI cutoff sits further from the middle than the human one (0.30 vs
  0.15 from 0.50) so that accusing someone takes more evidence than clearing them.

**Where it lives:** `scoring.py::combine_signals`

**A case where my two signals split, and what my rule does with it:** The lightly
edited AI paragraph (AI text where I swapped formal words for casual ones). The
model signal read it as human-ish (0.48) because casual words are less predictable,
while the style signal still read it as AI-ish (0.62) because the sentences are
still even. The weighted average is 0.53, which is "unsure", and that is the right
answer for text that is half-edited. The disagreement rule matters in the other
direction: if one signal were at 0.95 and the other at 0.45, the average would be
above the AI threshold, and the rule would hold the score just under it so the label is "unsure"
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
| unsure | 0.35 – 0.80 | We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal. |
| high-confidence AI | 0.80 – 1.00 | This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it. |

(Ranges as of the Unit 8 improvement; the AI band started at 0.70 in unit 7. `scoring.label_ranges()` prints these ranges from `config.py`. All three are
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

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
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

Three trials, nothing changed in between. `python run_eval.py --label before`
(criteria 1, 2, 5, output in `results/run_2026-11-11_0043_before.md`) and
`python eval_extra.py` (criteria 3 and 4, which `scenarios.py` can't express:
a 0.00-1.00 label sweep, and submit-then-appeal checked against `GET /log`).
Both signals are deterministic, so identical trials are expected.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. My own writing flagged as AI | at most 1 of 10 | 2 of 13 | 2 of 13 | 2 of 13 | MISSED |
| 2. AI vs human spread | AI avg at least 0.30 above human; no AI under 0.50; no human over 0.50 | gap -0.03; 1 AI piece under 0.50 is 0.41; human max 0.71 | same | same | MISSED |
| 3. All three labels reachable | 3 of 3, every score 0.00-1.00 maps to one | 3/3, 101/101 | 3/3, 101/101 | 3/3, 101/101 | MET |
| 4. Appeal always recorded and changes status | 10 of 10, 404 unknown id, 400 empty | 10/10, 404, 400 | 10/10, 404, 400 | 10/10, 404, 400 | MET |
| 5. Bad input returns 4xx, never 500 | 8 of 8, `/ping` still answers | 8/8 (7 x 400, 1 x 413) | 8/8 | 8/8 | MET |

Notes: criterion 1's target is per 10 pieces and I had 13, so 2 of 13 scales to
about 1.5 of 10, still above 1. Criterion 2's AI set average is 0.577 and my
writing's is 0.603. The wording in `criteria.md` that the model's scores can vary
between runs turned out wrong (they didn't), but I left the original text alone.

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

*Criterion 1 and 2: `app.py::submit` via `run_eval.py`, trial 1.* Two of my own
paragraphs came back as AI (13 sent; the "ai" ones):

```json
[
  {"status": 200, "guess": "ai", "confidence": 0.7038, "sent": "I learned that you cannot wait for everybody to be ready before you move."},
  {"status": 200, "guess": "ai", "confidence": 0.7069, "sent": "One hobby I actually enjoy is making content and messing around with ideas for videos."}
]
```

*Criterion 3: `scoring.py::score_to_label` over 0.00-1.00:*
`{"human": 36, "unsure": 34, "ai": 31}`, and 0.34 / 0.36 and 0.69 / 0.71 return different label text.

*Criterion 4: `app.py::appeal`, with `GET /log` afterwards:*

```json
{"content_id": "4ed4ecea2359", "message": "Thanks. Your appeal has been recorded and this item is now under review. A person will look at it.", "status": "under_review"}
```
```json
[{"content_id": "4ed4ecea2359", "creator_id": "c4_paste", "guess": "ai", "combined_score": 0.7242, "model_score": 0.6256, "style_score": 0.8722, "status": "decided", "timestamp": "2026-11-11T06:43:56+00:00"},
 {"content_id": "4ed4ecea2359", "creator_id": "c4_paste", "event": "appeal", "reasoning": "I wrote this myself.", "status": "under_review", "timestamp": "2026-11-11T06:43:56+00:00"}]
```

*Criterion 5: `app.py::submit` (`_bad`):* `{"text": "", "creator_id": "x"}` returns
`{"error": "empty_text", "message": "text is empty."}` with 400, and `POST /ping`
still answers `{"ok": true, ...}` afterwards.

**Diagnoses**

Every miss and every broken attack, with its stage and mechanism. The five
stages are the route, signal one (`detector.py::model_signal`), signal two
(`stylometry.py::style_signal`), the combining rule (`scoring.py::combine_signals`)
and the label mapping (`scoring.py::score_to_label`). Scores below are
`model / style / combined` from `logs/audit.jsonl`.

**Criteria 1 and 2, and the false positives FP02-FP07. Stage: signal one, with
signal two reinforcing it.** Six real human texts were labelled high-confidence
AI: formal register (FP02), a non-native speaker (FP03), a rubric essay (FP04),
technical documentation (FP05), a person imitating a template (FP06) and a
deliberate repeat (FP07). The model signal was 0.74-0.88 on every one of them,
above my 0.70 AI cutoff by itself, while the style signal ranged from 0.52 to
0.97. The mechanism: gpt2 measures how *predictable* text is, not who wrote it,
and plain, formal, formulaic or carefully written text is predictable. The same
mechanism missed criterion 1 (my own short, plain paragraphs #6 and #7 scored
0.70 and 0.71) and criterion 2: my plain writing averaged 0.603 while the
AI-written paragraphs, which were vivid and varied, averaged 0.577, so the two
sets did not separate (gap -0.03, target +0.30). In every one of these cases
both signals were above 0.50, so my disagreement rule (`AI_CONFIRM_FLOOR`)
never fired. It only protects against one signal being wrong, not two signals
being wrong the same way.

**EV01 (typos). Stage: signal one, not signal two.** The attacker added
intentional typos to AI-generated text, hoping the increased word variety would
lower the style signal and make the text appear more human. Instead the model
signal dropped to 0.16 while the style signal stayed at 0.75. The misspelled
words were less predictable to gpt2, which increased perplexity and made the text
seem more human-written. So the attack fooled signal one rather than signal two,
which was the original target. My rule weights signal one at 0.6, so that drop
pulled the combined score down to 0.40 ("unsure").

**EV02, EV06, EV07 (shape attacks). Stage: signal two.** EV02 broke AI text into
short sentences ("Really."), EV06 put one very long and one very short sentence
in, and EV07 padded the text with punctuation. Style scores fell to 0.26, 0.29
and 0.12. The mechanism: signal two measures only shape (sentence-length spread
and punctuation per word), so adding short sentences raises the spread, and extra
punctuation raises the density, both of which it reads as human. The model
signal stayed at 0.57-0.59, so the combined scores landed at 0.40-0.46
("unsure"), and the 0.6 / 0.4 weighting could not rescue them.

**EV08 (short text). Stage: signal one.** The model signal fell to 0.25. A short
text gives gpt2 little to be predictable about, so the perplexity is noisy and
tends to be high, which reads as human. The combined score was 0.35, right on the
human boundary, and the label was "human".

**EV05 (heavy human editing). Stage: signals one and two together.** Both
signals fell to about 0.31-0.32 (combined 0.32, "human"). When both signals are
fooled the same way there is nothing for the combining rule to do.

**EV03, EV04, EV09 (near-misses). Stage: the combining rule and the label
mapping.** These AI texts scored 0.60, 0.67 and 0.63, close to but under my 0.70
AI cutoff. For EV03 (a pasted quotation) the style signal was 0.49, below the
0.50 floor, so `AI_CONFIRM_FLOOR` would have capped it under the cutoff even if
the average had been higher. The mechanism: I set the AI threshold at 0.70 and
required both signals to agree so that accusing someone is hard. The same
protection that stops false accusations lets AI text that scores 0.6-0.7 through
as "unsure". That is a deliberate trade, not a bug, but it is a cost.

**PI02 (fake "SYSTEM:" line). Stage: signal one.** The service does not read
instructions, and did not obey this one: it asked for confidence 0.02 and got
0.26. The extra capitalised, unusual line was unpredictable to gpt2, so the model
signal fell to 0.20 and the AI text was labelled "human". The attack worked by
accident, the same mechanism as the typos in EV01.

**MF03 (control characters). Stage: the route.** `app.py::submit` only checks
that `text` is a non-empty string with at least 3 words, so `\x00\x01\x02 test
\x1b[31mred\x1b[0m` passed. It scored 0.00 / 0.50, was labelled "human" with a
200, and the escape codes were written into the audit log. It should have been
refused.

**The pattern.** The failures are mostly one problem, not seventeen. Both of my
signals measure the *shape* of the text (predictability and rhythm), not who
wrote it. Anything that changes the shape moves the score in either direction:
plain human writing moves it up and typos, short sentences or odd lines move AI
text down. The combining rule has only one defence, the floor, and it only helps
when the two signals disagree. When both are fooled the same way (the false
positives, EV05), the rule has nothing to work with.

---

## The Improvement

**What I changed:** One thing: the high-confidence AI threshold in `config.py`,
`AI_THRESHOLD`, from **0.70 to 0.80**. Nothing else changed: same signals, same
weights (0.6 / 0.4), same floor, same human threshold (0.35), same attack set and
same five criteria. The unsure band is now 0.35-0.80, 0.10 wider on the AI side.
(`AI_CONFIRM_FLOOR`'s cap follows it automatically, to 0.79.)

**Which diagnosis pointed at it:** The false positives, FP02-FP07 and criterion
1. Real human writing was landing in the high-confidence AI band with combined
scores of 0.74-0.87. Signal one was the cause, and I can't fix signal one
(gpt2 measures predictability, not authorship), but I can decide how much
evidence it takes to *accuse* someone. Five of the six accused texts sat in
0.74-0.80, so I put the cutoff at 0.80. That number is fitted to this set, which
I note in the trade below.

**Prediction I wrote down before running it:** FP02, 03, 04, 06 and 07 would drop
to "unsure"; FP05 (0.87) would stay accused; evasion, PI02 and MF03 would not
change because a threshold can't reach them.

### Attack Run — Before (56 attacks, threshold 0.70)

Same table as in the section above: **17 BROKE, 39 HELD.**

### Attack Run — After (56 attacks, threshold 0.80)

`python run_attacks.py --set <attack_set> --label after`; output in
`results/attack_run_2026-11-11_0128_after.md`. Verdicts use the same rules as
before (false positive: BROKE if labelled AI; evasion: BROKE if not labelled AI;
PI02: BROKE if labelled human; MF03: BROKE if accepted with a 200;
everything else HELD).

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `d8cd32754a75` | unsure | 0.398 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `4ee5806b1a23` | unsure | 0.461 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `27c2996e2e00` | unsure | 0.596 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `20fdb8e61a26` | unsure | 0.667 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `a49244b9b9c6` | human | 0.318 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `429d58453f8d` | unsure | 0.460 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `10372621afdd` | unsure | 0.400 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `d1c7c954c26f` | human | 0.347 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `3b2129c0451c` | unsure | 0.630 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `f5be26a5b7a2` | ai | 0.930 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `a8ba7e69af57` | unsure | 0.630 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `585b1cd0d991` | unsure | 0.799 | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `f1095337633f` | unsure | 0.792 | HELD |
| FP04 | false_positive | a student essay written to a rubric | 200 | `8e9c5934b4ea` | unsure | 0.793 | HELD |
| FP05 | false_positive | technical documentation written by a person | 200 | `7d9bf5fd24f9` | ai | 0.870 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | `00b05b7f1ab4` | unsure | 0.769 | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `366ba4e69f3f` | unsure | 0.737 | HELD |
| FP08 | false_positive | very short genuine human submission | 200 | `592d7e6f6593` | unsure | 0.420 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `8c933ebe72c3` | unsure | 0.412 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `4b383a427ecf` | human | 0.258 | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `b072cecb030d` | unsure | 0.605 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `333a1358d90d` | unsure | 0.519 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `e4bdf11cf48f` | unsure | 0.384 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `f68f75942fe2` | unsure | 0.589 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 400 | `—` | — | — | HELD |
| MF03 | malformed | text is control characters | 200 | `33a71561c0c1` | human | 0.200 | BROKE |
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
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `3e708ba88f92` | human | 0.217 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `03c8e849a56d` | human | 0.217 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `3bbbd9677047` | human | 0.217 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `1931d4bfd15b` | human | 0.217 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `198205a778d6` | human | 0.217 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

**Side by side**

| Family | Before: broke | After: broke |
|---|---|---|
| False positives (8) | 6 | **1** (FP05) |
| Evasion (10) | 9 | 9 |
| Prompt injection (6) | 1 (PI02) | 1 (PI02) |
| Malformed (20) | 1 (MF03) | 1 (MF03) |
| Flood (12) | 0 | 0 |
| **Total (56)** | **17** | **12** |

| Criterion | Before (0.70) | After (0.80) |
|---|---|---|
| 1. My own writing flagged as AI (at most 1 of 10) | 2 of 13 in every run: MISSED | **0 of 13** in every run: MET |
| 2. AI vs human spread (gap +0.30) | gap -0.03: MISSED | gap -0.03: MISSED (scores unchanged) |
| 3. All three labels reachable | 3/3, sweep 101/101: MET | sweep 101/101 (human 36, unsure 44, ai 21): MET; see cost below |
| 4. Appeals recorded | 10/10 x3: MET | 10/10 x3: MET |
| 5. Bad input returns 4xx | 8/8 x3: MET | 8/8 x3: MET |

Three trials each, identical every time (output in
`results/run_2026-11-11_0128_after.md`; criteria 3 and 4 from `eval_extra.py`).

**Did it help, and how do I know:** It helped where the diagnosis aimed. Five of
six wrongly accused human texts are now "unsure" (FP02, 03, 04, 06, 07,
including my worst outcome, FP03, a non-native speaker), and criterion 1 went
from MISSED to MET: none of my 13 own paragraphs is labelled AI any more. Total
broken attacks fell from 17 to 12. I know it's the threshold and nothing else
because the combined scores are identical before and after; only labels moved.
It did not touch the evasion attacks, PI02 or MF03, as predicted.

**What it cost on the other side:**
- **AI text scoring 0.70-0.80 is no longer called AI.** In the attack set no
  such text existed, so the cost doesn't show there: EV10 (0.93) is still caught.
  It does show in my own calibration sample: the clearly-AI "technology" paragraph
  scored 0.75 and was labelled AI before, and is "unsure" now. That's why the
  label-coverage scenario (`scenarios.py`) now returns unsure, unsure, human, not
  ai, unsure, human. All three labels are still reachable (the sweep, EV10 and my
  AI paragraph 1 at 0.82 get "ai"), so I count criterion 3 as MET, but it's a
  weaker pass.
- **The cutoff is fitted to this set.** Five accused texts sat at 0.74-0.80 and I
  chose 0.80 to clear them. A real writer scoring 0.82 would still be accused,
  and FP05 (technical documentation, 0.87) still is.
- **Criterion 2 is not helped at all.** It's a spread problem and I only moved a
  cutoff.

---

## What's Still Broken

**Attacks still getting through (12 broke after the change):**

- **FP05 (technical documentation, 0.87).** Still accused. Signal one and signal
  two both score precise, formulaic text as AI. I'd stop doing this by moving the
  threshold, because 0.87 is above where I'd honestly put it. It needs a better
  signal, not a number; I stopped because I can't make signal one measure
  authorship.
- **EV01-EV09 (nine evasion attacks).** Typos and the "SYSTEM:" line fool signal
  one by raising perplexity; short sentences and punctuation padding fool signal
  two. I'd fix the style signal's easy-to-game inputs first (count sentence
  length with minimum-length rules, ignore repeated punctuation) and normalise
  typos before the model sees the text. I stopped because it's nine different
  fixes and the milestone says one change.
- **PI02.** Same mechanism as the typos: an odd prefix raises perplexity.
- **MF03.** The route accepts control characters as text. I'd reject any `text`
  with non-printing characters in `app.py::submit`. It's a one-line fix; I left it
  because the milestone says one change and it wasn't the one my diagnosis
  prioritised.

**Criteria still missed:**

- **Criterion 2 (AI vs human spread).** The gap is -0.03 against +0.30, because
  plain human writing and vivid AI writing swap places on both signals. I'd need a
  signal that doesn't depend on shape. I stopped because no threshold or weight
  fixes a signal that points the wrong way.

**The trade I'd make if this ran for real:** I'd keep the wide unsure band and
accept missing AI text, because the writers who get wrongly accused (plain,
non-native and formal writers) have the least room to argue back, while the cost
of AI text slipping through is only borne by the site. The people who pay for it
are the platform's other readers and honest writers whose work competes with AI
text that wasn't caught, and the appeal path is the only protection for
everyone else.

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
