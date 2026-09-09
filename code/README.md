# Code

Five standalone utilities. None of them is the pipeline and none imports the rest of the
system, so you can read `method/METHOD.md` without any of this. Each one exists because
something went wrong during the work in the paper.

| file | what it does | rationale |
|---|---|---|
| `luau_spans.py` | splits Luau source into code, string and comment spans | a regex rewrite that edits `wait()` inside a string literal yields a file whose code contradicts its own comments, and no later stage detects this |
| `blocks.py` | locates Luau function bodies with correct block matching | `end` closes any of `function`, `if`, `for`, `while` or a bare `do`, and the `do` in `for … do` belongs to the `for`. A regex cannot resolve this |
| `paired_test.py` | McNemar exact test over two evaluation runs | refuses to run unless both runs cover an identical task set. Section 6 of the paper records two comparisons we lost to the eval set changing between conditions |
| `best_checkpoint.py` | selects the lowest-validation checkpoint from an mlx-lm log | `mlx-lm` writes the *final* checkpoint to `adapters.safetensors`, which downstream tools load by default. In run 3 that checkpoint was 30% worse than the best one |
| `make_figures.py` | renders the paper's figures as standalone SVG | GitHub strips `<style>` out of embedded SVG and won't resolve CSS variables, so figures in Markdown need literal colours and a light/dark pair |

## Use

```bash
python paired_test.py baseline.jsonl adapter.jsonl
python best_checkpoint.py train.log adapters/run3
python make_figures.py
```

`paired_test.py` expects JSONL with `sample_id` and `ok` per line, which is the shape of
`results/run3_baseline.jsonl`. The statistics reported in section 4 can be reproduced directly:

```bash
python paired_test.py ../results/run3_baseline.jsonl ../results/run3_adapter.jsonl
```

`luau_spans.py` and `blocks.py` only speak Luau, but the requirement isn't language-specific.
Rewrite source in any language and you need a span-aware scanner before you start, and a real
block matcher the moment you touch structure.

Requires Python 3.11+. No dependencies.
