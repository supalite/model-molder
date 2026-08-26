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

