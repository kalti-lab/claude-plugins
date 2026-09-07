---
name: kalti-contrib
disable-model-invocation: true
description: "Shows what each kalti member has put into the vault, as three plain numbers side by side: 연구노트 (journals written), 카드 (times those journals were drawn on by ontology cards), and 밀도 (카드 ÷ 연구노트). Invoke with /kalti-contrib for the whole lab over the whole period, or /kalti-contrib --write to also save a dated snapshot under reports/contrib/. A bar summary up top makes the three columns comparable at a glance; below it each member gets their period, work-type mix, projects, and a short paragraph written from actually reading their three most-drawn-on journals. It never computes a total score, never ranks, and never writes to journals/ or ontology/ — the three numbers order the members differently on purpose, and judging them is left to the reader."
---

# kalti contribution view

The vault has two layers that hold work — `journals/` (evidence, one member's own record) and `ontology/` (curated knowledge, shared). A journal earns its keep when a card draws on it. This skill counts that crossing, per member.

It exists because the obvious number is misleading. On kalti's vault the journal counts run 187 / 67 / 12 — a fifteen-fold spread — while the same members' 밀도 runs 2.0 / 2.5 / 3.5, in the opposite order. Either number alone tells a false story. Shown side by side they tell a true one: one member works broad, one works fast, one works deep.

## This is a reference view, not a score

**Never produce a total, a rank, or a winner.** Not as a table, not as a sentence, not as an aside about who "leads". The three numbers are deliberately left unreduced because combining them requires an exchange rate — how many 카드 is one 연구노트 worth — that nothing in the vault can supply. On kalti's numbers, plausible weightings flip first and last place completely. A ranking would report the weighting, not the work.

So the reader judges. This skill's whole job is to lay the three numbers out clearly, say what kind of work each member does, and stop.

Two further limits, both of which belong in the output rather than in this file only:

- **밀도 responds to writing habits.** Cards are extracted by `/kalti-ontology`, which pulls best from journals whose conclusions land in one sentence and whose numbers sit in tables. So 밀도 measures how usably someone records, which is close to but not the same as how well they research. Say so.
- **Numbers move when the ontology convention moves.** Card counts shift with `/kalti-ontology`'s rules, so a number from an old run is not comparable to a fresh one. Always recount everyone in one pass, and never quote a figure carried over from an earlier session.

## Where to work — resolve the vault first

As a global plugin this runs **from whatever directory it's called in**, so pin down the vault root first.

1. **Config file**: `. ~/.config/kalti/notes.env 2>/dev/null` reads the `$KALTI_VAULT` that setup wrote. If it holds `journals/` and `ontology/`, use it as `$VAULT`.
2. If missing or empty, try the **default path** `~/dev/lab-notes`.
3. If neither resolves, point the user to `/kalti-setup`.

Members are the folders under `$VAULT/journals/` — do not hardcode names, and do not ask which member to run for. This view is always the whole lab, because a single member's three numbers mean nothing without the others beside them.

## The three numbers

| | what it counts |
|---|---|
| **연구노트** | journals under `journals/<member>/`, read recursively |
| **카드** | how many times those journals were drawn on by cards in `ontology/` |
| **밀도** | 카드 ÷ 연구노트 |

Counting rules, all of them settled deliberately:

- **A card that draws on several journals counts once for each.** On kalti's vault 226 cards cite one journal, 94 cite two or more, and the largest cites sixteen. Being one ingredient among sixteen is still a contribution, and counting it whole keeps the arithmetic to a single division. (Splitting a card into fractions is the alternative; it makes every figure a decimal and buys nothing here, because 318 of 320 cards draw on a single member's journals — there is almost no shared card to apportion.)
- **Project histories are excluded** — `00-프로젝트-히스토리-*.md`, `type: retro`, one per project. They summarize journals already counted, so counting them again counts the same work twice. `/kalti-weekly` excludes them too, for its own reason (no week to file them under); excluding them here keeps the two skills on one basis.
- **Pre-registrations are excluded** — `type: prereg`, named `…-사전등록-….md`. They carry no results; the measurement they precede is counted as its own journal.
- **Frontmatter whitespace is ignored.** Some journals align their frontmatter into columns (`type:      build`). Match `^type:[ \t]*(.+)`, never `^type: (\S+)` — the strict form silently drops those files from the type mix.

## Run the counting script

Do not count by hand or by ad-hoc grep — the numbers must be reproducible run to run.

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kalti-contrib/scripts/count.py" "$VAULT"
```

Pass `$VAULT` as the argument rather than relying on the environment: `. ~/.config/kalti/notes.env` sets the variable in the shell without exporting it, so a child process does not see `$KALTI_VAULT` and the script falls through to its default path.

It prints the finished 요약 block, the per-member fact rows (기간 · 종류 · 프로젝트), and the 참고 lines — **reproduce all of that verbatim**, including the bars. Below a `=== READ` marker it also prints each member's three most-drawn-on journals. That list is working material: open those journals, and **never print it in the report**. Showing which journals scored highest turns a reference view into a scoreboard, which is the thing this skill is built not to be.

## Write the paragraph — the only part you author

For each member, read the three journals the script named. Read the whole file, not the frontmatter. Then write **four to six lines in Korean** covering, in whatever order fits:

- **What shape the work has.** Broad across many projects, or driven into one. The 프로젝트 row supports this and the journals confirm it.
- **Why the numbers came out as they did**, when the type mix explains it. A member whose journals are mostly `build` will run a lower 밀도 than one whose journals are mostly `experiment`, because a build record has less to lift into a card than a measurement record does. That is an explanation, not a demerit — write it as one.
- **What the record shows that no number can.** The most valuable thing to look for is whether the writer caught themselves: re-measured after finding the first measurement wrong, recorded why an approach was dropped, or corrected something they had written earlier. Those passages are what the vault is for, and they are invisible in every column.

Rules for that paragraph:

- **Only claims you read.** Every sentence must trace to one of the three journals you opened. Do not infer from the counts, do not generalize from project names, and do not carry over what you know about the project from elsewhere in the session.
- **Describe, never grade.** "만들기 비중이 높다" is a shape. "기여가 부족하다" is a verdict, and this skill does not issue verdicts. No praise either — "훌륭하다" is the same error facing the other way.
- **A thin record is reported plainly.** A member with twelve journals gets a short paragraph saying the sample is small, not padding.
- **No links.** The journals you read stay out of the output.

## Output shape

Print to screen. Korean throughout. Assemble in this order, with the script's blocks pasted unchanged and your paragraph slotted under each member's fact rows:

```
kalti-contrib · 전체 기간 (…)

── 요약 ───────────────────────────
   (bar table: 연구노트 · 카드 · 밀도, one row per member)
   (the two lines defining 밀도 and disclaiming a total)

── 상세 ───────────────────────────
   <member>
     기간 / 종류 / 프로젝트
     (your paragraph)

── 참고 ───────────────────────────
   (the 밀도-responds-to-habits line and the cross-citation count)
```

Members are ordered by 연구노트 count, descending — the script fixes the order, and it is a sort, not a standing. Do not re-sort by 밀도 to make a point.

## Saving a copy: `--write`

Default is screen only. A document that measures people, sitting in git forever, gets read later in ways nobody intended — so it is written only when asked.

With `--write`, save the same content as markdown to `$VAULT/reports/contrib/YYYYMMDD.md` (`mkdir -p` on demand), dated because it is a snapshot of a moving count. Convert the bars to a plain markdown table; keep everything else as printed.

Then honor `$KALTI_GIT_SYNC` as the other skills do (`push` / `commit` / `ask` / `off`, unset → `ask`) — with one exception: **confirm before committing even in `push` mode.** Every other skill commits the author's own record; this one commits a file about colleagues, and that deserves a deliberate yes. The file is already saved either way; report the outcome in one line.

## What this skill does not do

- **It never writes to `journals/` or `ontology/`.** It reads both and writes, at most, one file under `reports/contrib/`.
- **It does not judge the work, and does not recommend.** No "should write more", no "should refine more". If the counts suggest something worth acting on, that belongs to whoever reads them.
- **It does not fix what it notices.** Malformed frontmatter, an uncited journal, a project with no cards — mention it in a closing line if it affects the counts, and leave the fixing to `/kalti-journal` and `/kalti-ontology`.
