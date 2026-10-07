# Community reading — AI-assisted preparation

Community: public Hacker News technology discussions. Collection date: 2026-10-07.
Codex read the first 40 complete comments in the collected sample before proposing
the taxonomy below. This is an AI reading log, not a claim that James personally
completed the assignment's reading or labeling exercise.

## Distinctions visible in the reading

- Some comments ask for missing information or a change. For example, comment
  49997782 asks about incentives, while 49995842 asks for comparisons between
  durable execution products.
- Some opinions include observable support. Comment 49992110 reports a binary
  size reduction after a specific code change; 49997519 explains a Firefox
  layout measurement issue and links a fix.
- Some comments state a reaction or prediction without support. Comment 49998049
  criticizes LLM-written blog posts without an example, and 49999510 predicts
  paid ranking without evidence for that future outcome.
- Tone does not separate these groups: 49993455 is frustrated but identifies
  specific authentication behavior, whereas 49995453 mainly offers an analogy
  and an aesthetic judgment.

## Candidate taxonomy and precedence

1. `request`: main purpose is a genuine information/feature/action request.
2. `grounded`: otherwise, concrete support for the main claim is present.
3. `ungrounded`: otherwise, a reaction or claim without such support.

The hardest boundary is `grounded` versus `ungrounded`. A tool name, a number,
a URL, or a confident tone does not automatically count as evidence. There must
be a described observation, mechanism, example, quotation, or source that bears
on the main claim. A firsthand experience counts as reported support, not as
verified truth. A purely hypothetical analogy does not count. A supplied link
counts only when the comment explains what it supports. This classifier measures
the support supplied in text, not factual correctness or the author's expertise.

For mixed requests and claims: a genuine unanswered request that is the comment's
main purpose wins. A rhetorical question, or a question immediately answered by
the author, does not. Feature suggestions such as "it would be helpful to hear
the sound" count as requests. Background technical details do not override this.

## Sampling limits

The collector visited 24 technology threads from one front-page snapshot and
considered the first 25 direct comments per thread. It retained whole comments
of 8–180 whitespace-delimited words, removed exact duplicate text and dead/deleted
items, interleaved threads, and selected 200. HTML markup was converted to plain
text; no comment was shortened or rewritten. The original HTML and source IDs
are retained. This favors visible, shorter, top-level English discussions and is
not a representative sample of all Hacker News. Related comments can share a
thread across the starter's random splits; interpret later scores accordingly.

Twenty rows are reserved for James to classify without suggested labels. They
are not labeled `cold` until James supplies his own decisions. The other 180
will have AI draft labels requiring his individual review. No human reading,
review, authorship, time spent, training completion, or accuracy is assumed.
