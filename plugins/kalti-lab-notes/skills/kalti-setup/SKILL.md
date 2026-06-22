---
name: kalti-setup
disable-model-invocation: true
description: "One-time setup before using the kalti research-journal system. Resolves the lab-notes vault location (KALTI_VAULT) and the user's own journal folder (KALTI_AUTHOR), writes them to the config file ~/.config/kalti/notes.env, clones the vault if missing, registers that folder as an Obsidian vault in the app, and points the user at the Obsidian CLI and the kepano obsidian-skills install. Invoke with /kalti-setup — for 'set up', 'first-time setup', or 'connect my vault' requests, or when kalti-journal/kalti-ontology are blocked because KALTI_VAULT/KALTI_AUTHOR aren't set. Re-run it to fix a wrong value or change the vault/author folder; it shows the current values and reconfigures. Global plugin: works regardless of the current working directory."
---

# kalti setup (one-time)

The job is small: find two values — the vault root (`KALTI_VAULT`) and the user's own journal folder (`KALTI_AUTHOR`) — and write them to `~/.config/kalti/notes.env`. After that, `/kalti-journal` and `/kalti-ontology` read this file from any directory and know the vault and the user's folder.

This is preparation, not research work, so the user wants it over quickly. Settle the obvious things with sensible defaults, ask only for what genuinely needs a human (a new folder name, say), and end with a short summary of what was done and the final values. Spelling out a rationale at every step only drags the prep out.

## First, on every call: new setup or reconfigure?

`/kalti-setup` is typed deliberately. If it's run when things are already set up, it usually means the user wants to fix something. So read the current values first with `. ~/.config/kalti/notes.env 2>/dev/null` and branch:

- **File missing or empty** — new setup. Go through "Vault" → "Author folder" → "Persist" below.
- **Values present but pointing at something broken** (`$KALTI_VAULT` has no `journals/`, or `$VAULT/journals/$KALTI_AUTHOR/` is gone) — say what's broken and re-resolve just that item via its section. The user came to fix it; declaring "already set up" and stopping would waste the trip.
- **Values present and valid** — show the current `KALTI_VAULT`/`KALTI_AUTHOR` and let the user choose what to do (AskUserQuestion): keep as-is / change the author folder / change the vault / start over. If they pick a change, have them re-pick that value even though it's currently valid — re-offering the existing value defeats the point of coming to change it. Then overwrite `notes.env` via "Persist".

## Vault (`KALTI_VAULT`)

Resolve the vault in these steps, stopping at the first hit. Avoid wide filesystem sweeps (e.g. `find ~/dev`): they're slow, they surprise the user by scanning places they didn't expect, and the same answer takes a human one second.

1. If `notes.env`'s `$KALTI_VAULT` is valid (has `journals/` inside), use it. Done.
2. Otherwise, check whether the current folder or one or two levels up holds both `journals/` and `ontology/` — if so, the skill was called from inside a clone, and that's the vault. Use it.
3. Still nothing: the user is the fastest source now. Ask (AskUserQuestion) with two choices:
   1. **Set up in the current folder** — clone into here (`<pwd>`) with `git clone https://github.com/kalti-lab/lab-notes.git`.
   2. **Have a specific path?** — take the path via "Other (type it in)" (an existing vault's path, or a location to clone into).

## Author folder (`KALTI_AUTHOR`)

With the vault set, pick the user's own journal folder. Pick from folders that actually exist rather than guessing — a guessed name with one typo creates a stray folder (`journals/Aram/`) and splits journals in two.

1. If `$KALTI_AUTHOR` already exists under `$VAULT/journals/`, use it.
2. Otherwise list the folders in `journals/` and let the user pick (AskUserQuestion).
3. If they pick "create new", take a single folder name and `mkdir -p "$VAULT/journals/<name>"`.

## Persist

Write the two settled values to `~/.config/kalti/notes.env`. Leave the shell config (`~/.zshrc`/`~/.zshenv`) alone — the skills read this file directly on every call, so there's no need to lean on the shell environment, and that also sidesteps the old problem of non-interactive shells not reading rc files. Just rewrite the file whole:

```
mkdir -p ~/.config/kalti
cat > ~/.config/kalti/notes.env <<EOF
KALTI_VAULT=<path>
KALTI_AUTHOR=<name>
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
- `NEEDS_GUI` (not macOS, or the app wouldn't close, etc.) — don't force it; guide the user through GUI registration: Obsidian's vault icon (bottom-left) → "Open another vault" → "Open folder as vault" → pick `$VAULT`.

The quit is graceful, not a force-kill, so work is saved before it closes, and registration only happens after the close is confirmed — no data loss. (If a conservative mode that never touches the app is needed, call the script without `--restart`; it returns `NEEDS_GUI` when the app is running.)

Note in the summary that lab-notes is now in Obsidian's vault list.

## Obsidian CLI

Just check `which obsidian`. If present, move on; if not, note in the summary that enabling Settings → General → Command line interface speeds up graph queries during ontology refinement (it still works without it, via file reads).

## kepano obsidian-skills (required)

This is the official skill bundle that teaches the model Obsidian syntax and CLI usage, so the refinement step relies on it — it's a required part of setup. If it's not installed yet, ask the user to run these two lines themselves (the model can't type `/plugin`):
```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```
Make clear in the summary that setup isn't complete until kepano is installed, so the user doesn't skip it.

## When done

Show the final values (`KALTI_VAULT`/`KALTI_AUTHOR`) and what was done (folder created / `notes.env` written / Obsidian vault registered / kepano installed or not).

Then tell the user about the two skills they can now use — the user just finished setup, often doesn't know what these do, and a bare name goes unused. Two points matter and are easy to get wrong:

- **They don't fire on their own.** Both are slash-only (`disable-model-invocation`), so they never trigger from ordinary conversation — the user has to type `/kalti-journal` or `/kalti-ontology`. This is deliberate: it keeps a journal from being created when nobody asked. Saying "log what I just did" in chat won't start the journal skill; typing the command does.
- **What each is for:** `/kalti-journal` records work the user just did as a research-journal entry, in their own folder (`journals/<name>/`). `/kalti-ontology` pulls hypotheses and findings out of accumulated journals and curates them into the knowledge graph (usually in batches).

Phrase this however reads naturally — there's no fixed wording.

(This setup never handles secrets — if a token or an infra key under `~/.kalti/` happens to surface, leave it untouched and don't print it.)
