---
name: kalti-report
disable-model-invocation: true
description: "Builds the kalti lab's derived report layer under reports/ — the two views that read journals/ and ontology/ but never write to them. Three modes. /kalti-report (or --weekly) rolls one member's journals for an ISO week into reports/weekly/<author>/YYYY-Www.md as a navigation map: six buckets (progress, findings, decisions, blockers, next actions, ontology candidates), each item one line plus a wikilink back to the source journal; accepts a week (2026-W28), a member, or --backfill A..B, and is idempotent (everything above the 운영자 코멘트 heading regenerates). /kalti-report --contrib shows what each member has put in as three plain numbers side by side (연구노트 · 카드 · 밀도), with no total, no rank, and no winner; screen-only, it writes no file. /kalti-report --digest [YYYY-MM] builds the monthly whole-lab newspaper (연구실 소식) into reports/digest/YYYY-MM.html — an A4 two-page fixed layout: 이달의 연구 leads page one, four more stories on page two, what got overturned, one quoted sentence from a journal, per-member contrib; every number comes from count.py --digest and the issue is a single self-contained HTML file. All are derived views: they are regenerated from the journals, so nothing here is ever the grounding for an ontology card."
---

# kalti report layer

## 낱말 — 쓰기 전에 읽는다

**`${CLAUDE_PLUGIN_ROOT}/shared/writing.md`를 따른다.** 한국 사람이 실제 대화에서 쓰는 낱말만 쓰고, 글에서나 보이는 말·번역투·새로 만든 비유는 안 쓴다. 기술 용어는 뜻을 우리말로 먼저 말하고 이름을 괄호에 넣는다. 지적받은 뒤에 고치는 게 아니라 처음 쓸 때부터 그렇게 쓴다. 그 파일에 이 볼트에서 실제로 걸렸던 낱말 표가 있다.

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
| `/kalti-report`, `2026-W28`, `… jinsik`, `--backfill A..B` | **weekly** (default) | `references/weekly.md` |
| `/kalti-report --contrib` (screen only, writes nothing) | **contrib** | `references/contrib.md` |
| `/kalti-report --digest [YYYY-MM]` (default: last month) | **digest** (월간 소식) | `references/digest.md` |

All three live under `${CLAUDE_PLUGIN_ROOT}/skills/kalti-report/`. The full convention is in there, not here.

**A bare `/kalti-report` asks one question before starting weekly mode** (AskUserQuestion): whose
week to write — **me only** / **every member, one file each** / a named member. Members are the
folders under `journals/`. Skip the question when the invocation already names a member, a
`--backfill`, or the user said whose. "Every member" runs the same personal weekly once per member
into each `reports/weekly/<member>/` folder — it is a batch of personal reports, not a combined
lab report (that place belongs to the monthly 소식, `--digest`).

## Vault, author, git

```
. ~/.config/kalti/notes.env 2>/dev/null
VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"; AUTHOR="$KALTI_AUTHOR"
```

`$AUTHOR` is weekly mode's "me"; contrib mode is always the whole lab and never
asks which member. Reports are written by direct file write into `$VAULT/reports/` (`mkdir -p` on
demand; headless OK).

If `$VAULT` has no `journals/`, or weekly mode needs an author and `$KALTI_AUTHOR` is empty, and
again before running git, follow **`${CLAUDE_PLUGIN_ROOT}/shared/vault-and-git.md`** — it holds
the fallbacks, the four sync modes (`push` / `commit` / `ask` / `off`, unset = `ask`) and the
failure handling. This skill's scope is `git add reports/` — never `-A` — with
`weekly: <author> <week> 주간 보고` or `digest: <YYYY-MM> 소식` (contrib writes nothing, so it never commits).

## What this skill never does

It never edits `journals/` or `ontology/`, and never creates ontology objects — weekly mode only
*surfaces* candidates for `/kalti-ontology`. It does not fix what it notices either: malformed
frontmatter, an uncited journal, a project with no cards go in the run summary, and the fixing is
left to `/kalti-journal` and `/kalti-ontology`.
