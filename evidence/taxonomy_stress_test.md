# AI boundary stress test (synthetic; not in the training dataset)

These eight invented comments test the proposed rules. They are explicitly
separate from the 200 real comments. Decisions below are Codex's analysis, not
James's unaided labels.

| Synthetic comment | Draft decision | Reason |
|---|---|---|
| This editor is obviously the fastest. | ungrounded | A comparison with no measurement or example. |
| This editor opened my 40 MB log in two seconds; the other froze. | grounded | Reports a concrete comparative observation, without proving it true. |
| I use this editor daily and love it. | ungrounded | Frequency of use does not explain or substantiate the praise. |
| I use this editor daily because it preserves my unsaved buffers after crashes. | grounded | Supplies a specific observed behavior supporting the preference. |
| My 40 MB file freezes the editor; is there a setting I should change? | request | Troubleshooting is the purpose; factual setup does not override it. |
| Why call this fast? It froze on every 40 MB file I opened. | grounded | Rhetorical question followed by supporting observation. |
| Nice project. Please add a keyboard shortcut for fullscreen. | request | Concrete feature request, even without a question mark. |
| Version 9 will obviously destroy every competitor. | ungrounded | A version number alone is not support for a prediction. |

## What the test clarified

The initial shorthand "specific details mean grounded" would misclassify the
last example. The final rule requires support for the main claim, not just a
number or proper noun. Firsthand experience counts when it describes the
observation behind the claim; bare ownership or liking does not.

Real borderline post: [49991267](https://news.ycombinator.com/item?id=49991267)
contains telescope-building experience and an iPhone SE 2022 detail, but ends
by asking whether the software works with weak night-sky signals. The strongest
case for `grounded` is that it supplies concrete experience and hardware.
The strongest case for `request` is that those details exist to make a genuine
compatibility question answerable. The written main-purpose precedence resolves
it to `request`; student review remains pending.
