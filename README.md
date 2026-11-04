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

I built this with Claude Code, working from the assignment text. Two moments, as
they actually happened:

**Moment 1: the style signal**

- *What I asked for:* The second signal in `stylometry.py`, using sentence length
  spread, word variety and punctuation, with each measure's direction written down.
- *What came back:* Three measures and a 0-1 combine, with scaling ranges that were
  first-guess numbers. I then ran it on five calibration texts. The plain-human
  paragraph scored 0.85 on style, which is a false positive.
- *What I changed:* I kept the honest result instead of tuning the ranges until
  that paragraph passed, because I'd be fitting five texts. I did change the
  type-token ratio to use 50-word windows (so a long text isn't punished for
  repeating common words) and made sentence spread drop out under 3 sentences.

**Moment 2: the combining rule and the bad-input handling**

- *What I asked for:* A combining rule that treats a false accusation as the costly
  error, and a `/submit` that can't crash on bad input.
- *What came back:* The 0.6/0.4 average with a rule that "AI" needs both signals
  at 0.50 or above, and validation that refuses missing, empty, short and huge
  text with 4xx errors.
- *What I changed:* I raised the AI threshold from the starter's 0.65 to 0.70 so
  accusing is harder than clearing, and I checked all eight bad inputs by hand with
  curl rather than trusting the code.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



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
