"""McNemar exact test over two eval runs on the same tasks.

Unpaired pass rates hide what actually matters on a small eval set: did the adapter win
tasks the base model failed, or did it just trade? McNemar looks only at the discordant
pairs, so a rate difference built from equal gains and losses gets no credit.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from math import comb
from pathlib import Path


def load(path: Path) -> dict[str, dict]:
    return {json.loads(l)["sample_id"]: json.loads(l)
            for l in path.read_text().splitlines() if l.strip()}


def depth(rec: dict) -> int:
    # Published results carry a flat `gates_cleared` count instead of the full gate
    # report, so that generated code isn't redistributed. Read both shapes.
    if "gates_cleared" in rec:
        return int(rec["gates_cleared"])
    return sum(1 for g in rec.get("report", {}).get("gates", []) if g.get("ok"))


def main() -> int:
    a, b = load(Path(sys.argv[1])), load(Path(sys.argv[2]))
    # Every invalidated comparison in this project came from the eval set moving
    # underneath it, so bail out loudly rather than reporting a number.
    if set(a) != set(b):
        only_a, only_b = len(set(a) - set(b)), len(set(b) - set(a))
        print(f"REFUSING: task sets differ ({only_a} only in A, {only_b} only in B).\n"
              "A paired test on different tasks is not a comparison.")
        return 1

    ids = sorted(a)
    both = only_x = only_y = neither = 0
    gained, lost = [], []
    for i in ids:
        x, y = a[i]["ok"], b[i]["ok"]
        if x and y: both += 1
        elif x and not y: only_x += 1; lost.append(i)
        elif y and not x: only_y += 1; gained.append(i)
        else: neither += 1

    pa = sum(1 for i in ids if a[i]["ok"]) / len(ids)
    pb = sum(1 for i in ids if b[i]["ok"]) / len(ids)
    da = sum(depth(a[i]) for i in ids) / len(ids)
    db = sum(depth(b[i]) for i in ids) / len(ids)

    print(f"paired on {len(ids)} identical tasks\n")
    print(f"  {'':<12}{'pass@1':>12}{'mean gates':>13}")
    print(f"  {'baseline':<12}{pa:>11.1%}{da:>13.2f}")
    print(f"  {'adapter':<12}{pb:>11.1%}{db:>13.2f}")
    print(f"  {'delta':<12}{pb-pa:>+11.1%}{db-da:>+13.2f}\n")
    print(f"  both pass {both} | adapter only {only_y} | baseline only {only_x} | neither {neither}")

    n = only_x + only_y
    if n:
        k = min(only_x, only_y)
        p = min(1.0, sum(comb(n, i) for i in range(k + 1)) / 2 ** n * 2)
        verdict = "significant at p<0.05" if p < 0.05 else "NOT significant"
        print(f"  McNemar exact two-sided p = {p:.4f} on {n} discordant pairs, {verdict}")
    else:
        print("  no discordant pairs; the two runs are identical on every task")

    shapes = Counter()
    for i in gained: shapes[a[i].get("report", {}).get("domain", "?")] += 1
    if gained:
        print(f"\n  gained ({len(gained)}): {', '.join(g[:30] for g in gained[:8])}")
    if lost:
        print(f"  lost   ({len(lost)}): {', '.join(l[:30] for l in lost[:8])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
