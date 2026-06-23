---
name: kalti-journal
disable-model-invocation: true
description: "Convention for writing and editing kalti research-group lab notes. Writes a journal entry into the lab-notes vault at journals/<author>/ as a titled file, following the fixed 7-field frontmatter (id, title, date, author, type, tags, project) and the prescribed 7 body sections and 5 principles. Global plugin — invoke with /kalti-journal from any working directory — to write or edit experiment / investigation / build / reading / meeting / decision / retro entries. Don't infer the format by digging through the vault; follow this skill's schema. (Creating or refining ontology objects belongs to the kalti-ontology skill, not this one.)"
---

# Writing kalti research journals

kalti is a research group. Members record what they did as **research journals**, and the operator collects those entries and refines them into knowledge (the ontology). This skill is the convention for the **writing** side.

Members only need to write journals — weaving hypotheses and findings into the knowledge graph is the operator's job. So focus on capturing what was done well enough that someone could reproduce it exactly from the note alone, even without you. The format isn't about tidiness: entries get read mechanically during refinement and linked into the vault graph, so the fields have to be where the refinement step expects them.

## When to write, and what to base it on

This skill is usually invoked manually (`/kalti-journal`) right after one sizable piece of work, not at the very end of everything. That work usually happens in an actual research folder (code, experiment environment), not in the vault — which is why this is a global plugin callable from anywhere. The primary source for an entry is **what actually just happened in this session**. When the session does contain such work, don't wait for the user to re-explain it — pull it from the conversation and work context directly (when there's nothing, use the gate below):

- the commands/code actually run and their output/results
- errors hit and how they were resolved — not just successes, but dead ends and things rolled back (e.g. a setting tried and removed)
- values, versions, paths, and settings **as seen** — rounding them from memory breaks later reproduction
- decisions made and why

If the user gives a separate explanation in the prompt, prefer that; otherwise reconstruct from session context.

### Nothing to write about — stop and ask first

A journal is **evidence**: only a record of work actually done lets the later graph and refinement be trusted. So write only when this session has real work to record. If the session is empty, or the recent conversation isn't journal material, stop and ask before writing — ask the user what work to record this time, with what they did, the commands run, and the results — and write only after getting an answer.

It's tempting to read other journals in `journals/` (especially other people's folders) and spin a plausible entry from them, but that's fiction, not evidence, and it breaks trust in the whole system. Reading existing journals is useful in exactly two cases: (1) **finding** a candidate file to continue (metadata only — title, `project`, date), and (2) format reference (`assets/journal-template.md`, `references/example-experiment.md`). Neither copies *content*.

When the basis is in the session or the user's explanation, write only that. For metadata that's genuinely missing (which `project`, the hypothesis note tested, the `author` name), ask once briefly rather than filling it by inference.

## Where to write — resolve the vault and author folder first

This skill is installed globally and runs **from whatever directory it's called in**, so pin down where the entry goes — the lab-notes vault (clone) root (`$VAULT`) and the author folder (`$AUTHOR`) — **first**. Writing to a path relative to the working directory (`journals/...`) would drop the file in the wrong place. Order:

1. **Config file**: `. ~/.config/kalti/notes.env 2>/dev/null` loads the `$KALTI_VAULT`/`$KALTI_AUTHOR` that setup wrote. If `$KALTI_VAULT` contains `journals/`, use it as `$VAULT`; if `$VAULT/journals/$KALTI_AUTHOR/` exists, use it as `$AUTHOR`.
2. If the file is missing or the values are empty, try the **default path** `~/dev/lab-notes` as `$VAULT` (if it has `journals/`). Don't guess the author folder — a typo carves out a stray new folder (`journals/Aram/`) — instead list the **existing folders** in `$VAULT/journals/` and let the user pick (AskUserQuestion). For a new member, take a folder name via "Other (type it in)" (lowercase latin recommended) and `mkdir -p`.
3. If neither resolves, point the user to run `/kalti-setup` once — it pins the vault and author folder into `~/.config/kalti/notes.env` so there are no more questions next time.

From there **every path is absolute under `$VAULT`** — write the entry by **direct file write** into the author folder `$VAULT/journals/$AUTHOR/` (independent of the Obsidian app, headless OK), and do candidate searches there too (**recursively** — see the layout below). (The vault is a git repo — after writing, sync the author folder via "After writing/editing: sync with git" below.)

### Author-folder layout — per-project subfolders + dated filenames

The author folder isn't flat. Entries are filed under a **per-project subfolder**, and filenames carry a **date prefix**:

```
$VAULT/journals/$AUTHOR/
├─ _inbox/                       # entries with no project (or a held one)
│  └─ 20260623-메모-아이디어.md
└─ <project-note-basename>/      # e.g. 이미지생성-파이프라인/
   ├─ 20260615-샘플러별-디테일-비교.md
   └─ 20260623-업스케일-검증.md
```

- **Subfolder** = the `project` note's filename (the wikilink basename, `[[ ]]` and any `|alias` stripped — e.g. `project: "[[이미지생성-파이프라인]]"` → folder `이미지생성-파이프라인`). No project, or a held/skipped one → `_inbox/`. Create the target folder with `mkdir -p` on demand.
- **Filename** = `YYYYMMDD-<title>.md` (details under "Writing a new entry").

Because the folder is nested, candidate searches and the refinement step read it **recursively** (project subfolders + `_inbox`).

## Keep the author folder tidy (auto-organize + migration)

Right after the vault and author folder are pinned, bring the author folder into the layout above before doing anything else. Older entries written under the flat scheme (loose in `journals/$AUTHOR/`, no date prefix) get filed into their project subfolder and renamed; entries already in place are left alone. This is **idempotent** — on a tidy folder it moves nothing.

For each `*.md` under `$VAULT/journals/$AUTHOR/` (recursive):

1. Read the `project` and `date` frontmatter.
2. **Target folder** = the `project` note basename (`[[ ]]`/`|alias` stripped); no project or a held one → `_inbox`.
3. **Target filename**:
   - already prefixed (`^\d{8}-`) → keep the name as-is.
   - otherwise → `<YYYYMMDD>-<current title>.md`, where `YYYYMMDD` is the `date` frontmatter with the dashes removed. If `date` is missing, fall back to the first git-commit date, then to mtime, and flag it in the report:
     ```
     git -C "$VAULT" log --diff-filter=A --date=format:%Y%m%d --format=%ad -- "<path>" | tail -1
     ```
4. If the current path already equals the target path, it's canonical — skip.
5. Otherwise move it with `git mv "<old>" "<target-dir>/<new>"` (`mkdir -p` the target dir first). **If the basename changed** (a rename, not just a move), rewrite the links pointing at it — next.

### Rewrite links on rename (`oldbase` → `newbase`)

A move alone is link-safe (Obsidian resolves by basename, which is unchanged). A **rename** changes the basename, so every `[[ ]]` pointing at the old name must be updated, **across the whole vault** (other members' journals, and `ontology/` `derivedFrom`/links):

```
# find the referencing notes
obsidian backlinks file="<oldbase>" format=json     # CLI present
grep -rl "[[<oldbase>" "$VAULT"                      # fallback when no CLI
```

In each referencing note, swap only the basename token, preserving any suffix — match `[[oldbase` only when the next char is `]`, `|`, `#`, or `^` (and the embed form `![[oldbase…]]`) so a longer name isn't partially clobbered:

```
[[oldbase]]  [[oldbase|alias]]  [[oldbase#heading]]  [[oldbase^block]]  ![[oldbase…]]
        → newbase (suffix kept)
```

### Scope, confirmation, and committing the migration

- **Write scope exception.** This routine is the one place the journal skill writes **outside the author folder** — it edits other members' notes and `ontology/` *solely to repair `[[ ]]` links* to renamed files, nothing else. (Everywhere else, leave other folders alone.)
- **Confirm a bulk transition once.** If the routine would move/rename more than a few files (the first transition off the flat scheme), give **one** heads-up first via AskUserQuestion — summarize "N files moved/renamed, M links rewritten" → proceed / skip. After that, incidental stragglers are filed without asking.
- **Commit the migration on its own**, so it's easy to review and revert, separate from the entry you're about to write:
  ```
  cd "$VAULT"
  git add journals/ ontology/        # migration touches links across both
  git commit -m "journal: migrate to project folders + dated filenames"
  ```
  (Honor `KALTI_GIT_SYNC` for whether to push — same modes as below. The normal entry commit stays scoped to `journals/$AUTHOR/`.)

## First, on every call: new entry vs existing entry

Don't guess whether this is new work or a continuation — ask the user. Make this decision after pinning the vault location and passing the "nothing to write about" gate above (i.e. once the work to record is settled). Ask via the **AskUserQuestion** tool — the choice UI is smoother. (If the user already said "as a new entry" / "continue that one" when invoking, follow that and skip the question.)

**1) New vs existing** (AskUserQuestion, two choices):
- **Write a new entry** → go to "Writing a new entry" below.
- **Continue/edit an existing entry** → go to candidate search.

**2) If existing — search, then let them pick:**
- Scan `$VAULT/journals/$AUTHOR/` and shortlist relevant candidates by relevance (title, `project`, open "next actions", topic).
- If there's **exactly one** candidate, merge into it without asking.
- If there are **two or more**, offer the **top 4 by relevance** as choices (this tool allows at most 4). If the wanted entry isn't listed, have the user type the filename in **"Other (type it in)"** — AskUserQuestion always offers free input, so any number of candidates fits within this limit.
- If there are **no** relevant candidates — the auto-search may have missed it, so confirm rather than silently starting a new entry. Ask (AskUserQuestion) "write a new entry / cancel", and let the user **name a file to merge into via "Other (type it in)"** (they may know a file the shortlist missed).

**3) Merging (continue/edit)** follows the "don't delete, revise" principle: don't erase or overwrite existing content. Append what's newly known with the date (`## 추가 기록 (2026-06-20)`, or `(2026-06-20 추가) ...` in the relevant section), and leave wrong content struck through (`~~...~~`) with the reason. Keep the existing filename — its date prefix marks the original creation date, so don't re-date it on edit.

(Even for entirely new work, if there's a related earlier entry, link it from the new note's `배경` section with `[[earlier entry]]`.)

## Writing a new entry

1. **Decide the location and filename.** File the note under its project subfolder `$VAULT/journals/$AUTHOR/<project-or-_inbox>/` (folder = the `project` note basename, or `_inbox` when there's no project; `mkdir -p` it). The filename is `YYYYMMDD-<title>.md`: a **date prefix** then a **descriptive title that says what was done** — the team works in Korean, so the titles are Korean (e.g. `$VAULT/journals/aram/이미지생성-파이프라인/20260615-샘플러별-디테일-비교.md`). The `YYYYMMDD` is the entry's `date` with the dashes removed (the `date` frontmatter still stays `YYYY-MM-DD`); the `id` field stays date-free. The date prefix sorts entries chronologically and the title keeps them recognizable at a glance — but it means **wikilinks to the entry include the prefix** (`[[20260615-샘플러별-디테일-비교]]`), so link by the full dated filename.
2. **Copy the template and fill it in.** Copy this skill's `assets/journal-template.md` verbatim and fill only the values. Start from the file rather than reconstructing the format from memory — the fields, order, and section titles are assumptions the refinement step depends on, and any drift breaks the automatic linking. Sections that don't apply can be left empty, but keep the order and titles.
3. If you're stuck on how to fill it, look at the worked example `references/example-experiment.md`.

## Choosing frontmatter values

Of the 7 template fields, these must be chosen from fixed sets:

**`type` (one)** — entry kind:

| value | meaning |
|---|---|
| `experiment` | experiment: set conditions, measure results |
| `investigation` | investigation: find a cause or current state |
| `build` | build: make/configure code, environment, tools |
| `reading` | reading: read and summarize papers/docs |
| `meeting` | meeting record |
| `decision` | decision record |
| `retro` | retrospective |

**`id` = type-abbrev + slug** — the abbreviation per type is `exp- / invest- / build- / read- / meet- / decide- / retro-` (e.g. `exp-sampler-detail`). Keep each id unique per entry (no date or sequence number) — reusing one blurs which entry the marker points to.

**`tags`** — only the agreed words: `infra · security · storage · network · ai · data · tooling · report · diffusion · sdxl · sampling · image · prompt`. Add a tag outside this list only after agreeing with the team; scattered tags break refinement and search.

**`tests`** — only for an `experiment` that tests a hypothesis: keep the template's `# tests:` line and point it at the hypothesis note under test. Drop that line for other types.

## Fill vs ask — only when genuinely ambiguous

The frontmatter values above (type, tags, project, tests) — the convention is all in this skill, so by default **fill them yourself** from session context plus a read of `ontology/`. Don't re-ask the user for something already decided (the "don't make me re-explain" principle).

**Only when unsure**, confirm once via AskUserQuestion — batched if possible. "Ambiguous" means:

- **project**: two or more candidates fit, or none in `ontology/` fits and a **new one** is needed. Offer the candidates + "new project" + "hold (skip)". If exactly one is clear, link it without asking. (Find candidates via `obsidian files folder=ontology` or the files in `$VAULT/ontology/`.)
- **type**: one piece of work straddles two types (e.g. build vs investigation) and it's unclear which. Put the inferred value as the first option marked "(recommended)" and confirm.
- **scope/boundary**: the session has **several** chunky pieces of work and it's unclear whether to combine them into one entry or split them. Ask how much counts as one entry.

Baseline: **fill when confident, ask only when not.** Don't ask about values the user already stated when invoking (e.g. "as a build entry for project X").

## Links by filename (not id)

Always write wikilinks `[[ ]]` with the note's **filename**, because Obsidian resolves links by filename (basename). `id` is just the entry's fixed marker, not a link identifier.
Example: `project: "[[이미지생성-파이프라인]]"` (good), `"[[proj-image-pipeline]]"` (bad).
Journal filenames carry the `YYYYMMDD-` date prefix, so links **to a journal** include it — `[[20260615-샘플러별-디테일-비교]]`, not `[[샘플러별-디테일-비교]]` (the same goes for the `배경` section's links to earlier entries). Ontology object names have no such prefix, so links to them stay bare.

## After writing/editing: sync with git

Entries are written **directly as files** in the author folder — they persist with no Obsidian, even when an agent runs headless. Sharing them is the point of this system, so they need to reach the shared git repo; if you write but don't push, nobody else sees it. How far to go is the user's preference in `KALTI_GIT_SYNC` (from the `notes.env` already sourced when resolving the vault; treat unset as `ask`):

- `push` — commit and push automatically.
- `commit` — commit locally only, don't push; tell the user it's committed but not yet shared.
- `ask` — ask once via AskUserQuestion (push now / commit only / skip), then do that.
- `off` — don't run git; the file is already saved.

When committing/pushing, scope it to the author folder so other people's changes and stray files aren't swept in:

```
cd "$VAULT"
git add "journals/$AUTHOR/"          # author folder only
git commit -m "journal: <note title or one-line summary>"
git pull --rebase --autostash        # integrate others' pushes first
git push                             # only in push mode, or when the user chose push in ask mode
```

Whatever the mode, handle these gracefully:
- **Vault isn't a git repo, or has no remote** — the file is already saved, so leave it and note in the summary that git sync was skipped (no remote).
- **push blocked by permissions** (no SSH key/token set) — the commit is already local, so the evidence is safe. Tell the user to run `git push` once they've set up access (it's a secret, so setup/skill can't supply it).
- **rebase conflict** (rare — usually the author folder doesn't collide) — auto-merging is risky, so revert with `git rebase --abort` and tell the user. A human needs to look at conflicts.

Put the sync result in the summary in one line.

## The five principles

- **Reproducibility**: someone could follow this exactly without you. "roughly" ❌ → "with value 12" ⭕
- **Traceability**: any conclusion can be backed to its basis within this note.
- **Write as you go**: writing it all up afterward loses numbers and steps.
- **Capture failures too**: record what didn't work and what was odd, so the same dead ends aren't repeated.
- **Don't delete, revise**: don't erase wrong content — strike it through (`~~...~~`) or append a correction, with the reason.

## What this skill touches (and what it can leave to others)

This skill only needs to focus on writing one entry in the author folder. The rest is handled elsewhere:

- **Hypotheses and findings** recorded in the entry body are enough. Promoting them into ontology objects is the `kalti-ontology` skill's job, so there's no need to touch `ontology/` here.
- Entries go **in the author folder (`journals/<name>/`)**, filed under per-project subfolders (`_inbox/` when no project) — leave other folders alone; they're that person's evidence. The single exception is the tidy/migration routine, which may edit other folders and `ontology/` *only to repair `[[ ]]` links* when it renames a file.

(Filename, tag, and link rules are in their sections above.)
