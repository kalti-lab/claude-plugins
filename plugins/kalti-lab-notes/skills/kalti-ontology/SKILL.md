---
name: kalti-ontology
disable-model-invocation: true
description: "Convention for refining kalti research journals into an ontology (knowledge graph). Pulls hypotheses and findings from the entries in journals/ and curates them into ontology/ as 6 object types (project, hypothesis, finding, concept, source, person) with typed links. Invoke with /kalti-ontology to create ontology objects, refine/promote journals, or update the knowledge graph. Where kalti-journal records evidence, this turns that evidence into curated knowledge (managed together by the group). The core discipline: don't create an object without grounding — verify each against a quoted sentence from the source journal."
---

# kalti ontology refinement

The journal system has two layers.

- **Journal layer `journals/<name>/`** — each member's record of work = **evidence**. Within a member folder, entries are filed under per-project subfolders (`_inbox/` when no project), with `YYYYMMDD-`prefixed filenames — so read it recursively.
- **Ontology layer `ontology/`** — the living knowledge refined out of journals, as objects: the meaning nodes that show up in the graph. **Managed by the group together.**

This skill is the **refinement (curation)** side. The core of refinement is promoting into objects only conclusions actually grounded in the journals, without duplication — inventing facts that aren't there breaks trust in the whole graph.

## Where to work — resolve the vault first

As a global plugin this runs **from whatever directory it's called in**, so pin down the vault root (the lab-notes clone, where journals and ontology live together) **first**. The `journals/`·`ontology/` paths below are all absolute under this root (`$VAULT`). Order:

1. **Config file**: `. ~/.config/kalti/notes.env 2>/dev/null` reads the `$KALTI_VAULT` that setup wrote. If it contains `journals/`·`ontology/`, use it as `$VAULT`.
2. If the file is missing or the value is empty, try the **default path** `~/dev/lab-notes`.
3. If neither, point the user to run `/kalti-setup` first — it pins the vault into `~/.config/kalti/notes.env`.

(`ontology/` lives in the lab-notes vault alongside `journals/` — cloning gets both.)

## Query and verify the graph via the `obsidian` CLI

The ontology is a typed-link graph. Questions like "which findings support this hypothesis", "what's orphaned", "which wikilinks are broken" are inaccurate to scrape with grep (it misses aliases, embeds, heading refs) and burn tokens. The **official Obsidian CLI** asks the link index the app already built, giving an accurate, compact answer in one call. **Prefer it for queries and verification.** (Object *creation* is done by direct file write, not the CLI — see "Refinement".)

Prerequisites: Obsidian must be running (if closed, the first command launches it), and run **inside the vault directory** or pass `vault=<name>`. If `which obsidian` finds nothing (headless, etc.), skip the CLI and read `$VAULT/ontology/`·`$VAULT/journals/` files directly to do the same (graceful fallback).

`file=` resolves by **name** (like a wikilink), `path=` by exact path. The default output format varies per command, so add **`format=json`** when parsing.

| want | command |
|---|---|
| list objects | `obsidian files folder=ontology` |
| things **pointing at** this note (supports, derivedFrom, etc. — reverse) | `obsidian backlinks file="가설-..." counts format=json` |
| things this note **points to** (forward) | `obsidian links file="발견-..."` |
| read frontmatter (status, partOf, supersedes…) | `obsidian properties file="가설-..." format=json` |
| **broken wikilinks** (objects not yet created) | `obsidian unresolved verbose` |
| **orphans** (no incoming links) / **dead ends** (no outgoing links) | `obsidian orphans` / `obsidian deadends` |
| body search | `obsidian search query="..." format=json limit=10` (line context via `search:context`) |
| tag distribution | `obsidian tags sort=count counts` |
| read body | `obsidian read file="..."` |

Especially useful in refinement: `unresolved` shows what journals link to but has no object yet, `orphans` shows what was created but nobody links to, `backlinks` shows whether an object already exists (a duplicate). Candidate discovery and duplicate checks are exactly these commands.

(With the kepano `obsidian-skills` plugin installed, the model can handle broader Obsidian work too — install via `/kalti-setup`. The table above is enough for the core graph commands.)

## Object types (6)

| type | meaning |
|---|---|
| `project` | a large research topic |
| `hypothesis` | a claim under test |
| `finding` | a conclusion confirmed by experiment/investigation |
| `concept` | a recurring term or technique |
| `source` | a paper, doc, or link |
| `person` | a participant |

## status (per type)

Status values are written into the notes in Korean (the team's working language):

- **project**: `진행` / `보류` / `완료` / `보관` (active / on-hold / done / archived)
- **hypothesis**: `제안` / `채택` / `기각` / `대체됨` (proposed / accepted / rejected / superseded)
- **finding · concept · source · person**: no status

Hypotheses are alive. When a new hypothesis replaces an old one, set the old one's status to `대체됨` and have the new one point at the old one with `supersedes` (don't delete — the history is the research narrative).

## id convention

`type-abbrev + slug` (no date or sequence — an id is a fixed marker and shouldn't shift): `proj-` / `hyp-` / `find-` / `con-` / `src-` / `per-`
e.g. `proj-image-pipeline`, `hyp-sampler`, `find-karras`, `con-nodes2`, `src-nodes2-doc`, `per-aram`

**Link by filename (not id).** id is just a fixed marker inside frontmatter; wikilinks `[[ ]]` use the note's filename. Ontology object names are bare (no date), but **journal** filenames carry a `YYYYMMDD-` prefix, so links *to a journal* — `tests` and especially `derivedFrom` — include it: `derivedFrom: "[[20260615-샘플러별-디테일-비교]]"`, not `"[[샘플러별-디테일-비교]]"`.

## Relationship links (typed)

Write each direction once, and read the reverse via Obsidian backlinks (avoids common-hub boilerplate).

| key | meaning | on which note (from) | points to (to) |
|---|---|---|---|
| `project` | belongs to | journal | project |
| `partOf` | belongs to | hypothesis, finding | project |
| `tests` | tests | experiment journal | hypothesis |
| `supersedes` | replaces | hypothesis | hypothesis |
| `supports` / `refutes` | supports / refutes | finding | hypothesis |
| `derivedFrom` | derived from | finding | experiment journal |
| `concept` | is an instance of | finding, hypothesis | concept |
| `worksOn` | works on | person | project |

## Required fields per type

| type | required |
|---|---|
| project | id, title, type, status, tags |
| hypothesis | id, title, type, status, partOf (supersedes when replacing) |
| finding | id, title, type, date, partOf, derivedFrom, (supports / refutes) |
| concept | id, title, type, tags |
| source | id, title, type, url |
| person | id, title, type, worksOn |

## Body shape per type (summary)

Section headings are written in Korean in the notes:

- **project**: one paragraph of goal + `## 현재 가설` + `## 실험` + `## 발견` + `## 참여`
- **hypothesis**: one-sentence hypothesis + `## 상태` (value and date) + `## 근거`
- **finding**: one-sentence conclusion + a mechanism/grounds paragraph
- **concept**: the concept in 3–5 plain sentences, then the curation — see below

### The concept layer is the cross-project index

`partOf` files an object under one project, so a graph built only from it is a set of islands: to find what *another* project already concluded about your topic you would have to know which project to look in. The `concept` link is the only edge that crosses those boundaries, and a concept card is the hub it points at.

So a concept card carries two things. The **prose** (3–5 sentences) says what the term is and why it matters here. Below it, a **curated grouping** names the distinct forms the concept takes and cites a finding for each — that grouping is the knowledge no single finding holds, and it is what makes the card usable as a review checklist.

**The authoritative membership list is the backlinks, not the card.** Each finding or hypothesis declares its own `concept:`, so nothing can be silently missing; read the full set with `obsidian backlinks file="개념-…"`. Never regenerate a concept card's body from that list — the grouping is hand-curated and a machine rewrite destroys it. Instead, when refining, check for **drift**: members that point at the card but are not mentioned in it, and add the ones worth naming.

A concept may legitimately sit inside one project (a tool-specific term), but a concept that never gains a second project is a glossary entry, not an index — worth keeping, not worth curating.
- **source**: what · URL · use to our research
- **person**: one-line intro + `## 주로 보는 것`

The full frontmatter+body block to copy when actually creating each object is in **`references/object-templates.md`**. Read that file right before creating an object and use the block for that type verbatim.

## Refinement (curation) — the heart of the system

Promoting journals into the ontology. **Anyone** can do it — the person who wrote a journal can promote it straight to objects, or it can be done in periodic batches. With no forced gate, **discipline keeps quality**: only what's grounded, no duplicates, revise rather than delete.

1. **Scope one run**: pick the journals this run covers — one project folder, not the whole backlog (see below).
2. **Project objects first**: every project those journals belong to must already have a `project` object (see below).
3. **AI refinement**: have the AI extract hypothesis/finding candidates not yet in the ontology, plus their links, from the scoped journals (prompt below).
4. **Apply**: check each candidate is grounded in an actual journal and isn't a duplicate, then apply to `ontology/`. Discard the ungrounded.
5. **Cadence**: nothing fixed, but a weekly batch (alongside the weekly report) catches everything.

### Scope one run — never the whole backlog at once

The prompt below reads journals in full, so one run has to fit in one context. Scope it by **project folder** — the unit the ontology is already organized by (`partOf`):

```
$VAULT/journals/<author>/<project>/
```

A member folder, let alone all of `journals/`, stops fitting as soon as a backlog builds up — a vault three months in can hold well over 1.5MB of journals, and a run that exhausts its context part-way leaves the ontology half-applied. **One project per run, committed on its own**, is the safe unit; several small projects can share a run if their journals together stay in the same range.

**Which journals are still unrefined** — a refined journal is one that some object in `ontology/` links to, so a journal with **no incoming link from `ontology/`** is remaining work. Those incoming links *are* the progress cursor; nothing else needs tracking.

Count **every** link from `ontology/`, not just `derivedFrom`. Only `finding` carries a `derivedFrom` field; a `hypothesis` cites its source journal in its `## 근거` body and a `project` lists journals under `## 실험`, both as plain wikilinks. Refinement never edits journals either, so it can never add the journal-side `tests` link. Counting `derivedFrom` alone therefore reports journals you have **already fully refined** as untouched — measured on kalti's vault, it mis-flagged 78 of 264 journals, and a run that promoted only hypotheses from a journal left it looking unrefined forever.

```
obsidian backlinks file="<journal name>" format=json    # no ontology/ backlink = not yet refined
```

```
# fallback with no CLI — journals that no ontology object links to
cd "$VAULT"
grep -oh '\[\[[0-9]\{8\}-[^]|#^]*' ontology/*.md | sed 's/\[\[//' | sort -u > /tmp/cited
find journals -name '*.md' | sed 's|.*/||; s|\.md$||' | sort -u | comm -23 - /tmp/cited
```

Both resolve by **filename**, the way a wikilink does. If two journals share a basename, no link can tell them apart — fix that on the journal side first (the `kalti-journal` tidy routine gives every entry a `YYYYMMDD-` prefix), then refine them.

### Project objects come first

`hypothesis` and `finding` both **require** `partOf: "[[<project note>]]"`. So the project object has to exist before any of them can be created — otherwise a required field points at nothing and the graph fills with broken links. Journals already carry the answer in their `project:` frontmatter.

```
grep -h "^project:" <the scoped journals> | sort -u     # projects these journals name
ls "$VAULT/ontology/"                                   # which already have an object
```

For each project with no object, create it from the `project` block in `references/object-templates.md`. Take the goal paragraph and `status` from the journals themselves — read enough of them to say what the project is after, and don't invent a goal they don't state. Leave `## 현재 가설`·`## 실험`·`## 발견` empty for now; they fill in as this run produces objects. `## 참여` takes the `person` note of whoever wrote the journals.

A `person` object's `worksOn` points at project notes too, so people are easiest to create or update **after** their projects exist.

### Reusable refinement prompt

To extract journal → ontology candidates, instruct the AI (a subagent, etc.) like this:

```
Read the journals in the scope given below, and the existing objects in ontology/.
Scope: <one project folder, e.g. $VAULT/journals/aram/이미지생성-파이프라인/>
Journals contain conclusions and insights that haven't yet been promoted to a
'finding' or 'hypothesis' object — find those and propose them as candidates.
- Exclude anything already in the ontology; propose only new ones.
- For each candidate, quote the source journal sentence verbatim (groundingQuote),
  and point at that journal with derivedFrom.
- Write only conclusions actually stated in the journal — promote only what a verbatim quote supports.
Then verify each candidate is genuinely grounded in that journal and isn't a duplicate; keep only those that pass.
```

Create only the candidates that pass, as files in `ontology/` (using the blocks in `references/object-templates.md`).

## After applying: sync with git

The ontology is **shared knowledge managed by the group**, so changes should reach everyone else's graph (`ontology/` is in the same lab-notes repo). How far to go is the user's preference in `KALTI_GIT_SYNC` (from the `notes.env` already sourced when resolving the vault; unset = `ask`) — same modes as the journal skill: `push` (commit + push), `commit` (commit only), `ask` (ask via AskUserQuestion: push now / commit only / skip), `off` (don't run git). Scope the add to `ontology/`:

```
cd "$VAULT"
git add "ontology/"
git commit -m "ontology: <one line on what was refined/added>"
git pull --rebase --autostash        # integrate others' pushes first
git push                             # only in push mode, or when the user chose push in ask mode
```

Handle no-remote / blocked-push / rebase-conflict the same as the journal side — the files are already saved; push again once access (SSH key/token) is set; and for conflicts don't auto-merge — `git rebase --abort` and tell the user. Put the sync result in the summary in one line.

## Why two layers

Journals are evidence, the ontology is knowledge. Splitting them means: writing only a journal is already a contribution (low burden), refined knowledge can be trusted, and the graph lets you pull exactly the related pieces via links — so the context handed to an AI is small and accurate.

## Sources (basis for the human-facing guide)

- NIH — Best Practices for Keeping a Lab Notebook (2024)
- Harvard Medical School — Electronic Lab Notebooks
- UCSF McManus Lab — Notebook Guidelines
