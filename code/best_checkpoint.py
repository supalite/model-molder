"""Pull the lowest-validation-loss adapter checkpoint out of an mlx-lm training log.

    python best_checkpoint.py <train.log> <adapter_dir> [--out DIR]

mlx-lm writes the last checkpoint to `adapters.safetensors`, not the best one, and that
is the file every downstream tool loads by default. Unless `iters` happened to be sized
right in advance, training runs past the point where validation stops improving and the
default file is the most overfit adapter of the run. Run 1 finished at val 1.183 after
touching 0.866 at iter 100.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

VAL_RE = re.compile(r"Iter (?P<iter>\d+): Val loss (?P<loss>[\d.]+)")


def val_points(log: Path) -> list[tuple[int, float]]:
    return [(int(m["iter"]), float(m["loss"])) for m in VAL_RE.finditer(log.read_text())]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("adapter_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    points = val_points(args.log)
    if not points:
        print(f"no 'Val loss' lines in {args.log}", file=sys.stderr)
        return 1

    best_iter, best_loss = min(points, key=lambda p: p[1])
    final_iter, final_loss = points[-1]
    print(f"validation: {len(points)} checkpoints, "
          f"best iter {best_iter} ({best_loss:.3f}), final iter {final_iter} ({final_loss:.3f})")

    # Validation runs more often than `save_every`, so the best val point often has no
    # file behind it. Take the nearest saved checkpoint at or below it.
    saved = sorted(
        (int(p.name.split("_")[0]), p) for p in args.adapter_dir.glob("*_adapters.safetensors")
    )
    if not saved:
        print(f"no numbered checkpoints in {args.adapter_dir}", file=sys.stderr)
        return 1
    usable = [(i, p) for i, p in saved if i <= best_iter] or [saved[0]]
    pick_iter, pick_path = usable[-1]
    if pick_iter != best_iter:
        print(f"  (no file at iter {best_iter}; using nearest saved checkpoint {pick_iter})")

    out = args.out or args.adapter_dir.with_name(args.adapter_dir.name + "-best")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(args.adapter_dir / "adapter_config.json", out / "adapter_config.json")
    shutil.copy(pick_path, out / "adapters.safetensors")
    if final_loss > best_loss:
        print(f"  final checkpoint is {((final_loss / best_loss) - 1) * 100:.0f}% worse "
              f"than the best; evaluating the default would understate the adapter")
    print(f"wrote iter-{pick_iter} adapter -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
