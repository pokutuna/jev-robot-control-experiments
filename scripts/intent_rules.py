"""実験 005、006、010 の記録で、Jev が選んだ意図が、問いに書いた条件 (s1cap.jev_staged.INTENTS) と合っていたかを数える。

    uv run scripts/intent_rules.py experiments/005-staged-guide experiments/006-fixed-carry

INTENTS の文に書いた条件を RULES に Python の式で書き直し、判断ごとに、そのときの条件の値で成り立つ意図の集まりを求める。
Jev が選んだ意図がその中にあれば「条件どおり」、集まりが空なら「どの意図の条件も成り立たない」と数える。
"""

import argparse
import json
from collections import Counter
from pathlib import Path

# INTENTS の各意図の「Choose when ...」を式にしたもの
RULES = {
    "approach": lambda c: (
        not c["fingers_closed"]
        and not c["bowl_held"]
        and c["at_carry_height"]
        and not c["cross_on_bowl"]
    ),
    "descend": lambda c: (
        not c["fingers_closed"]
        and not c["bowl_held"]
        and (
            (c["at_carry_height"] and c["cross_on_bowl"])
            or (c["previous_intent"] == "descend" and c["last_move"] == "down reached")
        )
    ),
    "grasp": lambda c: (
        not c["fingers_closed"]
        and c["previous_intent"] == "descend"
        and c["last_move"] == "down blocked"
    ),
    "lift": lambda c: c["fingers_closed"] and c["previous_intent"] == "grasp",
    "retry": lambda c: (
        c["fingers_closed"] and c["at_carry_height"] and not c["bowl_held"]
    ),
    "carry": lambda c: (
        c["fingers_closed"]
        and c["bowl_held"]
        and c["at_carry_height"]
        and not c["cross_on_tray"]
    ),
    "lower": lambda c: (
        c["fingers_closed"]
        and c["bowl_held"]
        and (
            (c["at_carry_height"] and c["cross_on_tray"])
            or (c["previous_intent"] == "lower" and c["last_move"] == "down reached")
        )
    ),
    "release": lambda c: (
        c["fingers_closed"]
        and c["previous_intent"] == "lower"
        and c["last_move"] == "down blocked"
    ),
    "finish": lambda c: not c["fingers_closed"] and c["bowl_in_tray"],
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("experiments", type=Path, nargs="+")
    args = parser.parse_args()
    for exp in args.experiments:
        counts: Counter[str] = Counter()
        none_cases: Counter[str] = Counter()
        off_cases: Counter[str] = Counter()
        for events in sorted(exp.glob("runs/*/events.jsonl")):
            for e in map(json.loads, events.open()):
                if e.get("kind") != "decision" or "conditions" not in e:
                    continue
                c, chosen = e["conditions"], e["intent"]
                allowed = {name for name, rule in RULES.items() if rule(c)}
                counts["判断"] += 1
                if not allowed:
                    counts["どの意図の条件も成り立たない"] += 1
                    key = ", ".join(
                        f"{k}={v}" for k, v in c.items() if k != "bowl_in_tray"
                    )
                    none_cases[f"{key} -> {chosen}"] += 1
                elif chosen in allowed:
                    counts["条件どおり"] += 1
                    if len(allowed) > 1:
                        counts["条件どおり (複数の意図の条件が成り立つ)"] += 1
                else:
                    counts["条件と違う意図"] += 1
                    off_cases[f"{sorted(allowed)} -> {chosen}"] += 1
        print(f"## {exp}")
        for k, v in counts.items():
            print(f"- {k}: {v}")
        if off_cases:
            print("条件と違う意図 (成り立つ意図 -> 選んだ意図):")
            for k, v in off_cases.most_common():
                print(f"  {v} {k}")
        if none_cases:
            print("どの意図の条件も成り立たない (条件 -> 選んだ意図):")
            for k, v in none_cases.most_common():
                print(f"  {v} {k}")
        print()


if __name__ == "__main__":
    main()
