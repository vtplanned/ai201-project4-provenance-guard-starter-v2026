"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

SCENARIOS = [
    {
        # Criterion 1: at most 1 of 10 of my own pieces labelled high-confidence AI.
        # 13 paragraphs I wrote myself (short, plain, everyday).
        "name": "my own writing",
        "criterion": 1,
        "texts": ['Yesterday was mostly NAC stuff, no lie. I spent the evening chasing HOD updates and trying to lock in the badges idea with Nife, then I moved Aisha to media and marketing HOD and assistant CoS because those guys are struggling and we need her there right now. It was a lot of DMs, but at least things finally started moving, mehn.', 'I made something simple last night because I did not have time to do anything fancy. I threw rice in the pot, made a quick stew with chicken, and called it a day. It was not perfect, the stew was a bit spicy, but it hit the spot after a long day of messages. Sometimes simple food just dey do the work, no wahala.', 'My commute is not really a long drive most days, it is more like getting from one thing to the next. I put on music, check a few messages at red lights, and try to plan what I need to do first. Traffic in OKC can be annoying, but it also gives me time to think, so I just lock in and go.', 'The most frustrating thing lately is trying to get people to reply. I will send a message, follow up, and still hear nothing, then everybody wants to rush at the last minute. It is annoying because I am trying to keep NAC moving, but I cannot do everything myself. I just have to keep pushing and not let it spoil my mood.', 'My favorite place is honestly just somewhere I can think without too much noise. It does not have to be fancy, just good vibes, good music, and space to breathe. When I am there I can plan, write stuff down, and actually focus. I always leave feeling a bit lighter, like okay, we can handle this and plan the next step.', 'I learned that you cannot wait for everybody to be ready before you move. If you wait, nothing will happen, and the work will just pile up. You have to start with the people who are active, give them clear roles, and let the rest catch up later. That lesson came from NAC, but it honestly applies to everything else too.', 'One hobby I actually enjoy is making content and messing around with ideas for videos. I like thinking about how a story should flow, what caption fits, and how to make it look clean without overdoing it. It is not work for me when I am in the zone, it is just fun, and I lose track of time.', 'I had a recent conversation with Nife about moving Aisha to media and marketing HOD and using her to help with CoS tasks. We talked about DMing the project managers so there is no confusion, and about pushing the non urgent stuff to next week. It felt good because we finally agreed on a clear direction instead of just talking in circles.', 'My weekend was busy, but in a good way. I caught up on NAC messages, talked to a few people about their roles, and tried to rest a little in between. I did not get everything done, that is normal for me, but I made progress. By Sunday I was already thinking about the week ahead and what we need to finalize.', 'An everyday problem I solved was just getting organized again. My messages were everywhere, so I started listing what was actually urgent and what could wait. I told the right people what to do, delegated a few things to Aisha, and stopped trying to hold everything in my head. It was small, but it made the day feel way easier.', "The old lighthouse had not guided a ship in years, but it still stood at the edge of the cliff, watching the waves come and go. On stormy nights, the keeper's granddaughter would climb the spiral stairs just to listen to the wind through the broken windows. She liked to imagine the light turning again, not for sailors, but for anyone who felt a little lost and needed something steady to look toward.", 'Learning to cook from scratch is mostly about making mistakes and eating them anyway. The first time I tried to make soup, I added too much salt, then too much water, then ended up with something that was technically food but nobody wanted seconds. Still, each attempt taught me a little more about timing, heat, and patience, and now the kitchen feels less like a test and more like a place to experiment.', 'A city at 5am has a completely different feeling from a city at midnight. The streets are quiet, the shops are still closed, and the only people out are delivery drivers, early joggers, and workers heading to their shifts. There is a soft, grey light that makes everything look calmer, like the whole place is taking a deep breath before the noise of the day starts again.'],
    },
    {
        # Criterion 2 (with "my own writing" as the human set): 6 paragraphs
        # that were AI-generated. Averages should sit at least 0.30 above mine.
        "name": "ai writing",
        "criterion": 2,
        "texts": ['The train slowed down as it crossed the river, and for a few seconds everyone in the carriage stopped looking at their phones and looked out instead. The water was calm, the sky was turning orange, and the whole scene felt like it had been paused on purpose. It was a small moment, but it reminded me that sometimes the best part of a trip is not where you are going, it is what you notice along the way.', 'Gardening is a slow kind of reward. You plant something, water it, wait, and for days nothing seems to change. Then one morning a tiny green shoot appears, and suddenly all that patience feels worth it. It teaches you to pay attention to small changes, to check in without rushing, and to accept that some things just need time before they grow into what they are meant to be.', 'An old bookstore on a side street smells like paper, dust, and rain. The shelves are packed so tightly that pulling out one book makes three others lean forward, as if they are trying to get your attention too. The owner knows exactly where everything is, even without labels, and will happily recommend something you did not know you wanted. It is the kind of place where time moves slower, and leaving empty handed feels almost impossible.', 'A night market is loud in the best possible way. Vendors call out prices, music plays from three different stalls at once, and the smell of grilled food follows you down every aisle. You go in planning to buy one thing and come out with a bag full of snacks, a phone case you did not need, and a story about the seller who threw in an extra item just because you smiled.', 'Learning the piano as an adult is humbling. Your fingers do not listen, the easy songs sound hard, and the metronome feels like it is judging you. But then one evening, after weeks of practice, a simple melody finally flows without stopping, and it feels like a small victory. It is proof that starting late is still starting, and that slow progress is still progress.', 'Winter mornings have a quiet kind of beauty. Frost covers the grass, breath turns into little clouds in the air, and the world feels softer and slower than usual. People walk a bit more carefully, hold their coffee a bit tighter, and take a moment before stepping out into the cold. There is something comforting about that stillness, like the day is giving you a few extra minutes to wake up properly.'],
    },
    {
        # Criterion 3: inputs spread across the score range, so all three labels
        # can be seen. Written for calibration, not by me and not a fair test of
        # accuracy; they only show the labels are reachable.
        "name": "label coverage",
        "criterion": 3,
        "texts": ['Technology has become an integral part of modern society, shaping the way people communicate, work, and learn. It offers numerous benefits, including increased efficiency, improved access to information, and enhanced connectivity. However, it is important to consider the potential challenges associated with its widespread use. Balancing innovation with responsibility is essential for ensuring a positive future. By fostering collaboration and thoughtful decision-making, society can harness the full potential of technology while addressing its risks.', "Tech's become a huge part of life nowadays, changing how we talk, work and learn. It gives us lots of stuff, like faster everything, easy info, and being connected. But, you know, there's a downside too and we should think about it. Finding balance between new ideas and being responsible matters a lot. If people work together and think carefully we can get the good without the bad, mostly.", "My grandmother burned every single pancake. Every one! She'd stand there at the stove in her slippers, humming something tuneless, and flip them a beat too late, and we ate them anyway because what else were you going to do? Syrup fixes most things. I still think of her whenever the kitchen smells faintly of smoke, which, honestly, is often, because I inherited the gene. Last Sunday I scorched a whole batch and laughed until my neighbour knocked."],
    },
    {
        # Criterion 5: bad input. Each should be a JSON 4xx, never a 500.
        "name": "bad input",
        "criterion": 5,
        "bodies": [
            {"text": "", "creator_id": "eval_bad_empty"},
            {"creator_id": "eval_bad_missing"},
            {"text": "   \n ", "creator_id": "eval_bad_space"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": 42, "creator_id": "eval_bad_number"},
            {"text": "hello there my friend"},
            {"text": "hi there", "creator_id": "eval_bad_short"},
            {"text": "word " * 40000, "creator_id": "eval_bad_huge"},
        ],
    },
    # Criterion 4 (appeals) needs a submission and then an appeal against its
    # content_id, which this file can't express. I test it by hand with curl;
    # the README's Sample Run shows one.
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
