---
name: kalti-ontology
disable-model-invocation: true
description: "Convention for refining kalti research journals into an ontology (knowledge graph). Pulls hypotheses and findings from the entries in journals/ and curates them into ontology/ as 6 object types (project, hypothesis, finding, concept, source, person) with typed links. Invoke with /kalti-ontology to create ontology objects, refine/promote journals, or update the knowledge graph. Where kalti-journal records evidence, this turns that evidence into curated knowledge (managed together by the group). The core discipline: don't create an object without grounding — verify each against a quoted sentence from the source journal."
---

# kalti ontology refinement

## 낱말 — 쓰기 전에 읽는다

**`${CLAUDE_PLUGIN_ROOT}/shared/writing.md`를 따른다.** 한국 사람이 실제 대화에서 쓰는 낱말만 쓰고, 글에서나 보이는 말·번역투·새로 만든 비유는 안 쓴다. 기술 용어는 뜻을 우리말로 먼저 말하고 이름을 괄호에 넣는다. 지적받은 뒤에 고치는 게 아니라 처음 쓸 때부터 그렇게 쓴다. 그 파일에 이 볼트에서 실제로 걸렸던 낱말 표가 있다.

The journal system has two layers.

- **Journal layer `journals/<name>/`** — each member's record of work = **evidence**. Within a member folder, entries are filed under per-project subfolders (`_inbox/` when no project) — so read it recursively.
- **Ontology layer `ontology/`** — the living knowledge refined out of journals, as objects: the meaning nodes that show up in the graph. **Managed by the group together.**

This skill is the **refinement (curation)** side. The core of refinement is promoting into objects only conclusions actually grounded in the journals, without duplication — inventing facts that aren't there breaks trust in the whole graph.

## Where to work — resolve the vault first

Pin down the vault root (the lab-notes clone, where journals and ontology live together) **first**. Every `journals/`·`ontology/` path below is absolute under it (`$VAULT`).

```
. ~/.config/kalti/notes.env 2>/dev/null; VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"
```

If that directory has no `journals/`·`ontology/`, follow **`${CLAUDE_PLUGIN_ROOT}/shared/vault-and-git.md`** rather than guessing. That file also carries the rule this skill leans on hardest: **both layers are nested, so a flat glob returns a partial answer with no error.** Read them with `grep -ar … --include='*.md'`, `find`, or `os.walk` — never `ontology/*.md`.

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
| `decision` | a choice that was made, why, and what it ruled out |

## status (per type)

Status values are written into the notes in Korean (the team's working language):

- **project**: `진행` / `보류` / `완료` / `보관` (active / on-hold / done / archived)
- **hypothesis**: `제안` / `채택` / `기각` / `대체됨` (proposed / accepted / rejected / superseded)
- **decision**: `유효` / `번복됨` (standing / reversed)
- **finding · concept · source · person**: no status

### Nothing is deleted, only superseded

The history *is* the research narrative, so a card that stopped being true is never removed. What
changes is its status and what points at it. Each type ages differently:

**hypothesis** — replaced by a newer claim: old one goes `대체됨`, the new one points back with
`supersedes`. Measured and found false: `기각`, and the finding that killed it points at it with
`refutes`. Either way the *reason* must be reachable from the card. A dropped hypothesis with no
successor and no refuting finding is the exact condition that lets a dead premise come back to
work — this lab was caught by it once, a discarded measurement approach turning up ten days later
as the justification for the next move. The weekly reports that count and it should stay at zero.

**decision** — reversed: old one goes `번복됨`, the new decision points back with `supersedes`,
and *why it was reversed* goes in the new decision's 왜. A decision is never `기각` — it was not
wrong, it was replaced. When only part of a decision is overturned, leave the status `유효` and add
a **## 어떻게 뒤집혔나** section naming what fell and what still stands; forcing the whole card to
`번복됨` throws away the part that is still load-bearing.

**finding** — has no status, because a conclusion does not expire; it gets narrowed. A later
result that contradicts it is itself a finding, and the two are joined by the concept they share
or by the hypothesis they both touch. If a finding turns out to be plainly wrong, the honest fix
is to rewrite its body saying what the earlier reading missed and why — the card keeps its name
and its citations, so anyone who followed a link still lands somewhere that explains itself.

**project** — `보류` means someone decided to stop; it is not what happens when a project simply
goes quiet. Dormancy is not a status. Set it only when a journal says so.

## id convention

`type-abbrev + slug` (no date or sequence — an id is a fixed marker and shouldn't shift): `proj-` / `hyp-` / `find-` / `con-` / `src-` / `per-`
e.g. `proj-image-pipeline`, `hyp-sampler`, `find-karras`, `con-nodes2`, `src-nodes2-doc`, `per-aram`

**Link by filename (not id).** id is just a fixed marker inside frontmatter; wikilinks `[[ ]]` use the note's filename. Every name in the vault is bare — cards and journals alike — so `derivedFrom: "[[샘플러별-디테일-비교]]"` is the whole form. Nothing in a link's shape tells you what it points at; only the file's actual location does. **Project overview notes** (`"[[00-프로젝트-히스토리-agrune]]"`) are worth citing alongside dated work: they hold the across-the-months reasoning — why a line was abandoned, what a pivot cost — that no single entry contains.

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
| `partOf` | belongs to | decision | project |
| `supersedes` | reverses | decision | decision |
| `basedOn` | rests on | decision | finding, hypothesis |
| `derivedFrom` | recorded in | decision | journal |

## Required fields per type

Every card also carries **`updated`** (`YYYY-MM-DD`) — set it on creation and on every edit.
A card is a living document; without it a reader cannot tell a settled conclusion from a stale one.

| type | required (besides `updated`) |
|---|---|
| project | id, title, type, status, tags |
| hypothesis | id, title, type, status, partOf (supersedes when replacing) |
| finding | id, title, type, date, partOf, derivedFrom, (supports / refutes) |
| concept | id, title, type, tags |
| decision | id, title, type, status, date, partOf, derivedFrom (supersedes when reversing) |
| source | id, title, type, url |
| person | id, title, type, name, role, worksOn (a list) — **never a contact address** |

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

A journal with no incoming link is **not automatically remaining work**. Most journals record what was built, renamed, deployed or set up, and honestly yield nothing to promote — reading one and finding nothing is a correct, common outcome, not a failure. If the cursor counts those forever it never reaches zero and stops meaning anything.

So a run that reads a journal and finds nothing records that fact in `reports/정제/검토기록.md`, and the cursor subtracts it. Never edit the journal itself to mark it — journals are evidence and belong to their author; the record layer is where operational state goes.

```
# journals neither cited by ontology/ nor already reviewed
cd "$VAULT"
# 일지의 이름 집합. prereg는 type 칸으로 뺀다 — 파일 이름으로 거르면 제목에 "사전등록"이
# 들어간 experiment 일지가 조용히 빠진다(볼트에 실제로 한 편 있었다).
# 00-프로젝트-히스토리는 다른 일지를 요약한 회고라 정제 대상이 아니다
# (주간·기여도 같은 이유로 건너뛴다). 세면 영원히 미정제로 남는다.
grep -arL '^type: prereg$' journals/ --include='*.md' | sed 's|.*/||; s|\.md$||' \
  | grep -v '^00-' | sort -u > /tmp/journals
# 온톨로지가 가리키는 것 중 실제로 일지인 것 = 정제된 일지
grep -aroh '\[\[[^]|#^]*' ontology/ --include='*.md' | sed 's/\[\[//; s/[[:space:]]*$//' | sort -u > /tmp/linked
comm -12 /tmp/journals /tmp/linked > /tmp/cited
grep -oh '^- [^ ]*' reports/정제/검토기록.md 2>/dev/null | sed 's/^- //' | sort -u > /tmp/checked
cat /tmp/cited /tmp/checked | sort -u | comm -23 /tmp/journals -
```

Append to the record under a dated heading, in three groups, and say in one line per entry why nothing came out: **뽑을 결론 없음** (nothing to promote), **결론은 있으나 보류** (a conclusion exists but no single project owns it, so `partOf` cannot be chosen), **링크를 걸 수 없음** (the filename collides with others, so no wikilink can address it). The second and third are held work, not finished work — keep them visible.

**Pre-registrations are excluded from the cursor — by their `type`, never by their filename.** A journal titled "…사전등록 재실험…" is an `experiment` whose subject is a pre-registration, and a name filter drops it silently; that is a real entry in this vault. A `type: prereg` entry states what will count as correct *before* a measurement; it holds no conclusion to promote, so counting it would keep the backlog above zero forever. Its findings arrive in the `experiment` journal that follows it.

The cursor never guesses a link's kind from its shape. A journal name carries no reserved pattern — nothing in `[[샘플러별-디테일-비교]]` says "journal" rather than "card" — so the only correct test is membership in the set of files actually under `journals/`. Both resolve by **filename**, the way a wikilink does. If two journals share a basename, no link can tell them apart — fix that on the journal side first (`shared/lint.py` reports the collision and `kalti-journal` disambiguates by appending the project), then refine them.

### Project objects come first

`hypothesis` and `finding` both **require** `partOf: "[[<project note>]]"`. So the project object has to exist before any of them can be created — otherwise a required field points at nothing and the graph fills with broken links. Journals already carry the answer in their `project:` frontmatter.

```
grep -h "^project:" <the scoped journals> | sort -u     # projects these journals name
find "$VAULT/ontology" -name '*.md'                     # which already have an object
```

For each project with no object, create it from the `project` block in `references/object-templates.md`. Take the goal paragraph and `status` from the journals themselves — read enough of them to say what the project is after, and don't invent a goal they don't state. Leave `## 현재 가설`·`## 실험`·`## 발견` empty for now; they fill in as this run produces objects. `## 참여` takes the `person` note of whoever wrote the journals.

A `person` object's `worksOn` points at project notes too, so people are easiest to create or update **after** their projects exist.

### Reusable refinement prompt

To extract journal → ontology candidates, instruct the AI (a subagent, etc.) like this:

```
Read the journals in the scope given below, and the existing objects in ontology/.
Scope: <one project folder, e.g. $VAULT/journals/aram/이미지생성-파이프라인/>
These journals hold conclusions, live claims and choices that have not yet been
promoted to an object. Propose them as candidates, one of three kinds:
  finding    — a conclusion the journal states as settled, with evidence behind it
  hypothesis — a claim still being tested, or one the journal records as dropped
  decision   — a choice that was made. Not true-or-false, chosen. What was ruled out?
- Exclude anything already in the ontology; propose only new ones.
- For each candidate, quote the source journal sentence verbatim (groundingQuote),
  and point at that journal with derivedFrom.
- Write only conclusions actually stated in the journal — promote only what a verbatim quote supports.
Then verify each candidate is genuinely grounded in that journal and isn't a duplicate; keep only those that pass.
```

**One journal can yield more than one kind, and that is not duplication.** A pivot entry usually
carries both — the testable claim becomes a `hypothesis`, and the choice with its cost becomes a
`decision`. Measured on this vault: of 18 `decision` journals, 14 were already cited by a hypothesis
or finding, and every one of them still had an unrecorded *what we gave up instead*.

Which kind is it? The journal's own `type` is a hint, not the answer — a `build` entry often
carries a decision, and an `experiment` often carries both a finding and a superseded hypothesis.
Ask instead:

| The sentence says… | kind |
|---|---|
| this is so, and here is what showed it | `finding` |
| this may be so; we are measuring / we measured and dropped it | `hypothesis` |
| we are going this way, and not that way | `decision` |
| nothing that survives outside the run — a step, a version bump, a rename | none, record it in the review log |

Create only the candidates that pass, as files in the matching `ontology/<종류>/` folder (using the blocks in `references/object-templates.md`).

### When a new concept is warranted

A `concept` is not written from one journal. It is found by laying findings side by side, so it
comes **after** the findings exist, not during their extraction.

The bar is **three or more different projects saying the same thing.** Three findings inside one
project is that project's conclusion, not a concept — the whole job of this layer is crossing
project boundaries, and a hub that spans one project crosses nothing.

Two more tests before creating one:

- **Does it tell the reader to do something differently?** Every existing concept carries a rule
  you can act on. If all that survives is "be careful", it is general advice, not something this
  lab found out. Leave it; when more cases arrive and a shared mechanism gets sharper, make it then.
- **Is the name narrow enough to keep things out?** A name broad enough to admit anything will
  admit everything, and a hub carrying a hundred findings tells you nothing when you open it.

Concepts are cheap to add later and awkward to untangle once written. When unsure, don't.

A concept card that is only a glossary entry — a term explained, not a hub joining projects —
takes `role: glossary` and drops out of the concept count and the drift check.

### Check the graph before committing

```
python3 "${CLAUDE_PLUGIN_ROOT}/shared/lint.py" "$VAULT" --ontology
```

**오류** are graph breakage: a `type` outside the six, a missing required field, a name prefix that
disagrees with its `type`, a duplicate `id`, and above all **a typed link pointing at a note that
does not exist** — the one mistake refinement makes most often, because a card is written before
the note it cites. Fix them before the commit; a broken link is invisible until someone follows it.

**경고** are the refinement backlog rather than defects: a `finding` with no `concept` (it can only
be found from inside its own project), and an orphan card nobody points at. Work them down over
time; do not let them block a run.

## After applying: sync with git

The ontology is **shared knowledge managed by the group**, so changes should reach everyone else's graph. The four modes (`push` / `commit` / `ask` / `off`, unset = `ask`) and the failure handling are in **`${CLAUDE_PLUGIN_ROOT}/shared/vault-and-git.md`** — read it before running git. This skill's scope and message:

```
cd "$VAULT"
git add "ontology/"                  # the ontology layer only — never -A
git commit -m "ontology: <one line on what was refined/added>"
```

A run that also appended to `reports/정제/검토기록.md` adds that file too. Put the sync result in the summary in one line.

## Why two layers

Journals are evidence, the ontology is knowledge. Splitting them means: writing only a journal is already a contribution (low burden), refined knowledge can be trusted, and the graph lets you pull exactly the related pieces via links — so the context handed to an AI is small and accurate.

## Sources (basis for the human-facing guide)

- NIH — Best Practices for Keeping a Lab Notebook (2024)
- Harvard Medical School — Electronic Lab Notebooks
- UCSF McManus Lab — Notebook Guidelines
