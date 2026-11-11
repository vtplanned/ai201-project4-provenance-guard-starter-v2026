# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-10 22:41
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

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

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "212f3dfe12b9",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.3981,
  "model_score": 0.1635,
  "style_score": 0.75,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "f25f5c1eaeae",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.4606,
  "model_score": 0.5943,
  "style_score": 0.26,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "06d591a6d006",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.5964,
  "model_score": 0.6662,
  "style_score": 0.4916,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "38b13326a3d6",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.6668,
  "model_score": 0.6114,
  "style_score": 0.75,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "926341a060de",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.3176,
  "model_score": 0.3212,
  "style_score": 0.3122,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "78d135c69906",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.4596,
  "model_score": 0.5727,
  "style_score": 0.29,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "42b09be3388c",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.3997,
  "model_score": 0.5862,
  "style_score": 0.12,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "d5a447d6b774",
  "creator_id": "attacker_EV08",
  "guess": "human",
  "confidence": 0.3471,
  "model_score": 0.2452,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "82c1805c59ee",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.6305,
  "model_score": 0.7042,
  "style_score": 0.52,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "30afe1df0545",
  "creator_id": "attacker_EV10",
  "guess": "ai",
  "confidence": 0.93,
  "model_score": 0.9792,
  "style_score": 0.8561,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "71088b0dcd43",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.6302,
  "model_score": 0.6175,
  "style_score": 0.6492,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "c950f7d740a5",
  "creator_id": "attacker_FP02",
  "guess": "ai",
  "confidence": 0.7992,
  "model_score": 0.7387,
  "style_score": 0.89,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "574852c28f4e",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.7918,
  "model_score": 0.8051,
  "style_score": 0.7718,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "ed19b00e85d4",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.7931,
  "model_score": 0.8329,
  "style_score": 0.7333,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "579afe2b4d2e",
  "creator_id": "attacker_FP05",
  "guess": "ai",
  "confidence": 0.8695,
  "model_score": 0.8005,
  "style_score": 0.9731,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "a3c574a74e8c",
  "creator_id": "attacker_FP06",
  "guess": "ai",
  "confidence": 0.7692,
  "model_score": 0.8814,
  "style_score": 0.6008,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "99d1b8d0fc4f",
  "creator_id": "attacker_FP07",
  "guess": "ai",
  "confidence": 0.7366,
  "model_score": 0.8816,
  "style_score": 0.5191,
  "label": "This looks like it was probably written with the help of an AI tool. Our check isn't perfect and can be wrong about real writers. If you wrote this yourself, you can appeal, and a person will look at it.",
  "error": null,
  "verdict": "judged in README"
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "5787bf13b082",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.4202,
  "model_score": 0.3223,
  "style_score": 0.567,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "eb1874084a06",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.4124,
  "model_score": 0.4625,
  "style_score": 0.3373,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "2e708ea22ad4",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.2575,
  "model_score": 0.2044,
  "style_score": 0.3372,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "687f356c879d",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.6049,
  "model_score": 0.5943,
  "style_score": 0.6207,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "e7ed1c41857d",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.5188,
  "model_score": 0.4998,
  "style_score": 0.5473,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "68389465322a",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.3841,
  "model_score": 0.6401,
  "style_score": 0.0,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "78d3973320e0",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.5888,
  "model_score": 0.5583,
  "style_score": 0.6346,
  "label": "We can't tell whether this was written by a person or with AI help. Nothing is being held against you. Plenty of people write in a way our check can't read clearly. If you'd like someone to look at it anyway, you can appeal.",
  "error": null,
  "verdict": "judged in README"
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "1e5dcf05f367",
  "creator_id": "attacker_MF03",
  "guess": "human",
  "confidence": 0.2,
  "model_score": 0.0,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "0377d7b6d2ed",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2172,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "224215819061",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2172,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "8dd22c86c582",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2172,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "97dc665dee5a",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2172,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "b2702a2a25c2",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.2172,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": "judged in README"
}
```
