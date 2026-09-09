# Licensing

Three kinds of content, three licences.

| path | licence |
|---|---|
| `code/` | Apache License 2.0, see `LICENSE` |
| `paper/`, `method/`, `README.md` | CC BY 4.0 |
| `results/`, `figures/` | CC0 1.0 (public domain dedication) |

`LICENSE` at the repository root carries the Apache 2.0 text, because GitHub reads that
file to label the repository and the code is the part most likely to be reused verbatim.

## Why Apache 2.0 rather than MIT

Apache 2.0 is permissive in the same way MIT is, and adds three things that matter here:

- **An express patent grant** (clause 3), bounded to the contributed code. Contributors cannot
  later assert patents against users of what they contributed.
- **Patent retaliation** (clause 3). Anyone who brings a patent claim over this work loses their
  licence to it.
- **A NOTICE requirement** (clause 4d). Derivative works must carry the `NOTICE` file, so
  attribution survives downstream rather than depending on goodwill.

Neither licence restricts what the copyright holder may do with the work. Publishing under
Apache 2.0 does not prevent commercial use, relicensing, or building a paid product on the
same method.

## Prose and figures: CC BY 4.0

Share and adapt the paper, the method specification and the figures, including
commercially, provided you credit the source. https://creativecommons.org/licenses/by/4.0/

## Results: CC0

Measurements are facts and are placed in the public domain. Use them without attribution,
though a citation is appreciated if they appear in a comparison.
https://creativecommons.org/publicdomain/zero/1.0/

## What these licences do *not* cover

**They do not license the method.** A licence on the utilities in `code/` says nothing about
the mutation-mining approach described in `method/METHOD.md`. Publishing that description
places it in the public record.

**Model weights are not published here.** If they ever are, note that the training corpus
included files under MIT, Apache-2.0 and CC BY 4.0, and CC BY requires attribution in
derivative works. `results/NOTICE.txt` lists all 1,249 sources requiring attribution and
should travel with any released weights.

Some training data was produced by hosted language models whose terms of service could not
be verified in every case. That question is open and is noted in the paper rather than
resolved.

**The corpus itself is not redistributed.** `results/corpus_summary.json` records what was
ingested and under which licences; the file contents remain with their original authors.
