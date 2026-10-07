# TakeMeter — Hacker News technology discussions

> **Completed Unit 5 instructor example, with AI assistance.** At the instructor’s explicit request, Codex labeled the 20 formerly reserved comments, individually reviewed all 180 draft labels, wrote five acceptance criteria before training, and completed the Unit 5 training run. The model performed poorly, as documented below. This is not an unaided student exercise, and nothing has been submitted through the course portal.

## What This Does

TakeMeter classifies complete comments from public Hacker News technology discussions into `request`, `grounded`, and `ungrounded`. It distinguishes genuine requests from statements that supply concrete support and statements that do not. It measures what a comment provides in its own text, not whether the author is correct, trustworthy, or an expert.

This repository contains the completed 200-comment dataset, five preregistered acceptance criteria, an executed notebook, actual training results, and annotation provenance. The seed-42 model predicted only `grounded`, so completion of the build does **not** mean it is a useful classifier or that all acceptance criteria passed. Use the same repository for the separate Unit 6 evaluation.

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

**Precedence:** classify a genuine request by its main purpose, even if it supplies factual background. A rhetorical or self-answered question does not make a comment a `request`. Concrete feature suggestions directed at someone count as requests. Generic recommendations such as “use X because Y” are statements unless their main purpose is to seek an answer, action, or feature from an interlocutor. Then distinguish supported from unsupported statements using the rule above. The [eight synthetic boundary tests](evidence/taxonomy_stress_test.md) are separate from the real dataset.

## The Dataset

**Source:** 200 complete, unique public comments collected on 2026-10-07 from 24 technology threads using the [official Hacker News API](https://github.com/HackerNews/API). The [source manifest](data/source_manifest.csv) provides each comment’s author, timestamp, thread, and URL; the [raw source snapshot](evidence/source_comments.json) preserves HTML and plain text. The collector considered the first 25 direct comments per thread, retained live comments with 8–180 whitespace-delimited words, removed duplicate text, interleaved threads, and selected 200. HTML formatting was removed; comments were not truncated or generated. Original authors retain their rights; the API documentation’s license is not a blanket content license.

**Completed labeling process:** Codex read 40 comments to propose the taxonomy, initially reserved 20 comments for the student exercise, and drafted labels and rationales for the other 180. The user then identified themselves as the instructor and explicitly authorized an AI-assisted example. Codex labeled all 20 reserved comments and reviewed each of the other 180 against its full text and the written boundary rules. These 20 are **AI-labeled reserved rows, not unaided “cold” labels**. There is no claim that a human reviewed the 180 drafts.

The review changed one draft: [HN 49999760](https://news.ycombinator.com/item?id=49999760) moved from `ungrounded` to `grounded` because its explicit animation-smoothness comparison and linked reference supply support for the assessment. Other retained and ambiguous decisions have individual rationales. The [combined instructor review](data/instructor_review.json), [20-row labeling record](data/instructor_reserved20.json), [first 90 reviews](data/instructor_review_first90.json), [last 90 reviews](data/instructor_review_last90.json), and [completion record with file hashes](data/review_completed.json) preserve the process.

**Authoritative dataset:** [labels.csv](labels.csv) contains all 200 reviewed rows in one unsplit file with `text`, `label`, and `note`. Notes identify Codex AI, source URLs, rationales, the reserved/draft batch, and any correction or alternate label. Historical [review_items.json](data/review_items.json), [ai_draft_labels.json](data/ai_draft_labels.json), [community reading](evidence/community_reading.md), and [pre-review audit](evidence/draft_audit.md) preserve earlier states; their pending-review language is historical, not the current status. The original student worksheet is superseded for this instructor example and requires no further personal labeling steps.

<!-- COUNTS_START -->
| Final label | Count | Share of 200 |
|---|---:|---:|
| grounded | 108 | 54.0% |
| ungrounded | 49 | 24.5% |
| request | 43 | 21.5% |
| **Total** | **200** | **100.0%** |

All rows have a valid label. The largest class is below the course’s 70% ceiling, and all three meet the preregistered 20%–60% balance criterion.
<!-- COUNTS_END -->

### Hard cases and final decisions

1. [HN 49991267](https://news.ycombinator.com/item?id=49991267) supplies telescope experience and a phone model before asking whether weak night-sky signals work. It could look `grounded`, but **`request`** wins because compatibility information is its purpose.
2. [HN 49992110](https://news.ycombinator.com/item?id=49992110) opens with an opinion that Debug should never be inlined. It could look `ungrounded`, but the reported binary-size reduction after `#[inline(never)]` supports **`grounded`**. The dataset does not independently verify that report.
3. [HN 49999510](https://news.ycombinator.com/item?id=49999510) predicts a service will become pay-to-rank. A named product and an advertising analogy do not support the future outcome, so the final label is **`ungrounded`**.
4. [HN 49999760](https://news.ycombinator.com/item?id=49999760) combines aesthetic judgments with a specific smoothness comparison to linked Ciechanowski animations. The explicit comparison supports **`grounded`**, correcting the original draft; a reader emphasizing only the aesthetic preference could choose `ungrounded`.

**Limitations:** shorter top-level comments from one snapshot are overrepresented. Related threads can occur in different random splits even without duplicate text, so topic vocabulary can leak across splits. The labels are AI judgments under a written rule, not independently validated human ground truth. Requests and unsupported reactions are not inherently lower quality. With only seven test comments in each smaller class, per-label estimates are unstable.

## The Training Run

**Completed on 2026-10-07:** the runner executed the starter notebook’s Unit 5 sections 1–5 on the final 200-row CSV. [Criteria](criteria.md) and the reviewed dataset were committed at [`5709375740c1d165f4cf446794e436b63882e623`](https://github.com/jamespaek1/ai201-project3-takemeter-starter-v2026/commit/5709375740c1d165f4cf446794e436b63882e623) before the actual run. The [run summary](evidence/assignment-summary.json) records this commit and the exact dataset/criteria hashes, settings, timestamps, and completed status. The run took 17.91 seconds; that is machine execution time, not personal hours spent.

| Setting | Actual value |
|---|---|
| Base model | `distilbert-base-uncased` |
| Device | Apple Silicon GPU (`mps`) |
| Python / PyTorch | 3.12.14 / 2.14.1 |
| Epochs | 3 |
| Learning rate | 2e-5 |
| Batch size | 16 |
| Maximum tokens | 128 |
| Seed | 42 |
| Split method | Starter’s stratified 70/15/15 procedure |

**Hyperparameters:** all starter defaults were retained to establish the initial build result. No hyperparameter change, second assignment run, or stretch feature is claimed. Full comments remain in the CSV, but **29/200 inputs (14.5%) exceed 128 tokens** and are truncated for the model; the longest is 249 tokens. This can remove late evidence or a closing request. See the [validation record](evidence/validation.json).

The actual split is **139 train / 31 validation / 30 test**, not 140/30/30: the starter’s floating-point split calculation rounds the validation allocation upward. The original splitting code was preserved.

| Label | Train | Validation | Test |
|---|---:|---:|---:|
| request | 30 | 6 | 7 |
| grounded | 75 | 17 | 16 |
| ungrounded | 34 | 8 | 7 |
| **Total** | **139** | **31** | **30** |

### Actual seed-42 results

- **Accuracy:** 16/30 = **53.33%**.
- **Macro F1:** **0.2319**.
- **Per-label F1:** `request` **0.0000**, `grounded` **0.6957**, `ungrounded` **0.0000**.
- **Predictions:** all 30 test comments were classified as `grounded`; this exactly matches the test-set majority-class baseline.
- **Confidence ranking:** most-confident third accuracy **60%**, least-confident third **20%**, a **40-percentage-point gap**, with ten examples in each group. This does not establish calibrated probabilities or overcome the missing minority-class predictions.

The confusion matrix below uses actual labels as rows and predictions as columns.

| Actual / predicted | request | grounded | ungrounded |
|---|---:|---:|---:|
| request | 0 | 7 | 0 |
| grounded | 0 | 16 | 0 |
| ungrounded | 0 | 7 | 0 |

### Status against preregistered criteria

| Criterion | Unit 5 evidence | Current status |
|---|---|---|
| 1. Accuracy ≥0.70 for each seed | Seed 42: 0.5333 | **Failed for seed 42** |
| 2. Every label F1 ≥0.60 for each seed | Request and ungrounded: 0.0000 | **Failed for seed 42** |
| 3. Each label 20%–60% of the full dataset | 21.5%, 54.0%, 24.5% | **Met** |
| 4. Staff-set agreement ≥24/30 before adjudication | Staff consistency exercise not run | **Not evaluated; Unit 6** |
| 5. Confidence-third accuracy gap ≥0.15 for each seed | Seed 42: 0.40 | **Met for seed 42 only** |

The three-seed evaluation for **42, 7, and 2024**, the Unit 6 baseline comparison, and the staff consistency exercise have not been completed. Single-seed results do not establish that the full multi-seed criteria pass. Targets were not lowered after seeing the model’s failure. A likely issue to investigate in Unit 6 is the model’s failure to learn minority labels from this small dataset; the present run alone does not establish the cause.

**Evidence:** [results.json](results.json), [test_split.csv](test_split.csv), [executed notebook](executed-notebook.ipynb), [full run log](evidence/assignment-run.log), and [run summary](evidence/assignment-summary.json). The fine-tuned model and tokenizer are saved locally in ignored `models/unit5`; their weights are not committed to GitHub. [Final validation](evidence/validation.json) reloaded the saved model and reproduced the metrics and confusion matrix, confirmed 200 unique texts and no row overlap between the three splits, and checked the preregistered file hashes.

**Setup evidence:** the [environment log](evidence/environment.txt) reports nine checks passed and no failures; the expected Unit 6 baseline-download warning remains. The earlier [practice summary](evidence/practice-summary.json) and [practice log](evidence/practice-run.log) concern the separate 60-row fictional dataset and its `analysis`/`hot_take`/`reaction` taxonomy, not these assignment results.

**Optional reproduction:** preserve this completed run and model. Use a separate checkout of the preregistration commit above, set up its Python environment as described in [RUNNING.md](RUNNING.md), and execute:

```sh
.venv/bin/python scripts/run_notebook.py --csv labels.csv --labels request grounded ungrounded
```

The runner validates review metadata, file hashes, labels, and committed criteria; it refuses to overwrite an existing model, results, executed notebook, or assignment evidence. A separate checkout at the pre-training commit keeps the original evidence intact. No rerun is required to complete this instructor example.

## How I Used AI

**Disclosure:** the instructor explicitly asked Codex to label the 20 reserved comments, review the other 180, and write five acceptance criteria. Codex completed that work and the training execution. All annotations and criteria in this example are AI-assisted; no unaided student authorship, human cold labeling, human review, personal time spent, or course submission is claimed.

**Moment 1 — applying and reviewing the taxonomy:** Codex read the source comments, proposed the three distinctions, and exercised them with eight separate synthetic boundary tests. During full review, the definition of `request` was clarified to distinguish a genuine sought action from generic advice or rhetorical questions. Review also corrected comment 49999760 from `ungrounded` to `grounded` because its concrete comparison supplied support. The final annotation records retain rationales and plausible alternatives rather than implying the hard cases disappeared.

**Moment 2 — preregistration and honest measurement:** Codex wrote five numeric targets with community-specific reasons, committed them before training, and added runner validation for explicit instructor AI provenance and immutable dataset/criteria hashes. It then ran the actual starter model and recorded the poor majority-class result instead of replacing it with the successful practice run or claiming every criterion passed. The saved notebook and log show what executed; the separate review record identifies who supplied the labels.

The initial [180 AI drafts](data/ai_draft_labels.json) remain available for comparison with the final [200-entry instructor review](data/instructor_review.json). The [completion record](data/review_completed.json) explicitly records 20 AI-labeled reserved rows, 180 AI-reviewed drafts, and zero human cold or human-reviewed rows. Unit 6 remains a separate evaluation task, not an unreported step completed by AI here.

**Repository:** [jamespaek1/ai201-project3-takemeter-starter-v2026](https://github.com/jamespaek1/ai201-project3-takemeter-starter-v2026).
