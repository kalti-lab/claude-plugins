---
name: kalti-context
disable-model-invocation: true
description: "Reads the kalti ontology and hands the current session what the lab already knows — before work starts, not after. Invoke with /kalti-context <project> for one project's cards (goal, live hypotheses, findings, and the rejected/superseded paths), /kalti-context <topic> to route through the concept layer into findings from every project that reached the same conclusion, or /kalti-context --check <concept> to use a concept card as a review checklist against the work in hand. Read-only: it never writes to journals/ or ontology/ and runs no git commands. Where kalti-journal and kalti-ontology fill the vault, this is the read side that makes it pay off."
---

# kalti context lookup

The vault has two layers of accumulated knowledge — `journals/` (evidence) and `ontology/` (curated conclusions) — and three skills that write into them. This is the **read** side. Without it the ontology is a filing cabinet nobody opens.

What this skill hands over is **what the codebase and git cannot hold**. `kalti-journal` deliberately keeps file lists, symbol names and commit hashes out of journals, on the grounds that the repo and git already have them. So what is left in the ontology is exactly the complement: which approaches were tried and dropped, why a tuned value is the value it is, and which landmines will silently reappear if someone steps on them again.

## When this is worth calling

Calling it on every task is waste — routine work (fix this bug, add this feature) is answered by reading the repo. It pays off at four specific moments:

| moment | what the lookup supplies |
|---|---|
| **resuming a dormant project** | what was found and decided months ago, and the open next actions |
| **about to try an approach** | whether it was already tried and dropped, with the reason |
| **about to change an experimentally tuned value** | why that value, and what the alternatives cost |
| **starting something new** | findings from *other* projects that already reached a conclusion here |

The last one is the highest-value case and the one nobody can do by memory: a new project's author does not know which of the other 30-odd projects already learned something relevant.

## Where to work — resolve the vault first

As a global plugin this runs **from whatever directory it's called in**, so pin down the vault root (the lab-notes clone) **first**; every path below is absolute under it (`$VAULT`).

1. **Config file**: `. ~/.config/kalti/notes.env 2>/dev/null` reads the `$KALTI_VAULT` that setup wrote. If it contains `journals/`·`ontology/`, use it as `$VAULT`.
2. If missing or empty, try the **default path** `~/dev/lab-notes`.
3. If neither resolves, point the user to `/kalti-setup`.

Prefer the **obsidian CLI** for graph queries when `which obsidian` finds it (`obsidian backlinks`, `obsidian links`, `obsidian properties`); when it is absent, read `$VAULT/ontology/` directly with grep — same answers, more tokens.

## Mode 1 — one project (`/kalti-context <project>`)

For resuming a project, or before touching one you did not write. The project note's filename is the key; every object under it carries `partOf: "[[<project>]]"`.

```
cd "$VAULT"
grep -l 'partOf: "\[\[<project>\]\]"' ontology/*.md
```

Hand over, in this order:

1. **The project note** — its goal paragraph and `status`. This is the one thing that says what the project is *for*.
2. **Live hypotheses** (`status: 제안` / `채택`) — the claims currently standing.
3. **Rejected and superseded hypotheses** (`status: 기각` / `대체됨`) — see "Lead with what was dropped" below.
4. **Findings** — title plus the one-sentence conclusion, which is the first body paragraph of each finding note.
5. **The `## 실험` list** from the project note — journal links, offered as *where to read more*, not pasted in.

A typical project is 5–17 objects, a few KB in total, so the whole set fits. Do not paste journal bodies; the point of the ontology layer is that you do not have to.

## Mode 2 — a topic, across projects (`/kalti-context <topic>`)

For starting something new, where the caller does not know which projects are relevant. **Route through the concept layer** — that is what it is for.

```
cd "$VAULT"
grep -l "^type: concept$" ontology/*.md          # the available concepts
obsidian backlinks file="개념-…" format=json      # findings pointing at one (CLI present)
grep -l 'concept: "\[\[개념-…\]\]"' ontology/*.md  # fallback
```

Two hops, not a scan: topic → the concept card that owns it → the findings from every project that reached that conclusion. Read the concept card's own body first — it says *why* those findings belong together, which the flat list does not.

Do **not** substitute a body-text search across all findings for this. Full-text search on a common word returns most of the vault (on kalti's, "평가" matched 33 objects across 15 projects, roughly half of them unrelated), and tags are worse — two tags cover more than half of all objects. The concept layer exists because neither works.

If no concept card covers the topic, say so plainly rather than forcing a match, and fall back to a targeted body search with the noise flagged. A missing concept is a refinement candidate — mention it, and leave creating it to `/kalti-ontology`.

## Mode 3 — a concept as a checklist (`/kalti-context --check <concept>`)

A concept card that gathers a failure class is a review checklist, and a better one than a generic linter: every item is something this lab actually got caught by, in its own code.

Load the concept card and apply its groupings to the work in hand — the diff, the file, or the design under discussion. Report per group, and say plainly when a group does not apply rather than padding. Each hit should cite the finding it comes from, so the reader can check the original evidence.

The concept card's sub-headings are the checklist structure; they carry the curation (why these belong to one class, and what the distinct forms are). Use them as given — do not re-derive your own categories.

## Lead with what was dropped

Rejected (`기각`) and superseded (`대체됨`) hypotheses are the highest-value part of any lookup, because they are the part with **no trace in the repo**. A dropped approach leaves no code and usually no commit, so an agent reading only the codebase will cheerfully propose it again as if it were new.

So for those two statuses, hand over the **body**, not just the title — the `## 근거` section is where the reason lives, and the reason is the whole value. For live hypotheses and findings, the title plus one-sentence conclusion is enough.

Where a hypothesis was superseded, follow the `supersedes` chain and present it as a sequence, so the reader sees the path rather than a pile: "first X, dropped because …, replaced by Y".

## Output shape

Group by meaning, not by object type. Lead with the project's goal or the concept's explanation, then the standing conclusions, then the dropped paths. Keep each item to a one-line conclusion plus its wikilink, expanding only the dropped ones.

Say explicitly when a project or concept has little to offer — a project with one finding is common and correct, and padding it out with restated titles wastes the caller's attention. State the counts up front (`발견 11 · 가설 4 (기각 1 · 대체됨 2)`) so the caller knows the size of what they are getting.

Write the summary in Korean, the team's working language.

## What this skill does not do

- **It never writes.** No new objects, no edits to existing ones, nothing under `journals/`. Promoting anything is `/kalti-ontology`'s job; recording work is `/kalti-journal`'s.
- **It runs no git commands** — not even a read of history. Nothing here needs syncing.
- **It does not judge the work.** If a lookup shows a project contradicting itself, or a finding that a later journal quietly invalidated, report it as an observation for refinement — do not resolve it here.
