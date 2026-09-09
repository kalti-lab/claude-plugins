# Shared: resolving the vault, the author, and syncing with git

Every kalti skill is installed globally and runs **from whatever directory it was called in**,
so all of them start by pinning the vault down and end by deciding how far to sync. Those two
routines are identical across skills and live here so there is one copy to fix.

Each skill inlines the one-line happy path. Read this file when that path does not resolve,
or when you are about to run git.

---

## Resolving the vault (`$VAULT`)

`$VAULT` is the lab-notes clone root — the folder holding `journals/` and `ontology/` together.

1. **Config file.** `. ~/.config/kalti/notes.env 2>/dev/null` loads what `/kalti-setup` wrote.
   Use `$KALTI_VAULT` as `$VAULT` if that directory contains `journals/`.
2. **Default path.** If the file is missing or the value is empty, try `~/dev/lab-notes`.
3. **Neither resolves.** Do not guess and do not create a vault. Tell the user to run
   `/kalti-setup` once — it pins the vault into `~/.config/kalti/notes.env` and there are no
   more questions after that.

From there **every path is absolute under `$VAULT`**. A path relative to the working directory
(`journals/...`) would land the file in whatever repo the user happened to be sitting in.

Note that `. notes.env` sets the variables **without exporting them**, so a child process does
not see `$KALTI_VAULT`. Pass the value as an argument when calling a script.

## Resolving the author (`$AUTHOR`)

Only the skills that write or report per member need this.

1. `$KALTI_AUTHOR` from the same config file, if `$VAULT/journals/$KALTI_AUTHOR/` exists.
2. Otherwise **do not guess** — a typo carves out a stray folder (`journals/Aram/`) that then
   looks like a new member. List the existing folders under `$VAULT/journals/` and let the user
   pick with AskUserQuestion.
3. For a genuinely new member, take the folder name through "Other (type it in)" (lowercase
   latin recommended) and `mkdir -p` it.

## Reading the vault — always recursively

Both layers are nested, so a flat glob silently returns a partial answer instead of an error:

- `journals/<author>/<project>/…` — per-project subfolders, plus `_inbox/`
- `ontology/` — documents (project · concept · person · source) at the top level,
  `ontology/세부/` — the project-scoped cards (hypothesis · finding) underneath.
  A vault that has not been migrated yet holds all of them flat in `ontology/`; a recursive
  read is correct either way, which is exactly why it is the rule.

So never write `ontology/*.md` or `journals/*.md`. Use `grep -r … --include='*.md'`,
`find … -name '*.md'`, or `os.walk`. The same goes for a name-filtered read: not
`ontology/가설-*.md` but `grep -r … ontology/ --include='가설-*.md'`.

And write it `grep -ar`, not `grep -r`. One byte that is not valid UTF-8 — a truncated
character pasted out of a terminal, say — can make grep call the file binary and skip it
**whole**, with no warning and exit code 0. Measured on this vault: a bad byte planted in a
title line dropped that journal out of the refinement cursor's denominator, 279 → 278, in
silence; `-a` held it at 279. Note grep decides by sniffing the **start** of the file, so
the same byte appended to the end of that journal changed nothing — which makes this worse,
not better. It is intermittent, and it depends on where the byte happens to land.

What it costs when it does fire: a journal vanishes from the cursor's denominator, or a
card's every wikilink vanishes from the linked set, and the weekly prints the shrunken
number as if it were the count. `-a` reads the file as text instead. `shared/lint.py`
reports such a file as an error so it gets fixed at the source; `-a` is what keeps the
tally right until someone does.

---

## Syncing with git (`KALTI_GIT_SYNC`)

The vault is a shared git repo. Writing without pushing means nobody else sees the work, so
every skill that writes ends here. How far to go is the user's standing preference in
`KALTI_GIT_SYNC` (in the `notes.env` already sourced above; **unset counts as `ask`**):

| mode | what to do |
|---|---|
| `push` | commit and push automatically |
| `commit` | commit locally only — tell the user it is committed but not yet shared |
| `ask` | ask once with AskUserQuestion (push now / commit only / skip), then do that |
| `off` | don't run git at all; the file is already saved |

This setting only decides **how far a skill tries to go**. Permission to run git commands at all
is the Claude Code / Codex permission layer's business, not this one.

### The command shape

Each skill supplies its own `git add` scope and commit message prefix — never `git add -A`,
which sweeps in other people's edits and stray files:

```
cd "$VAULT"
git add <the scope this skill owns>
git commit -m "<prefix>: <one line>"
git pull --rebase --autostash        # integrate others' pushes first
git push                             # push mode, or when the user chose push in ask mode
```

### When it fails

The file is already written in every one of these cases, so nothing is lost. Report the outcome
in **one line** in the run summary and move on.

- **Not a git repo, or no remote** — leave it; say git sync was skipped (no remote).
- **Push blocked by permissions** (no SSH key or token) — the commit is local, so the work is
  safe. Tell the user to run `git push` once access is set up; a credential is a secret, so no
  skill can supply it.
- **Rebase conflict** (rare — members mostly touch different folders) — auto-merging is risky.
  Run `git rebase --abort` and tell the user. A human has to look at it.
