---
name: kalti-context
description: "Reads the kalti lab's ontology and hands back what the lab already knows about something — the goal, the live hypotheses, the findings, and above all the approaches already tried and dropped, which leave no trace in any repo. Trigger it when the user's own words point at the lab's notes — 연구노트, 일지, 온톨로지, 볼트, 연구실, kalti, lab-notes — or when the session is working inside the lab-notes vault itself, and they are asking what is known, what was decided, or what was already tried. Also invoked directly as /kalti-context followed by a project name, a topic, a concept, or a question in plain words. It cannot tell from a bare project name whether that project belongs to the lab, so it does not guess: with no such cue, a lookup is the user's to ask for. Read-only — it never writes to journals/ or ontology/ and runs no git commands."
---

# kalti context lookup

The vault has two layers of accumulated knowledge — `journals/` (evidence) and `ontology/` (curated conclusions) — and three skills that write into them. This is the **read** side. Without it the ontology is a filing cabinet nobody opens.

What this hands over is **what the codebase and git cannot hold**. `kalti-journal` deliberately keeps file lists, symbol names and commit hashes out of journals, on the grounds that the repo and git already have them. So what is left in the ontology is exactly the complement: which approaches were tried and dropped, why a tuned value is the value it is, and which landmines will silently reappear if someone steps on them again.

## When this is worth calling

Calling it on every task is waste — routine work (fix this bug, add this feature) is answered by reading the repo. It pays off at four moments:

| moment | what the lookup supplies |
|---|---|
| **resuming a dormant project** | what was found and decided months ago, and the open next actions |
| **about to try an approach** | whether it was already tried and dropped, with the reason |
| **about to change an experimentally tuned value** | why that value, and what the alternatives cost |
| **starting something new** | findings from *other* projects that already reached a conclusion here |

The last one is the highest-value case and the one nobody can do from memory: a new project's author does not know which of the other thirty-odd projects already learned something relevant.

## Where to work — resolve the vault first

Pin down the vault root (the lab-notes clone) **first**; every path below is absolute under it (`$VAULT`).

```
. ~/.config/kalti/notes.env 2>/dev/null; VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"
```

If that directory has no `ontology/`, follow **`${CLAUDE_PLUGIN_ROOT}/shared/vault-and-git.md`** instead of guessing. That file also states the reading rule this skill depends on: **both layers are nested, so never use a flat glob.** `ontology/` holds one folder per object type — `종목` · `개념` · `사람` · `자료` · `가설` · `발견` — and the folder, not a name prefix, is what says the type.

Prefer the **obsidian CLI** for graph queries when `which obsidian` finds it (`obsidian backlinks`, `obsidian links`, `obsidian properties`); when it is absent, read `$VAULT/ontology/` directly with grep — same answers, more tokens.

## The input is free text — resolve it, don't make the caller pick

There are no modes and no flags. Whatever follows `/kalti-context` is what the caller wants to know about, written however they write. Work out what it refers to, in this order:

1. **It names a project** (matches a `project` note's filename, or is close to one) → pull everything filed under it: `grep -arl 'partOf: "[[<project>]]"' ontology/ --include='*.md'`
2. **It names a concept** (matches a `concept` note) → that card plus its full membership: `obsidian backlinks file="<concept>"`, or `grep -arl 'concept: "[[개념-…]]"' ontology/ --include='*.md'` as fallback. The card's own body says *why* those findings belong together, which the flat list does not — read it first.
3. **It is a topic or a question** → route through the **concept layer**, which is the only edge that crosses project boundaries. List the concepts (`grep -arl "^type: concept$" ontology/ --include='*.md'`), pick the ones that cover the topic, then follow their membership out into findings from every project that reached that conclusion. Two hops, not a scan.
4. **Nothing covers it** → say so plainly rather than forcing a match, then fall back to a targeted body search with the noise flagged. A missing concept is a refinement candidate: mention it and leave creating it to `/kalti-ontology`.

When the input is ambiguous between a project and a topic, do both and label which is which — it is cheaper than asking.

**Do not substitute a body-text search for step 3.** Full-text search on a common word returns most of the vault (measured on kalti's: `평가` matched 33 objects across 15 projects, roughly half unrelated), and tags are worse — two tags cover more than half of all objects. The concept layer exists because neither works.

## What to hand over

Lead with the thing that says what something is *for* — a project's goal paragraph and `status`, or a concept card's prose. Then:

- **Live hypotheses** (`status: 제안` / `채택`) — the claims currently standing.
- **Rejected and superseded hypotheses** (`status: 기각` / `대체됨`) — see below.
- **Findings** — title plus the one-sentence conclusion, which is the first body paragraph of each finding note.
- **The `## 실험` list** from a project note — journal links, offered as *where to read more*, not pasted in.

A typical project is 5–17 objects, a few KB in all, so the whole set fits. Never paste journal bodies; the point of the ontology layer is that you do not have to.

A concept card that gathers a failure class doubles as a code-review checklist — use its form-by-form groupings as given and don't re-derive your own, since that grouping is the curated part.

## Lead with what was dropped

Rejected (`기각`) and superseded (`대체됨`) hypotheses are the highest-value part of any lookup, because they are the part with **no trace in the repo**. A dropped approach leaves no code and usually no commit, so an agent reading only the codebase will cheerfully propose it again as if it were new.

So for those two statuses hand over the **body**, not just the title — the `## 근거` section is where the reason lives, and the reason is the whole value. For live hypotheses and findings the title plus one-sentence conclusion is enough.

Strip the frontmatter with this exact form. A naive `sed '1,/^---$/d'` looks right and **silently eats the body too**, because the opening `---` is line 1 and the range then runs to the *second* delimiter; chaining two of them deletes everything.

```
# $CARD is the resolved path — each object type lives in its own ontology/<종류>/ folder
awk '/^---$/{n++;next} n>=2' "$CARD"                        # whole body
awk '/^---$/{n++;next} n==2 && NF && !/^#/ {print; exit}' "$CARD"   # first paragraph only
```

Where a hypothesis was superseded, follow the `supersedes` chain and present it as a sequence so the reader sees the path rather than a pile: "first X, dropped because …, replaced by Y". **Scope that search to the project**, not the whole vault — every chain is local to one project, so a vault-wide grep hands back every chain in the lab (20-odd on kalti's) for you to filter by hand:

```
grep -arl 'partOf: "[[<project>]]"' ontology/가설/ --include='*.md' | xargs grep -ah "^supersedes:"
```

## Output shape

Group by meaning, not by object type. Keep each item to a one-line conclusion plus its wikilink, expanding only the dropped ones. State the counts up front (`발견 11 · 가설 4 (기각 1 · 대체됨 2)`) so the caller knows the size of what they are getting.

Say explicitly when something has little to offer — a project with one finding is common and correct, and padding it out with restated titles wastes the caller's attention. Write the summary in Korean, the team's working language.

## What this skill does not do

- **It never writes.** No new objects, no edits to existing ones, nothing under `journals/`. Promoting anything is `/kalti-ontology`'s job; recording work is `/kalti-journal`'s.
- **It runs no git commands** — not even a read of history. Nothing here needs syncing.
- **It does not judge the work.** If a lookup shows a project contradicting itself, or a finding a later journal quietly invalidated, report it as an observation for refinement — do not resolve it here.
