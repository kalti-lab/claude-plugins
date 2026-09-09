---
name: kalti-report
disable-model-invocation: true
description: "Builds the kalti lab's derived report layer under reports/ — the two views that read journals/ and ontology/ but never write to them. Two modes. /kalti-report (or --weekly) rolls one member's journals for an ISO week into reports/weekly/<author>/YYYY-Www.md as a navigation map: six buckets (progress, findings, decisions, blockers, next actions, ontology candidates), each item one line plus a wikilink back to the source journal; accepts a week (2026-W28), a member, --backfill A..B, or --all for a whole-lab report, and is idempotent (everything above the 운영자 코멘트 heading regenerates). /kalti-report --contrib shows what each member has put in as three plain numbers side by side (연구노트 · 카드 · 밀도), with no total, no rank, and no winner; screen-only unless --write. Both are derived views: they are regenerated from the journals, so nothing here is ever the grounding for an ontology card."
---

# kalti report layer

The vault has three layers: `journals/<name>/` (each member's evidence), `ontology/` (the curated
knowledge), and `reports/` (the periodic derived views). **This skill writes to the third, and
only the third.** Both other layers are nested, so read them recursively — never `journals/*.md`
or `ontology/*.md`.

Two things hold in both modes:

- **A report is a map, not a copy.** One line per item plus a link back to the source; the reader
  scans, then clicks through.
- **A report is derived, never grounding.** It is regenerated from the journals, so an ontology
  card must cite the *journal*. A summary of a summary cannot carry the quoted sentence that
  refinement depends on.

## Pick the mode, then read its reference file

| invocation | mode | follow |
|---|---|---|
| `/kalti-report`, `2026-W28`, `… jinsik`, `--backfill A..B`, `--all` | **weekly** (default) | `references/weekly.md` |
| `/kalti-report --contrib` (`--write` to save a copy) | **contrib** | `references/contrib.md` |

Both live under `${CLAUDE_PLUGIN_ROOT}/skills/kalti-report/`. The full convention is in there, not
here. A bare `/kalti-report` is weekly mode for the invoking member's current ISO week — don't ask.

## Vault, author, git

```
. ~/.config/kalti/notes.env 2>/dev/null
VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"; AUTHOR="$KALTI_AUTHOR"
```

`$AUTHOR` is weekly mode's default report author; contrib mode is always the whole lab and never
asks which member. Reports are written by direct file write into `$VAULT/reports/` (`mkdir -p` on
demand; headless OK).

If `$VAULT` has no `journals/`, or weekly mode needs an author and `$KALTI_AUTHOR` is empty, and
again before running git, follow **`${CLAUDE_PLUGIN_ROOT}/shared/vault-and-git.md`** — it holds
the fallbacks, the four sync modes (`push` / `commit` / `ask` / `off`, unset = `ask`) and the
failure handling. This skill's scope is `git add reports/` — never `-A` — with
`weekly: <author> <week> 주간 보고` or `contrib: <YYYY-MM-DD> 기여 현황`.

**Contrib mode confirms before committing even in `push` mode.** Every other commit in this system
is the author's own record; that one is a file about colleagues.

## What this skill never does

It never edits `journals/` or `ontology/`, and never creates ontology objects — weekly mode only
*surfaces* candidates for `/kalti-ontology`. It does not fix what it notices either: malformed
frontmatter, an uncited journal, a project with no cards go in the run summary, and the fixing is
left to `/kalti-journal` and `/kalti-ontology`.
