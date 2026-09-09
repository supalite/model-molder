# model-molder

AI coding models write confident, well-structured code that calls functions which don't
exist. This is training data aimed at that, in domains where a machine can settle whether an
answer is right.

The trick is to work backwards. Take real open-source files that already pass a type checker,
a linter and an execution run. Break them on purpose. Keep the ones the toolchain can prove
are broken. Since we did the breaking, the human's original file is the answer, and no second
model has to produce it. Trained on 4,132 tasks mined this way from 1,278 Roblox repositories,
a 14B model went from 27 to 48 correct on 100 held-out tasks, drawn from repositories it never
saw during training.

What's here: the paper, a method spec detailed enough to reimplement from, the per-task
results, and five standalone utilities. Not the pipeline.

**[Read the paper](paper/PAPER.md)** · **[Plain-language version](paper/EXPLAINER.md)**
· **[Method specification](method/METHOD.md)**

---

## What this is

A 14B code model, fine-tuned on 4,132 tasks that were mined from real repositories and
verified by execution, went from 27 to 48 correct on 100 held-out tasks. The evaluation
split was grouped by source repository, both conditions were scored on an identical pinned
task file, and the comparison is paired (McNemar exact, p = 0.0005).

The technique behind the data is mutation testing, pointed at a different problem. Take a
file that passes every check, break it deliberately, confirm the toolchain can prove it
broken, keep the human's original as the reference answer. Nothing here calls a teacher
model, so a sample costs whatever the checks cost to run.

## What this repository contains

```
paper/     the write-up, and a plain-language version of it
method/    a specification of each stage, in enough detail to reimplement
results/   per-task outcomes, the experiment registry, corpus manifest, attribution notice
code/      five standalone utilities, each solving a problem we got wrong once
figures/   the figures as SVG, light and dark
```

You can reproduce the headline statistics from what is here:

```bash
cd code && python paired_test.py ../results/run3_baseline.jsonl ../results/run3_adapter.jsonl
```

The full pipeline isn't included, deliberately. The method is the part that travels. Our
implementation is welded to Roblox Luau, Blender, MLX and one Apple Silicon machine, so
copying it would mostly hand you our constraints. `method/METHOD.md` covers what each stage
has to do, plus the decisions that turned out to matter, which is the more useful half.

## How the data is made

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/fig1-funnel-dark.svg">
  <img alt="Mining funnel: 26,385 candidate files judged, 6,100 originals passed every gate, 4,132 tasks kept after the mutant-kill check. Task breakdown by operator: weaken_types 1,857, implement_from_signature 1,407, deprecate 508, hallucinate 360." src="figures/fig1-funnel-light.svg" width="100%">
</picture>

Files are only mined if the original passes every gate. Most of the loss is originals
failing their own checks. That's the filter working, not waste.

## Results

| | pass@1 | mean gates cleared |
|---|---:|---:|
| baseline | 27 / 100 | 2.93 |
| adapter | 48 / 100 | 3.40 |

Paired: 20 both pass, 28 adapter-only, 7 baseline-only, 45 neither.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/fig3-categories-dark.svg">
  <img alt="Tasks passed by category, baseline versus adapter. weaken_types 15 to 32 (+17), deprecate 5 to 11 (+6), teacher:blender 2 to 1 (-1), implement_from_signature 3 to 3 (0), hallucinate 2 to 1 (-1), teacher:roblox 0 to 0." src="figures/fig3-categories-light.svg" width="100%">
</picture>


Gains concentrate in the two mined Luau repair categories. Blender tasks, API-hallucination
tasks and module-writing tasks show no improvement. Per-category figures move by several
tasks between runs, so treat the breakdown as indicative.

`results/run3_baseline.jsonl` and `results/run3_adapter.jsonl` carry the per-task outcome
for every evaluation item, which is what a paired test needs. Generated code is not
included.

### Training

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/fig2-validation-dark.svg">
  <img alt="Validation loss across three runs. Run 1 with 118 rows bottoms at iteration 100 then degrades to 1.183. Run 2 with 207 rows descends to 0.617. Run 3 with 2,263 rows reaches 0.456 at iteration 500." src="figures/fig2-validation-light.svg" width="100%">
</picture>

Run 1 had 118 training rows. It burns through its signal inside a single pass and degrades
from there. Run 3 had 2,263 rows and gets to 0.456. The checkpoint we actually evaluated is
the lowest-validation one rather than the last, for reasons in `code/README.md`.

## Limitations

- One training seed, no ablations, no variance estimate on the training side.
- Evaluation tasks are produced by the same mutation operators used to build the training
  set, so the model is partly being examined on its own curriculum.
- Seven tasks regressed after fine-tuning.
- Two evaluation categories have fewer than ten tasks and support no conclusion.
- Scores carry roughly ±5 tasks of sampling noise, because generation wasn't seeded. Greedy
  decoding fixes this. It didn't get fixed in time for these numbers.

## Data provenance

Every ingested file came from a repository declaring a permissive SPDX licence; absent
licences were rejected rather than assumed. `results/NOTICE.txt` lists the 1,249 sources
requiring attribution, regenerated from the corpus manifest. `results/corpus_summary.json`
records the licence distribution.

Some training data came out of hosted language models whose terms we couldn't verify in
every case. Anyone planning to publish weights has to deal with that. The paper flags it; it
doesn't settle it.

## Licence

`code/` is Apache 2.0. The paper, method and README are CC BY 4.0. Results and figures are CC0.
See [LICENSES.md](LICENSES.md), which also covers what these do not extend to: the model
weights are not published here, and the corpus itself is not redistributed.
