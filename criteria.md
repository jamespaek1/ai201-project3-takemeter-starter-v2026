# Acceptance criteria — TakeMeter instructor example

These five targets were authored with Codex AI assistance at the instructor's
explicit request and committed before training on the 200 Hacker News comments.
They are example criteria, not a claim of unaided student authorship. The earlier
practice run used separate fictional posts and a different taxonomy.

In Unit 6, model-performance criteria must hold separately for seeds **42, 7,
and 2024**, using the starter's stratified 70/15/15 splits. Do not average away a
failed seed or lower a target after seeing results. Dataset balance is checked
once on the final unsplit CSV. Agreement requires the separate staff reference
set and is not inferred from model scores or agreement between AI reviewers.

## 1. Overall accuracy: at least 0.70

For each seed, at least **70%** of held-out posts must have the correct exact
label: `request`, `grounded`, or `ungrounded`. Compute correct predictions
divided by the full test-set size, without excluding ambiguous posts.

**Why this target:** the original drafts are roughly half `grounded`, so a model
that simply guesses the largest class can appear useful. A 0.70 target asks for
an improvement over that shortcut while allowing mistakes on mixed requests and
evidence boundaries in this small, informal-text dataset.

## 2. Per-label F1: at least 0.60 for every label

For each seed, the F1 score for **each of the three labels must be at least
0.60**, with `zero_division=0`. A missing prediction for one class counts as a
failure; do not drop that class or substitute macro F1 for its score.

**Why this target:** the smaller request and unsupported-statement classes have
about 40–60 examples apiece, so only about 6–9 may land in a test split. Their
scores will be noisy, but the classifier must still recognize them instead of
earning overall accuracy mainly from the supported statements. A 0.60 floor
requires usable precision and recall without demanding near-perfect learning
from that little data.

## 3. Dataset balance: every label between 20% and 60%

In the committed, unsplit `labels.csv`, each label must occupy **at least 20%
and no more than 60%** of all rows. For 200 examples this is 40–120 rows per
label. Count exact labels; missing labels are an error, not a fourth class.

**Why this target:** Hacker News has many explanatory statements, but questions
and reactions are essential to this task. The course's 70% ceiling alone could
leave a minority class with too few examples. The 20% floor preserves enough
examples to train and measure all three categories; the 60% cap restrains a
largest-class shortcut. It does not claim this curated sample represents the
community's natural distribution.

## 4. Annotation consistency: at least 24/30 staff-set agreement

In Unit 6, apply the supplied **staff taxonomy** to all 30 supplied staff posts,
before opening the staff labels. Exact agreement with that reference must be
**at least 24 of 30 (0.80)** before adjudication. Report every disagreement and
the labeling method; do not count post-adjudication edits toward this number.

**Why this target:** separating a genuine request from a rhetorical question,
and concrete support from a bare opinion, depends on applying written rules
consistently. The staff exercise offers an external reference for that skill.
An 80% target allows six ambiguous cases while requiring more than broad
agreement. Because the staff taxonomy differs from this project's taxonomy,
the result is a check of rule application, not proof that these 200 labels are
human-validated. An AI-assisted run must be reported as such.

## 5. Confidence usefulness: a 15-percentage-point accuracy gap

For each seed, rank held-out predictions by their maximum softmax probability,
using the notebook's existing confidence-third calculation. The accuracy of
the **most-confident third minus the least-confident third must be at least
0.15**. Keep equal group sizes (`floor(n_test/3)`), report that size, and use
the same grouping implementation for every seed. With 30 test posts, each
group has 10. This measures ranking usefulness, not calibrated probabilities.

**Why this target:** the hardest cases blend criticism, facts, and questions.
Confidence is useful for review triage only if it helps identify which posts
need attention. Requiring a 15-point advantage asks for a meaningful signal
while acknowledging the coarse ten-example groups; a confident model that
gets both groups equally right or wrong does not meet this criterion.
