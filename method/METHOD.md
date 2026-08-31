# Method

This is a specification rather than an implementation. It describes what each stage must do and the
decisions that turned out to matter, in enough detail to build your own version. It does
not contain our source.

Everything here is domain-agnostic except the gates. If your domain has a compiler, a type
checker, or anything that can execute an artefact and assert on the result, the rest
transfers. If it does not, this method does not apply to it.

---

## Stage 1. Corpus ingestion

Collect source files from repositories that declare a permissive licence.

**Requirements**

- Allowlist by SPDX identifier. Treat a missing licence as a rejection, not as an unknown.
  Most repositories in a niche ecosystem carry no licence file at all.
- Record, per file: licence, permanent URL, commit sha. You will want to regenerate an
  attribution notice later without re-crawling.
- Deduplicate on content, not on path. Ecosystems vendor the same libraries repeatedly.

**What we learned**

Curated registries beat breadth. A package-manager index (for us, Roblox's Wally) produced
repositories whose files passed the later verification stage at roughly twice the rate of
repositories found by a stars-based code search. If your ecosystem has a package registry,
enumerate it before you write a search query.

Rate limits are not the constraint people assume. An authenticated API token was worth
about 80x an unauthenticated one, which removed the problem entirely. We used no proxies
and rotated no credentials.

---

## Stage 2. Deterministic modernisation

Rewrite what a rule can guarantee before training sees the data.

**Requirements**

- Separate code from strings and comments before applying any rewrite. A deprecated call
  named inside a comment is prose. Rewriting it produces a file whose code contradicts its
  own documentation, and nothing downstream will catch that.
- Classify rules into three tiers: rewrite (unambiguous, applied), flag (legacy but not
  mechanically fixable, recorded), reject (anchored in removed APIs, file discarded).
- Rewrite rules should read code spans only. Flag and reject rules should read the whole
  file, since they frequently need to see inside a string literal.

**What we learned**

The two error modes in that last point are not symmetric, and the asymmetry is worth
working out for your own domain. Rejecting a file in error costs one training example.
Rewriting one in error produces a sample that still looks valid and will be trained on.

Check whether your domain's *official* corpus needs this. Roblox's own published
fine-tuning corpus needed 620 rewrites across its first 1,914 rows, had 281 rows that were
rejects outright, and 99.6% of it predated the language's type system.

---

## Stage 3. Mutation-based task mining

This is the core of the method. It manufactures training tasks whose correct answer already
exists and has been verified.

```
for each candidate file:
    verify ORIGINAL through every gate      -> must PASS, else discard
    inject a defect
    verify MUTANT through every gate        -> must FAIL, else discard
    emit (instruction, mutated file, original file) as a training sample
```

**Requirements**

- The original must pass before you mutate it. Otherwise you are teaching the model to
  reproduce code that does not work.
- The mutant must fail. This is mutation testing's kill criterion. A mutant your toolchain
  cannot distinguish from the original produces a sample that asks the model to make an
  edit whose necessity nobody can demonstrate. Count these and discard them.
- Group evaluation splits by source repository, never by file. See Stage 5.

**Operator design**

Each operator should be the inverse of something the model must get right. Ours:

| operator | inverse of | acceptance |
|---|---|---|
| deprecate | current idiom | kill-verified |
| hallucinate | real API knowledge | kill-verified |
| weaken_types | type discipline | kill-verified |
| implement_from_signature | module architecture | structural |

The last one is different and the difference matters. It removes function bodies while
keeping types, signatures and documentation, then asks for an implementation. A stub is
incomplete rather than broken, and often still type-checks, so a kill criterion would
reject every architectural task you could construct. We accept these structurally instead:
the reference passed every gate and some number of bodies were verifiably removed. That is
a weaker guarantee and should be reported separately rather than blended in.

**Sanity check your operators against ground truth.** One of our "hallucinated" API names
turned out to be real. The mutant was still killed, for an unrelated reason, so the sample
entered the dataset carrying a stated cause that was false. Verify every invented name
against your domain's published definitions.

**Yield.** Ours ran at 15.7% of candidate files, dominated by originals that failed their
own gates. That loss filters for quality and should not be optimised away.

