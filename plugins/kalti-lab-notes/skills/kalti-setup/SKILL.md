---
name: kalti-setup
disable-model-invocation: true
description: "One-time setup before using the kalti research-journal system. Resolves the lab-notes vault location (KALTI_VAULT) and the user's own journal folder (KALTI_AUTHOR), writes them to the config file ~/.config/kalti/notes.env, clones the vault if missing, registers that folder as an Obsidian vault in the app, and points the user at the Obsidian CLI and the kepano obsidian-skills install. Invoke with /kalti-setup — for 'set up', 'first-time setup', or 'connect my vault' requests, or when kalti-journal/kalti-ontology are blocked because KALTI_VAULT/KALTI_AUTHOR aren't set. Re-run it to fix a wrong value or change the vault/author folder; it shows the current values and reconfigures. Global plugin: works regardless of the current working directory."
---

# kalti setup (one-time)

The job is small: find two values — the vault root (`KALTI_VAULT`) and the user's own journal folder (`KALTI_AUTHOR`) — and write them to `~/.config/kalti/notes.env`. After that, `/kalti-journal` and `/kalti-ontology` read this file from any directory and know the vault and the user's folder.

This is preparation, not research work, so the user wants it over quickly. Settle the obvious things with sensible defaults, ask only for what genuinely needs a human (a new folder name, say), and end with a short summary of what was done and the final values. Spelling out a rationale at every step only drags the prep out.

## First, on every call: new setup or reconfigure?

`/kalti-setup` is typed deliberately. Read the current values first with `. ~/.config/kalti/notes.env 2>/dev/null` and branch:

- **File missing or empty** — new setup. Walk "Vault" → "Author folder" → "Git sync mode" → "Persist" below.
- **Values present** — this is a reconfigure. Show all three current settings (`KALTI_VAULT`/`KALTI_AUTHOR`/`KALTI_GIT_SYNC`), and flag any that are broken (`$KALTI_VAULT` has no `journals/`, or `$VAULT/journals/$KALTI_AUTHOR/` is gone). Then ask with a **multi-select** AskUserQuestion which settings to (re)configure — vault / author folder / git-sync mode — noting any broken one as needing a fix. Re-resolve each selected item via its section, re-picking even if the current value is valid (that's the point of changing it); leave unselected items as they are. If nothing is selected, keep everything (but if a broken item was left unselected, point out that it'll stay broken). Then overwrite `notes.env` via "Persist".

## Vault (`KALTI_VAULT`)

Resolve the vault in these steps, stopping at the first hit. Avoid wide filesystem sweeps (e.g. `find ~/dev`): they're slow, they surprise the user by scanning places they didn't expect, and the same answer takes a human one second.

1. If `notes.env`'s `$KALTI_VAULT` is valid (has `journals/` inside), use it. Done.
2. Otherwise, check whether the current folder or one or two levels up holds both `journals/` and `ontology/` — if so, the skill was called from inside a clone, and that's the vault. Use it.
3. Still nothing: the user is the fastest source now. Ask (AskUserQuestion) with two choices:
   1. **Set up in the current folder** — clone into here (`<pwd>`) with `git clone https://github.com/kalti-lab/lab-notes.git`.
   2. **Have a specific path?** — take the path via "Other (type it in)" (an existing vault's path, or a location to clone into).

## Author folder (`KALTI_AUTHOR`)

With the vault set, settle the user's own journal folder. This folder *is* the user's identity in the shared vault, so confirm it — don't infer it. A freshly cloned vault already holds other members' folders (and seed/sample folders), so a folder merely existing doesn't make it *this* user's, and a stale `$KALTI_AUTHOR` carried over from a previous config may not be them either.

- **Skip the question only when the author is already settled for this run** — either it's a reconfigure and the user didn't select the author folder to change (its valid value stands), or they named their folder when invoking. Then use that.
- **Otherwise — new setup, or the user chose to (re)configure the author folder** — list the folders under `$VAULT/journals/` and have the user pick (AskUserQuestion). Don't silently adopt an existing folder just because it matches a stale value or happens to exist. A returning member picks their own; a new member uses "Other (type it in)" to name a new one (lowercase latin recommended). Guessing a name risks a typo that carves a stray folder (`journals/Aram/`) and splits journals in two.
- On "create new", `mkdir -p "$VAULT/journals/<name>"`.

## Git sync mode (`KALTI_GIT_SYNC`)

After writing an entry, `/kalti-journal` and `/kalti-ontology` can sync to the shared git repo. How far they go is the user's preference, stored here so the skills can read it. Ask once (AskUserQuestion) and default to **ask** — the safe choice, since nothing leaves the machine without a per-write confirmation. The modes:

- `ask` (default) — after writing, the skill asks each time: push / commit only / skip.
- `push` — commit + `pull --rebase` + push automatically.
- `commit` — commit locally only; the user pushes later.
- `off` — don't touch git; just write the file.

This is a per-write preference for the kalti skills. Separately, Claude Code may still show its own permission prompt for the underlying git commands unless the user has allowlisted them in CC settings — that's a CC-level thing, independent of this value, so it's worth a one-line mention if they want truly prompt-free pushing.

## Persist

Write the settled values to `~/.config/kalti/notes.env`. Leave the shell config (`~/.zshrc`/`~/.zshenv`) alone — the skills read this file directly on every call, so there's no need to lean on the shell environment, and that also sidesteps the old problem of non-interactive shells not reading rc files. Just rewrite the file whole:

```
mkdir -p ~/.config/kalti
cat > ~/.config/kalti/notes.env <<EOF
KALTI_VAULT=<path>
KALTI_AUTHOR=<name>
KALTI_GIT_SYNC=<mode>
EOF
```
(This is a different path from `~/.kalti/`, which holds infrastructure secrets.)

## Register the vault in Obsidian

Writing `notes.env` only configures the kalti side — Obsidian itself doesn't know that folder is a vault. Without this step, the user opens Obsidian and lab-notes isn't there. For the graph view, and for the CLI to work during refinement, a freshly cloned (or otherwise unknown) vault has to be added to the app's vault list (`obsidian.json`).

The tricky part is timing: if Obsidian is running, edits to `obsidian.json` get overwritten with its in-memory state on quit. So when it's running, the safe order is quit gracefully → register → relaunch. A bundled script handles all of this (state check, idempotent registration, atomic write, and the quit/relaunch on macOS).

Since quitting a running app interrupts the user, confirm first (a one-line heads-up or AskUserQuestion) before running it. Once confirmed:
```
python3 <this skill's path>/scripts/register_obsidian_vault.py "$VAULT" --restart
```
Branch on the status the script prints:

- `REGISTERED` (was closed, registered directly) / `REGISTERED_WITH_RESTART` (macOS: quit gracefully, registered, relaunched) / `ALREADY_REGISTERED` — done. Any vault that was open is restored, and lab-notes now shows in the vault list.
- `NOT_INSTALLED` — the Obsidian app isn't on this machine (the script checks for the app, not just the CLI, and won't write a phantom config). This isn't a failure: journaling works without Obsidian, since entries are written directly as files (headless OK). But Obsidian gives the graph view and the refinement CLI, so be helpful — offer to install it rather than just pointing the user off-screen:
  - **macOS with Homebrew** (`which brew` succeeds) — offer to install it for them, and on a yes run `brew install --cask obsidian`. Installing software is a real change, so confirm first (a quick yes/no or AskUserQuestion); don't run it unprompted.
  - **No Homebrew, or another OS** — give the official download link (https://obsidian.md/download). Don't download and run an installer blind — point them to the official page.

  After it's installed, re-run registration (`register_obsidian_vault.py "$VAULT" --restart`) so the vault gets added. If the user would rather skip Obsidian for now, that's fine — journaling already works; they can install later and re-run `/kalti-setup`.
- `NEEDS_GUI` (the app is installed but can't be driven automatically — not macOS, or it wouldn't close, etc.) — don't force it; guide the user through GUI registration: Obsidian's vault icon (bottom-left) → "Open another vault" → "Open folder as vault" → pick `$VAULT`.

The quit is graceful, not a force-kill, so work is saved before it closes, and registration only happens after the close is confirmed — no data loss. (If a conservative mode that never touches the app is needed, call the script without `--restart`; it returns `NEEDS_GUI` when the app is running.)

Note in the summary that lab-notes is now in Obsidian's vault list.

## Obsidian CLI

Just check `which obsidian`. If present, move on; if not, note in the summary that enabling Settings → General → Command line interface speeds up graph queries during ontology refinement (it still works without it, via file reads).

## kepano obsidian-skills (required)

This is the official skill bundle that teaches the model Obsidian syntax and CLI usage, so the refinement step relies on it — it's a required part of setup. Check whether it's already installed before asking — Claude Code records installed plugins in `~/.claude/plugins/installed_plugins.json` keyed by `<plugin>@<marketplace>`, so the kepano bundle appears as `obsidian@obsidian-skills`:
```
grep -q '"obsidian@obsidian-skills"' ~/.claude/plugins/installed_plugins.json 2>/dev/null && echo INSTALLED || echo MISSING
```
- `INSTALLED` — note it in the summary and move on.
- `MISSING` — ask the user to run these two lines themselves (the model can't type `/plugin`), and make clear in the summary that setup isn't complete until they do. Present them as a fenced code block, each on its own line, so they're easy to copy — not run together in a sentence:
  ```
  /plugin marketplace add kepano/obsidian-skills
  /plugin install obsidian@obsidian-skills
  ```

## When done

Show the final values (`KALTI_VAULT`/`KALTI_AUTHOR`/`KALTI_GIT_SYNC`) and what was done (folder created / `notes.env` written / Obsidian vault registered / kepano installed or not).

Then tell the user about the two skills they can now use — the user just finished setup, often doesn't know what these do, and a bare name goes unused. Two points matter and are easy to get wrong:

- **They don't fire on their own.** Both are slash-only (`disable-model-invocation`), so they never trigger from ordinary conversation — the user has to type `/kalti-journal` or `/kalti-ontology`. This is deliberate: it keeps a journal from being created when nobody asked. Saying "log what I just did" in chat won't start the journal skill; typing the command does.
- **What each is for:** `/kalti-journal` records work the user just did as a research-journal entry, in their own folder (`journals/<name>/`, filed under per-project subfolders with a `YYYYMMDD-` dated filename). `/kalti-ontology` pulls hypotheses and findings out of accumulated journals and curates them into the knowledge graph (usually in batches).

Phrase this however reads naturally — there's no fixed wording.

(This setup never handles secrets — if a token or an infra key under `~/.kalti/` happens to surface, leave it untouched and don't print it.)
