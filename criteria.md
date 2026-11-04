# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. False positives: my own writing is almost never called AI

Of 10 plain paragraphs I wrote myself (60–150 words each, ordinary everyday
prose, not polished essays), **at most 1 is labelled high-confidence AI**, and
this holds in each of 3 separate runs of the same 10 pieces. Landing in "unsure"
doesn't count as a miss.

**Why this target:** On a writing site a wrong accusation costs the writer their
standing, while a missed AI piece costs the site very little. My model signal
rewards short sentences and common words, which is exactly how plain human
writers write, so this is where the system is most likely to fail. I picked 1 in
10 rather than 0 in 10 because gpt2 gives a slightly different score on repeat
runs and a zero target would be a coin flip I can't control.

---

## 2. Score spread: clearly-AI and clearly-human text land far apart

Take 3 pieces I am confident are AI-generated (generic, evenly paced
"importance of X" prose, 80+ words) and 3 I am confident are human (personal,
specific, uneven). The **average combined score of the AI set is at least 0.30
higher** than the average of the human set, and **no AI piece scores below 0.50
and no human piece scores above 0.50**.

**Why this target:** A confidence score only means something if it moves. If the
two groups score within 0.1 of each other, the number is noise and the labels
are a coin flip dressed up. 0.30 is about the width of my unsure band, so the
two groups have to be separated by at least one label's worth of distance.

---

## 3. Label coverage: all three labels can be produced

Across the inputs I try, **each of the 3 labels (high-confidence human, unsure,
high-confidence AI) is returned at least once**, and **every score from 0.00 to
1.00 maps to exactly one of them** (checked by calling `score_to_label` on 0.00,
0.01, ..., 1.00 and seeing no error and no missing label). Two scores 0.02 apart
on either side of a threshold, such as 0.63 and 0.67, return different label
text.

**Why this target:** The "unsure" label is the most important one for a system
where false accusations are expensive, and it is also the one a careless range
leaves unreachable. A weighted average of two signals can't leave the range
between them, so a label can be unreachable even when its range looks fine on
paper. This criterion catches that.

---

## 4. The appeal path: every appeal is recorded and changes status

For **10 out of 10** appeals sent with a valid `content_id`, the response is
HTTP 200 and says `under_review`, and `GET /log` then shows a new entry with
that `content_id`, `status: "under_review"` and my exact reasoning text, while
the original decision entry is still there unchanged. An appeal with an unknown
`content_id` returns 404 and writes nothing, and one with empty reasoning
returns 400.

**Why this target:** The appeal is the only thing standing between a wrong
accusation and nothing. If even 1 in 10 silently fails, a real writer is being
ignored without knowing it. It has to be 10 of 10, not "most", because
there is no acceptable rate of lost appeals. Rejecting unknown ids loudly stops a
typo from looking like a success.

---

## 5. Bad input: nothing I send can crash the service

Each of these returns a JSON error with an HTTP 4xx status, **never a 500 and
never a hang**: (a) `text` missing, (b) `text` is `""`, (c) `text` is only
whitespace, (d) `text` is `null` or a number, (e) `creator_id` missing, (f) a
body that isn't a JSON object, (g) text 200,000 characters long, and (h) text
shorter than 3 words. After all eight, `GET /ping` still answers.

**Why this target:** A crash on malformed input is one of the most common real
failures. The model signal runs inline and slow, so an enormous input is also an
easy way to tie the service up. All eight must pass because each is a different
code path and one unhandled one is enough to take the service down. I picked
200,000 characters because it's far past what gpt2 reads (it only reads the
first 400 tokens), so the limit is a deliberate choice.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
