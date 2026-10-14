# TakeMeter — Hacker News technology discussions

> **Completed Unit 5 instructor example, with AI assistance.** At the instructor’s explicit request, Codex labeled the 20 formerly reserved comments, individually reviewed all 180 draft labels, wrote five acceptance criteria before training, and completed the Unit 5 training run. The model performed poorly, as documented below. This is not an unaided student exercise, and nothing has been submitted through the course portal.

> **Unit 6 status (2026-10-14):** both zero-shot baselines and all six before/after training runs are complete, with run logs, diagnoses and the confidence check below. The required staff agreement score and adjudication are **pending the authentic `data/staff_labels.csv`**; the linked staff repository is inaccessible to the connected account. This is not yet a complete Unit 6 submission.

## What This Does

TakeMeter classifies complete comments from public Hacker News technology discussions into `request`, `grounded`, and `ungrounded`. It distinguishes genuine requests from statements that supply concrete support and statements that do not. It measures what a comment provides in its own text, not whether the author is correct, trustworthy, or an expert.

This repository contains the completed 200-comment dataset, five preregistered acceptance criteria, an executed notebook, actual training results, and annotation provenance. The seed-42 model predicted only `grounded`, so completion of the build does **not** mean it is a useful classifier or that all acceptance criteria passed. The Unit 6 continuation below evaluates the same dataset and retains the original evidence.

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

**Historical Unit 5 status:** at the time of this run, the three-seed evaluation for **42, 7, and 2024**, the Unit 6 baseline comparison, and the staff consistency exercise had not been completed. The current Unit 6 status is recorded below. Single-seed results do not establish that the full multi-seed criteria pass. Targets were not lowered after seeing the model’s failure. A likely issue to investigate in Unit 6 is the model’s failure to learn minority labels from this small dataset; the present run alone does not establish the cause.

**Evidence:** [results.json](results.json), [test_split.csv](test_split.csv), [executed notebook](executed-notebook.ipynb), [full run log](evidence/assignment-run.log), and [run summary](evidence/assignment-summary.json). The fine-tuned model and tokenizer are saved locally in ignored `models/unit5`; their weights are not committed to GitHub. [Final validation](evidence/validation.json) reloaded the saved model and reproduced the metrics and confusion matrix, confirmed 200 unique texts and no row overlap between the three splits, and checked the preregistered file hashes.

**Setup evidence:** the [environment log](evidence/environment.txt) reports nine checks passed and no failures; the expected Unit 6 baseline-download warning remains. The earlier [practice summary](evidence/practice-summary.json) and [practice log](evidence/practice-run.log) concern the separate 60-row fictional dataset and its `analysis`/`hot_take`/`reaction` taxonomy, not these assignment results.

**Optional reproduction:** preserve this completed run and model. Use a separate checkout of the preregistration commit above, set up its Python environment as described in [RUNNING.md](RUNNING.md), and execute:

```sh
.venv/bin/python scripts/run_notebook.py --csv labels.csv --labels request grounded ungrounded
```

The runner validates review metadata, file hashes, labels, and committed criteria; it refuses to overwrite an existing model, results, executed notebook, or assignment evidence. A separate checkout at the pre-training commit keeps the original evidence intact. No rerun is required to complete this instructor example.

## How I Used AI

**Unit 6 continuation:** Codex wrote the pre-baseline prediction, applied the staff taxonomy to all 30 posts before reference access, ran both local BART baselines, built and checked an evidence-preserving notebook runner, executed six actual DistilBERT runs, and drafted the diagnoses and report. Codex proposed the single epoch change after examining the before-run losses and committed that plan before running the after phase. A separate AI review checked the runner and measurements; this is an additional code/evidence check, not independent human ground truth.

**What AI could not complete:** the official staff key was inaccessible, so no agreement score or adjudications were invented. The 17 guard tests and metric re-computation check execution and arithmetic, not semantic correctness of the 200 AI labels. No human review, personal hours, or portal submission is claimed.

**Disclosure:** the instructor explicitly asked Codex to label the 20 reserved comments, review the other 180, and write five acceptance criteria. Codex completed that work and the training execution. All annotations and criteria in this example are AI-assisted; no unaided student authorship, human cold labeling, human review, personal time spent, or course submission is claimed.

**Moment 1 — applying and reviewing the taxonomy:** Codex read the source comments, proposed the three distinctions, and exercised them with eight separate synthetic boundary tests. During full review, the definition of `request` was clarified to distinguish a genuine sought action from generic advice or rhetorical questions. Review also corrected comment 49999760 from `ungrounded` to `grounded` because its concrete comparison supplied support. The final annotation records retain rationales and plausible alternatives rather than implying the hard cases disappeared.

**Moment 2 — preregistration and honest measurement:** Codex wrote five numeric targets with community-specific reasons, committed them before training, and added runner validation for explicit instructor AI provenance and immutable dataset/criteria hashes. It then ran the actual starter model and recorded the poor majority-class result instead of replacing it with the successful practice run or claiming every criterion passed. The saved notebook and log show what executed; the separate review record identifies who supplied the labels.

The initial [180 AI drafts](data/ai_draft_labels.json) remain available for comparison with the final [200-entry instructor review](data/instructor_review.json). The [completion record](data/review_completed.json) explicitly records 20 AI-labeled reserved rows, 180 AI-reviewed drafts, and zero human cold or human-reviewed rows. The Unit 6 work and remaining reference dependency are disclosed in the continuation below.

**Repository:** [jamespaek1/ai201-project3-takemeter-starter-v2026](https://github.com/jamespaek1/ai201-project3-takemeter-starter-v2026).


# Unit 6 — TakeMeter testing (instructor AI-assisted example)

## Baseline vs. Trained

**Prediction recorded before the Unit 6 baseline run:** given the already-known
Unit 5 result that predicts `grounded` for every test post, the trained model may
beat the zero-shot model on `grounded` recall (currently 1.00), but the baseline
is expected to do better on `request` and `ungrounded` F1. This prediction is made
before seeing baseline results; it does not pretend the Unit 5 trained result
was unseen.

The baseline will use the unchanged `label_definitions.txt` and all 30 original
`test_split.csv` posts. A separate bare-label run will measure the effect of
supplying definitions; it will not replace the primary baseline.

**Declared before execution:** include the confidence-check stretch by comparing
most- and least-confident thirds for each of three seeds before and after the
single improvement. This is also the evidence for original criterion 5. No
second improvement or taxonomy change is planned. Labels, taxonomy and the five
original criteria remain fixed; choose the one training change only after the
before-run diagnosis. Continue the explicit AI-assisted instructor provenance
from Unit 5, including the separate staff annotation exercise.


### Observed baseline comparison

The primary BART MNLI baseline used the exact three definition lines and **all 30
original Unit 5 held-out comments**, in the original order. The trained column
is the preserved Unit 5 seed-42 model; differences are trained minus baseline.

| Measure | Zero-shot with definitions | Unit 5 trained | Difference |
|---|---:|---:|---:|
| Accuracy | 0.5333 | 0.5333 | 0.0000 |
| Macro F1 | 0.2370 | 0.2319 | -0.0052 |
| Grounded F1 | 0.7111 | 0.6957 | -0.0155 |
| Request F1 | 0.0000 | 0.0000 | 0.0000 |
| Ungrounded F1 | 0.0000 | 0.0000 | 0.0000 |

The forecast was not supported: grounded recall tied at 1.00, and the baseline
also failed to recognize either minority class. BART predicted 29 grounded and
one incorrect ungrounded; the trained model predicted 30 grounded. The small
macro-F1 difference does not indicate a useful three-way classifier.

The additional bare-name baseline scored accuracy **0.3333**, macro F1 **0.2605**,
grounded F1 **0.3200**, request F1 **0.4615**, and ungrounded F1 **0.0000**.
Definitions raised accuracy by 0.20 but reduced request F1 and macro F1; they
changed the error pattern rather than uniformly improving performance. Both
runs use the same BART model, hypothesis template, data and split. These are
small-sample observations, not evidence that definitions are generally harmful.

Evidence: [primary baseline](baseline_results.json), [bare-name diagnostic](baseline_bare_names_results.json),
[definitions log](evidence/unit6/baseline-definitions.log), and
[bare-name log](evidence/unit6/baseline-bare-names.log).

## Run Log — Before

Actual runs used seeds **42, 7 and 2024**, `distilbert-base-uncased`, three epochs,
initial learning rate 0.00002, batch size 16 and maximum input length 128.
Device: Apple Silicon GPU (MPS), Torch 2.14.1. Each stratified split contains
139 training, 31 validation and 30 test rows, with test supports request 7,
grounded 16 and ungrounded 7. The same seed controls the split and model/training
randomness, so this experiment does not isolate those two sources of variation.

| Measure | Seed 42 | Seed 7 | Seed 2024 | Max − min |
|---|---:|---:|---:|---:|
| Accuracy | 0.5333 | 0.5333 | 0.5333 | 0.0000 |
| Macro F1 | 0.2319 | 0.2319 | 0.2319 | 0.0000 |
| Request F1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Grounded F1 | 0.6957 | 0.6957 | 0.6957 | 0.0000 |
| Ungrounded F1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

| Original criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Overall verdict |
|---|---|---|---|---|---|
| 1. Accuracy | ≥0.70 each seed | 0.5333 — MISSED | 0.5333 — MISSED | 0.5333 — MISSED | MISSED |
| 2. Every label F1 | ≥0.60 each label, each seed | min 0.0000 — MISSED | min 0.0000 — MISSED | min 0.0000 — MISSED | MISSED |
| 3. Full-CSV balance | Each label 20–60% | Shared dataset | Shared dataset | Shared dataset | MET: 21.5%, 54.0%, 24.5% |
| 4. Staff agreement | ≥24/30 before adjudication | Shared external check | Shared external check | Shared external check | PENDING: authentic staff reference unavailable |
| 5. Confidence ranking | High-third minus low-third accuracy ≥0.15 each seed | 0.60 − 0.20 = 0.40 — MET | 0.90 − 0.30 = 0.60 — MET | 0.60 − 0.30 = 0.30 — MET | MET |

Criterion 5 uses ten examples in each third. Criteria 3 and 4 are shared checks,
not three independent measurements. MET for a seed-dependent criterion requires
all three seeds to meet the original target. Zero spread here means repeatable
majority-class collapse; it does **not** mean reliable classification. This
qualifies the starter notebook's generic “Stable enough to trust” message.

### Confusion matrix and direction

Rows are actual labels; columns are predictions. **All three before seeds have
this same matrix** (though they contain different test comments).

| Actual / predicted | request | grounded | ungrounded |
|---|---:|---:|---:|
| request | 0 | 7 | 0 |
| grounded | 0 | 16 | 0 |
| ungrounded | 0 | 7 | 0 |

There is a tie for the largest off-diagonal: **request → grounded: 7** and
**ungrounded → grounded: 7**. Both reverse directions have zero errors. This is
collapse toward the largest class, not just a two-label swap. The full dataset
contains 43 request, 108 grounded and 49 ungrounded comments. Both minority
labels exist in training (30 request and 34 ungrounded per split), so they were
not lost through an empty training class.

## Verdicts and Diagnoses

**Criterion 1 — MISSED.** The 53.33% accuracy equals always predicting the test
majority class, with no variation across seeds. The matrix and 54% grounded
training-corpus share support a majority shortcut. The dataset meets the balance
rule, but that rule does not guarantee the model will learn each class. The
missing staff reference prevents external assessment of annotation consistency;
we cannot conclude that label noise is or is not the cause.

**Criterion 2 — MISSED.** Request and ungrounded have zero precision, recall and
F1 in every seed because neither is ever predicted. Grounded F1 alone clears
0.60. Three epochs provide only 27 optimizer steps. Validation loss falls
through epoch 3 for every seed: **1.0137 → 0.9814**, **0.9839 → 0.9566**, and
**0.9849 → 0.9371** (seed order 42, 7, 2024), while validation accuracy remains
17/31. This is evidence compatible with insufficient optimization, not proof
of it. A one-parameter training experiment is more directly motivated by these
curves than relabeling examples merely to improve the score.

**Criterion 3 — MET.** The 21.5%/54.0%/24.5% label shares meet the original
20–60% limits. Seven test examples per minority class still make their metrics
coarse and sensitive to individual errors; balance alone is insufficient.

**Criterion 4 — PENDING.** All 30 blind staff-taxonomy labels are saved, but the
authentic answer key is unavailable. There is no agreement score to use as
support for a consistency diagnosis, and no disagreement adjudication is
claimed. The staff taxonomy also differs from the project taxonomy.

**Criterion 5 — MET.** Gaps of 0.40, 0.60 and 0.30 meet the target. Confidence
ranks some correct majority-class predictions above wrong ones, even while both
minority classes fail. This measures triage ranking only, not calibration or
usable overall classification.

## Agreement Report

Codex AI labeled all 30 staff posts using the supplied staff taxonomy and
committed them in `778d8b0` before opening any reference answers. All texts match
the source exactly. Labels: 11 analysis, 9 hot_take and 10 reaction. These are
AI-assisted instructor annotations, not human cold labels.

The authentic `data/staff_labels.csv` remains unavailable. The instructor guide
links the [official staff repository](https://github.com/codepath/ai201-project3-takemeter-staff-v2026),
but authenticated access returned HTTP 404. That response does not establish
whether the repository is private, unavailable, or inaccessible to this account.
**Agreement and every-disagreement adjudication remain pending; criterion 4 is
not scored.** No substitute answer key, invented score, or empty successful
`agreement_results.json` has been created.

The [status record](evidence/unit6/agreement-status.json) includes the input hashes,
text checks and resume command. After the authentic key is supplied, preserve
`my_staff_labels.csv` and run:

```sh
.venv/bin/python agreement.py --staff-posts data/staff_posts.csv --staff-labels data/staff_labels.csv --mine my_staff_labels.csv --out agreement_results.json
```

Then report the pre-adjudication numerator out of 30 and, for **every** actual
disagreement, quote the post, show both labels, explain a decision, and classify
it as (a) loose rule application, (b) a definition gap, or (c) a defensible
ambiguous reading. The blind rationale flags `sp_014` as ambiguous; this is not
a claim that it disagrees with staff. Reference agreement would evaluate applying
the separate staff taxonomy, not validate all 200 project labels as human truth.

## The Improvement

**Exactly one declared change: EPOCHS 3 → 10.** The [committed plan](evidence/unit6/improvement_plan.json)
was written after the before diagnosis and before the after runs. The goal is
to test whether extra optimization breaks majority-class collapse. Ten epochs
provide 90 optimizer steps. Initial learning rate, batch size, model, maximum
length, labels, taxonomy, split seeds, device and acceptance criteria stay the
same. The unchanged default linear learning-rate schedule consequently spans
90 rather than 27 steps; this follows from the epoch change and is not a
separate tuned parameter.

This is a hypothesis-driven experiment with incomplete annotation evidence,
not a promise that more epochs will help. The planned stopping rule is one
10-epoch run per seed, followed by honest reporting; no further tuning on these
test sets. Because the assignment uses test results to diagnose and choose this
change, a future performance claim needs a fresh untouched evaluation set.


### Run Log — After

The declared ten-epoch experiment completed for all three seeds on MPS. It used
exactly the same train, validation and test rows in the same order for each
corresponding seed. No row labels, definitions, criteria or other training
parameters were edited. Scores below use the final epoch, as in the starter;
there was no best-epoch selection or second improvement.

| Original criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Overall verdict |
|---|---|---|---|---|---|
| 1. Accuracy | ≥0.70 each seed | 0.6333 — MISSED | 0.5667 — MISSED | 0.5667 — MISSED | MISSED |
| 2. Every label F1 | ≥0.60 each label, each seed | min 0.2500 — MISSED | min 0.0000 — MISSED | min 0.0000 — MISSED | MISSED |
| 3. Full-CSV balance | Each label 20–60% | Shared dataset | Shared dataset | Shared dataset | MET: 21.5%, 54.0%, 24.5% |
| 4. Staff agreement | ≥24/30 before adjudication | Shared external check | Shared external check | Shared external check | PENDING: authentic staff reference unavailable |
| 5. Confidence ranking | High-third minus low-third accuracy ≥0.15 each seed | 0.80 − 0.60 = 0.20 — MET | 1.00 − 0.40 = 0.60 — MET | 0.60 − 0.40 = 0.20 — MET | MET |

Both full run logs appear above. This direct comparison puts the model scores
side by side; the three seeds' held-out sets overlap, so these are not 90
independent test observations.

| Measure | Seed 42 before → after | Seed 7 before → after | Seed 2024 before → after |
|---|---:|---:|---:|
| Accuracy | 0.5333 → 0.6333 | 0.5333 → 0.5667 | 0.5333 → 0.5667 |
| Macro F1 | 0.2319 → 0.4795 | 0.2319 → 0.3258 | 0.2319 → 0.3204 |
| Request F1 | 0.0000 → 0.4444 | 0.0000 → 0.2500 | 0.0000 → 0.0000 |
| Grounded F1 | 0.6957 → 0.7442 | 0.6957 → 0.7273 | 0.6957 → 0.7111 |
| Ungrounded F1 | 0.0000 → 0.2500 | 0.0000 → 0.0000 | 0.0000 → 0.2500 |

**Did it help?** Yes, modestly: correct predictions increased from 16 to **19,
17 and 17 of 30**, and macro F1 improved in every seed. The change partly broke
the majority shortcut, but no seed met the accuracy target or every-label F1
target. Grounded recall remains 1.00, while minority recall is at most 2/7.
The after seed-42 result also exceeds the zero-shot definition baseline on the
same original held-out posts (accuracy 0.6333 vs 0.5333; macro F1 0.4795 vs
0.2370). The other seeds use different test posts and are not paired baseline
comparisons.

After accuracy spans **0.5667–0.6333**, a 0.0667 range; macro F1 spans
**0.3204–0.4795**, a 0.1592 range. Request F1 ranges from 0 to 0.4444, so a
modest accuracy spread hides unstable minority-label learning. The notebook's
generic uncertainty message does not replace the preregistered rule: criterion
1 is unambiguously MISSED because every observed accuracy is below 0.70.

### After confusion matrices

Rows are actual labels; columns are predictions. All three matrices are shown
to avoid presenting only the strongest seed.

**Seed 42**

| Actual / predicted | request | grounded | ungrounded |
|---|---:|---:|---:|
| request | 2 | 5 | 0 |
| grounded | 0 | 16 | 0 |
| ungrounded | 0 | 6 | 1 |

**Seed 7**

| Actual / predicted | request | grounded | ungrounded |
|---|---:|---:|---:|
| request | 1 | 5 | 1 |
| grounded | 0 | 16 | 0 |
| ungrounded | 0 | 7 | 0 |

**Seed 2024**

| Actual / predicted | request | grounded | ungrounded |
|---|---:|---:|---:|
| request | 0 | 7 | 0 |
| grounded | 0 | 16 | 0 |
| ungrounded | 0 | 6 | 1 |

For seed 42, the largest off-diagonal is now **ungrounded → grounded: 6**,
versus **grounded → ungrounded: 0**. Seed 7 has seven ungrounded → grounded
errors, and seed 2024 has seven request → grounded errors. The main remaining
problem is still the model treating unsupported statements or genuine requests
as supported statements. The direction alone cannot establish label noise;
that automatic suggestion in the starter is a hypothesis, and the missing
staff comparison cannot confirm it.

### Declared stretch — confidence check

Every before and after confidence gap exceeds 0.15, using the unchanged notebook
ranking and ten examples per third. After mean confidence for correct versus
incorrect predictions is **0.6670 vs 0.6025**, **0.7146 vs 0.5808**, and
**0.6567 vs 0.5703** for seeds 42, 7 and 2024 respectively. Higher confidence
therefore gives some ranking information on these samples. It is still a weak
basis for automation: the high-confidence group is only 60% accurate for
seed 2024, and moving a single example changes a third's accuracy by 0.10.

Two concrete counterexamples from the saved after predictions show why scores
must not be treated as verified correctness:

- **Seed 42, row-180:** the generic piracy/product-advice comment is labeled
  ungrounded but predicted grounded with score **0.7656**. “IME” and technical
  vocabulary do not themselves supply a reported concrete event supporting the
  whole claim under this taxonomy.
- **Seed 7, row-060:** “How do you compare to Azure Durable Functions, Temporal,
  AWS Lambda Durable Functions?” is part of a genuine comparison request, yet
  the model predicts grounded with score **0.7689**. Named tools and background
  context do not override request precedence.

These are illustrative high-confidence errors, not an additional relabeling
pass or a calibration test. Gold labels remain the original AI annotations;
uncertainty about those annotations remains an independent limitation.

## What's Still Broken

| Remaining criterion | Evidence after the change | Next step, and why this run stopped |
|---|---|---|
| 1. Accuracy ≥0.70 — MISSED | 19/30, 17/30, 17/30; 11–13 errors remain per seed, mostly toward grounded | Collect a larger, independently reviewed evaluation set separated by HN thread, then test whether gains generalize. Stop here to honor the one-change plan and avoid tuning repeatedly against the same held-out comments. |
| 2. Every label F1 ≥0.60 — MISSED | Request F1 0.4444/0.2500/0.0000; ungrounded F1 0.2500/0.0000/0.2500 | Obtain an independent annotation audit of mixed requests and unsupported technical advice, then consider targeted examples under the unchanged rules. More epochs alone did not resolve these boundaries. Further annotation/data or training changes would be a separate experiment. |
| 4. Staff agreement ≥24/30 — PENDING | All 30 blind labels exist; reference key inaccessible | Obtain the authentic staff CSV from the TF/instructor resource, run agreement.py, and adjudicate every disagreement. This dependency, rather than time or an assumed score, prevents completing the agreement report. |

Criteria 3 and 5 remain MET; that does not cancel the accuracy and minority-F1
failures. The final original-criterion tally is **2 MET, 2 MISSED, 1 PENDING**.

**Diagnosis after testing the change:** the gains support undertraining as one
contributor to the original collapse, but small training samples and difficult
boundaries remain plausible contributors to the residual errors. Longer
training also shows diminishing returns: seed 42 validation loss bottoms near
epoch 4 (0.9707) and ends at 1.0036; seed 7 bottoms near epoch 3 (0.9368) and ends
at 0.9645, while training loss decreases. This is consistent with emerging
overfitting for those two seeds; seed 2024 validation loss continues falling,
so the pattern is not uniform. Simply adding still more epochs is not an
evidence-based completion step. The missing staff agreement and lack of an
independent human audit prevent attributing the remaining errors confidently
to annotations versus the model. Maximum length remains 128 (29 original
comments exceed it), and shared discussion topics across random splits remain
limitations; neither was changed in this experiment.

**Intended versus learned, in two sentences:** The labels were intended to
capture a comment's main purpose and whether its own text supplies support,
with genuine requests taking precedence over background facts. The after
matrices show that the model still mostly learned to choose grounded—27, 28
and 29 predictions out of 30—with only weak and seed-dependent recognition of
requests and unsupported statements.

### Evidence, verification and completion status

- [Before results](results_three_seeds_before.json) and [after results](results_three_seeds_after.json) retain the starter's result format.
- [Before executed notebook](evidence/unit6/before-executed.ipynb) and [after executed notebook](evidence/unit6/after-executed.ipynb) show the executed cells and outputs; the original Unit 5 notebook/output files remain unchanged.
- [Before summary](evidence/unit6/before-summary.json) and [after summary](evidence/unit6/after-summary.json) record device, package versions, settings, hashes and machine runtime. Machine runtimes are not personal hours spent.
- [Before log](evidence/unit6/before-run.log), [after log](evidence/unit6/after-run.log), per-seed prediction JSONs and split inventories in [evidence/unit6](evidence/unit6) preserve the detailed evidence. The legacy field `csv_line` means the logical CSV record number including the header, **not** the physical file line for multiline comments.
- [Independent metric validation](evidence/unit6/validation.json) recomputes accuracy, all per-label metrics, confusion matrices and confidence thirds from the saved predictions. It checks exact baseline held-out rows, split separation within every trial, identical corresponding before/after splits, one changed setting, unchanged Unit 5 file hashes and 30 exact staff exercise texts. Status: `passed_with_pending_agreement`; there are no validation errors.
- [Runner tests](evidence/unit6/runner-tests.log): 17 passed. [Course environment check](evidence/unit6/environment.log): nine passed, zero failed. Its BART-download warning checks only the default home cache; both actual baselines succeeded using this repository's `.cache/huggingface` through `HF_HOME`.

The local saved after model in ignored `models/unit6_after` is the final seed
2024 model, not a selected best seed. Model weights and the virtual environment
are deliberately not committed. The [run script](scripts/run_unit6.py) refuses
to overwrite completed evidence; reproduction should use a separate checkout,
the preserved settings and the committed improvement plan. To cross-check
existing results without training, run:

```sh
.venv/bin/python scripts/validate_unit6.py
```

The history contains more than four new Unit 6 commits, including the baseline
forecast, blind staff labels, baseline results, and the before diagnosis/plan
before the after results. **The remaining required deliverable is the genuine
staff comparison and its adjudications. No course-portal submission has been
made, and this repository must not be described as fully complete until that
reference-dependent work is finished.**
