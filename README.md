# TakeMeter — Hacker News technology discussions

> **Status: prepared for student review; not ready for submission.** The repository contains 200 real comments, an AI-assisted taxonomy, local training tools, and a successful isolated practice run. Twenty unaided labels, individual review of 180 AI drafts, five student-authored criteria, and the assignment training run remain. No course submission has been made.

## What This Does

TakeMeter classifies complete comments from the public Hacker News technology community into `request`, `grounded`, and `ungrounded`. It distinguishes genuine requests from statements that supply concrete support and statements that do not. It measures what a comment provides in its own text, not whether the author is correct, trustworthy, or an expert. Codex prepared the community reading and candidate taxonomy; James’s review is pending.

## Label Taxonomy

### `request`

**Definition:** A comment whose main purpose is to ask the community for information, troubleshooting, a comparison, or a concrete feature/action, even when it supplies background facts.

**Real example 1:** [HN 49997782](https://news.ycombinator.com/item?id=49997782)

> What is the incentive for me to spend my tokens on submitting reviews?

**Real example 2:** [HN 49999634](https://news.ycombinator.com/item?id=49999634)

> would be helpful to hear the sound as the viz goes by.

### `grounded`

**Definition:** A non-request comment that supplies at least one concrete observation, technical mechanism, reported firsthand event, explicit example, quotation, or source supporting its main claim.

**Real example 1:** [HN 49992110](https://news.ycombinator.com/item?id=49992110)

> I’m fairly convinced that Debug should never be inlined. Display probably neither, the fmt machinery is heavy enough that not inlining is probably not a bottleneck even in serialization-heavy workloads. I’ve had to #[inline(never)] some of my own Debug/Display impls, shrinking the binary by tens of kilobytes (out of a few hundred, so relatively a significant reduction).

**Real example 2:** [HN 49991744](https://news.ycombinator.com/item?id=49991744)

> The old versions of VIC-20 used a font called Microgramma.
> https://www.reddit.com/r/vintagecomputing/comments/1pjw7q6/t...
> https://en.wikipedia.org/wiki/Microgramma_(typeface)

### `ungrounded`

**Definition:** A non-request comment expressing an opinion, prediction, reaction, or general claim without concrete support for that claim in the comment itself.

**Real example 1:** [HN 49998049](https://news.ycombinator.com/item?id=49998049)

> I am continually impressed by the ability of LLMs to take trivial ideas and turn them into lengthy and obtuse blog posts with unnecessary analogies.

**Real example 2:** [HN 49999510](https://news.ycombinator.com/item?id=49999510)

> Seeing Armature's pitch, It's very easy to see this is going to be pay-to-rank-higher as the next move once some critical mass of people starts pointing out their agents for this site as a reference. Adwords for tooling!!

### The hardest boundary

**`grounded` versus `ungrounded`:** require concrete support that bears on the main claim: a described observation, technical mechanism, firsthand event, explicit example, quotation, or identified source. A number, URL, tool name, confident tone, ownership, or hypothetical analogy alone is insufficient. A reported firsthand observation counts as support without being independently verified.

**Precedence:** classify a genuine request by its main purpose, even if it supplies factual background. A rhetorical or self-answered question does not make a comment a `request`. Concrete feature suggestions count as requests. Then distinguish supported from unsupported statements using the rule above. The [eight synthetic boundary tests](evidence/taxonomy_stress_test.md) are separate from the real dataset.

## The Dataset

**Source:** 200 complete public comments collected on 2026-10-07 from 24 technology threads using the [official Hacker News API](https://github.com/HackerNews/API). [Source manifest](data/source_manifest.csv) provides each comment’s author, timestamp, thread, and URL; [raw source snapshot](evidence/source_comments.json) preserves HTML and plain text. The collector considered the first 25 direct comments per thread, retained live unique comments with 8–180 whitespace-delimited words, interleaved threads, and selected 200. HTML formatting was removed; comments were never truncated or generated. Original authors retain their rights; the API documentation’s license is not a blanket content license.

**Workflow:** Codex read 40 comments to propose candidate distinctions, then reserved 20 different comments without suggested labels. Their note is `pending_cold`, not `cold`. The other 180 receive explicitly marked AI draft labels. James must classify the reserved set unaided and read/correct every draft. AI drafts were prepared separately before student review; this is disclosed rather than presented as a completed personal labeling exercise. The worksheet hides drafts until the cold set is completed. All 200 comments remain in one unsplit `labels.csv`; only the notebook creates the 70/15/15 split.

<!-- COUNTS_START -->
| Label | AI draft count | Share of 180 drafts | Status |
|---|---:|---:|---|
| grounded | 97 | 53.9% | Individual student review pending |
| ungrounded | 43 | 23.9% | Individual student review pending |
| request | 40 | 22.2% | Individual student review pending |
| Unlabeled cold rows | 20 | — | No AI suggestions provided |
| **All collected comments** | **200** | — | Not a fully labeled submission yet |

The draft distribution is below the 70% cap. Final counts must be computed after
all student decisions. With roughly 40–60 examples for a smaller label, only
about 6–9 may reach a 15% test split, so per-label results can be unstable.
<!-- COUNTS_END -->

### Three hard cases (AI draft decisions; student review pending)

1. [HN 49991267](https://news.ycombinator.com/item?id=49991267) supplies telescope experience and a phone model before asking whether weak night-sky signals work. It could look `grounded`, but `request` wins because compatibility information is its purpose.

2. [HN 49992110](https://news.ycombinator.com/item?id=49992110) opens with an opinion that Debug should never be inlined. It could look `ungrounded`, but the reported binary-size reduction after `#[inline(never)]` supports `grounded`. The text supplies evidence; the dataset does not independently verify the report.

3. [HN 49999510](https://news.ycombinator.com/item?id=49999510) predicts a service will become pay-to-rank. A named product and an advertising analogy could seem concrete, but neither supplies evidence for that future outcome, so the draft decision is `ungrounded`.

**Limitations:** shorter top-level comments from a single snapshot are overrepresented. Related threads can occur in multiple random splits even without duplicate text; later performance may partly reflect shared topic vocabulary. Requests and unsupported reactions are not inherently lower quality. Labels remain provisional until student review; neither final balance nor annotation consistency is established.

## The Training Run

**Assignment run: not started.** No root `results.json` or `test_split.csv` has been created. The five acceptance criteria must be written and committed before training. `criteria.md` intentionally remains the unfilled starter instead of attributing AI-written targets to James.

| Setting | Planned value |
|---|---|
| Base model | `distilbert-base-uncased` |
| Device | Apple Silicon GPU (`mps`) |
| Python / PyTorch | 3.12.14 / 2.14.1 |
| Epochs | 3 |
| Learning rate | 2e-5 |
| Batch size | 16 |
| Maximum tokens | 128 |
| Seed | 42 |
| Split | Starter’s stratified 70/15/15 |

No hyperparameter was changed. Full comments stay in the CSV, while tokenization may truncate model inputs at 128 tokens. Actual split sizes and per-label test counts will be recorded after the reviewed dataset is committed. No stretch feature is claimed.

**Environment verification:** the starter environment test passed 9 checks with 0 failures. The expected Unit 6 baseline-download warning remains. Native execution detects MPS; the shell sandbox reports CPU, so the practice run used native execution. [Environment log](evidence/environment.txt).

**Practice only:** sections 1–5 successfully ran on the starter’s separate 60-row fictional running-forum dataset and its original `analysis`/`hot_take`/`reaction` taxonomy. Defaults were unchanged, split sizes were 42/9/9, and all results are isolated under ignored `.cache/practice-run`. The [practice log](evidence/practice-run.log) and [practice summary](evidence/practice-summary.json) are setup evidence, not results for the 200-comment assignment.

### Finish the reviewed assignment run

1. Open `review.html` in your browser (or the already-open local worksheet) and supply 20 unaided labels, review all 180 drafts, and write five numbered criteria with numeric targets and reasons across at least three areas. Export its JSON.
2. Run `python scripts/import_review.py /path/to/takemeter-review.json`. The importer validates IDs, full text, labels, review completion, class balance, and criteria.
3. Review `criteria.md`, update this README with final counts and personal workflow, then commit `criteria.md`, `labels.csv`, and `data/review_completed.json`.
4. Run `python scripts/run_notebook.py --csv labels.csv --labels request grounded ungrounded`. It executes the notebook’s Unit 5 sections only and refuses unreviewed/uncommitted inputs.
5. Commit the actual `results.json`, `test_split.csv`, executed notebook, assignment logs, and updated README; push the same fork. The trained model/tokenizer stay in ignored `models/unit5`.

## How I Used AI

**Disclosure:** James requested that Codex complete Project 5. Codex created the fork, wrote collection/review tooling, read source comments, proposed the taxonomy, prepared draft labels, and ran the isolated practice pipeline. Student authorship, cold labeling, review, hours spent, and assignment results have not been asserted.

**Moment 1 — taxonomy boundaries:** Codex compared requests with statements in the first 40 comments and generated eight separate synthetic boundary examples. That test clarified that a number or product name alone is not evidence, and that a genuine request takes precedence over its factual setup. These are AI-assisted decisions awaiting James’s review.

**Moment 2 — implementation and verification:** Codex configured Python 3.12 and MPS, executed the actual starter notebook on practice data, and added validation so training cannot silently proceed with blank labels or uncommitted criteria. A separate Codex agent checked the runner’s failure cases.

**Pre-labeling:** the 180 non-cold comments receive Codex draft labels and individual rationales. They are not described as human-checked. The worksheet requires James to review each before export; imported notes distinguish unaided cold labels, reviewed AI labels, and corrections. James’s five criteria are left blank for his own targets and reasons.

**Repository:** https://github.com/jamespaek1/ai201-project3-takemeter-starter-v2026

Use this same repository for Units 5 and 6. See [RUNNING.md](RUNNING.md) for the starter workflow.
