#!/usr/bin/env python3
"""
Criteria 3 (sweep half) and 4 (appeals), which scenarios.py can't express.

    python app.py                    # one terminal
    python eval_extra.py             # another; run it three times

Criterion 3: score_to_label on 0.00, 0.01 ... 1.00 gives one label each, and
the labels change across 0.35 and 0.70.
Criterion 4: 10 submissions are appealed. Each appeal must return 200 and
under_review, and GET /log must then show an appeal entry with the same
content_id, status under_review and my exact reasoning, with the original
decision entry still there. Unknown id -> 404, empty reasoning -> 400.
"""
import json, sys, time, uuid
import requests
import config, scoring

URL = f"http://{config.HOST}:{config.PORT}"
TEXT = ("I walked to the shop this morning and bought bread. The queue was long "
        "and the weather was cold. I came home and made tea before work.")

def criterion_3():
    labels = [scoring.score_to_label(i / 100)[0] for i in range(101)]
    ok = all(l in ("human", "unsure", "ai") for l in labels)
    flips = (scoring.score_to_label(config.HUMAN_THRESHOLD - 0.01)[1] != scoring.score_to_label(config.HUMAN_THRESHOLD + 0.01)[1]
             and scoring.score_to_label(config.AI_THRESHOLD - 0.01)[1] != scoring.score_to_label(config.AI_THRESHOLD + 0.01)[1])
    return ok and set(labels) == {"human", "unsure", "ai"} and flips, {l: labels.count(l) for l in set(labels)}

def criterion_4():
    run = uuid.uuid4().hex[:6]
    good = 0
    for i in range(10):
        r = requests.post(f"{URL}/submit", json={"text": TEXT, "creator_id": f"appeal_{run}_{i}"}).json()
        cid, why = r["content_id"], f"my reasoning {run} {i}"
        a = requests.post(f"{URL}/appeal", json={"content_id": cid, "reasoning": why})
        entries = requests.get(f"{URL}/log").json()["entries"]
        mine = [e for e in entries if e.get("content_id") == cid]
        decided = [e for e in mine if e.get("event") is None]
        appealed = [e for e in mine if e.get("event") == "appeal" and e.get("reasoning") == why
                    and e.get("status") == "under_review"]
        if a.status_code == 200 and a.json().get("status") == "under_review" and decided and appealed:
            good += 1
    nf = requests.post(f"{URL}/appeal", json={"content_id": "nope", "reasoning": "x"}).status_code
    em = requests.post(f"{URL}/appeal", json={"content_id": cid, "reasoning": "  "}).status_code
    return good == 10 and nf == 404 and em == 400, f"{good}/10 appeals ok, unknown id -> {nf}, empty reasoning -> {em}"

if __name__ == "__main__":
    ok3, d3 = criterion_3(); print("criterion 3 sweep:", "PASS" if ok3 else "FAIL", d3)
    ok4, d4 = criterion_4(); print("criterion 4 appeals:", "PASS" if ok4 else "FAIL", d4)
    sys.exit(0 if ok3 and ok4 else 1)
