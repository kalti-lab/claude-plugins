---
name: kalti-weekly
disable-model-invocation: true
description: "Convention for rolling up kalti research journals into a weekly lab report. Gathers the entries in journals/ whose date falls in a given ISO week, groups them reader-first (domain → project → member) into six buckets (progress, findings, decisions, blockers, next actions, ontology candidates), and writes one report per week to reports/weekly/YYYY-Www.md with a one-line summary + [[link]] per item. Invoke with /kalti-weekly (this week), /kalti-weekly 2026-W28 (a specific week), or /kalti-weekly --backfill 2026-W22..2026-W28 (past weeks). Re-running is idempotent: only the auto-generated region is rewritten, hand-written operator notes are preserved. Where kalti-journal records evidence and kalti-ontology curates knowledge, this produces the periodic shared report the group reads."
---

# kalti weekly report

The journal system has three layers.

- **Journal layer `journals/<name>/`** — each member's record of work = **evidence**. Entries are filed under per-project subfolders (`_inbox/` when no project), with `YYYYMMDD-`prefixed filenames — so read it **recursively**.
- **Ontology layer `ontology/`** — the curated knowledge (managed by the group).
- **Report layer `reports/weekly/`** — the periodic roll-up the group reads: one file per ISO week, plus an index. **This skill writes here.**

This skill is the **weekly roll-up** side. A weekly report is a **navigation map, not a copy**: each item is a one-line summary plus a `[[link]]` back to the source journal, so a reader scans fast and clicks through for detail. It is a **derived view** — the auto-generated region is regenerated from the journals on every run (unlike a journal, which is append-only evidence).

The two principles behind every choice here: **stay faithful to the journals** (one-liners must be backed by the entry — never invent progress that isn't recorded), and **be easy for researchers to reference** (readers look for "my project / what X did / where that decision is", so lead with project and member, not with category).

## Where to work — resolve the vault first

As a global plugin this runs **from whatever directory it's called in**, so pin down the vault root (the lab-notes clone, where `journals/`, `ontology/`, `reports/` live together) **first**. Order:

1. **Config file**: `. ~/.config/kalti/notes.env 2>/dev/null` reads the `$KALTI_VAULT` that setup wrote. If it contains `journals/`, use it as `$VAULT`.
2. If missing or empty, try the **default path** `~/dev/lab-notes`.
3. If neither resolves, point the user to run `/kalti-setup` first.

From there every path is absolute under `$VAULT`. Reports are written by **direct file write** into `$VAULT/reports/weekly/` (`mkdir -p` on demand; headless OK). `$KALTI_GIT_SYNC` (same file) controls git sync at the end.

## Resolve the target week(s)

The argument decides which week(s) to build. Weeks are **ISO 8601** (Monday–Sunday); a report is named by its ISO week `YYYY-Www` (e.g. `2026-W28`).

| invocation | meaning |
|---|---|
| `/kalti-weekly` | the current ISO week (from today) |
| `/kalti-weekly 2026-W28` | that one ISO week |
| `/kalti-weekly 2026-07-08` | the ISO week containing that date |
| `/kalti-weekly --backfill 2026-W22..2026-W28` | every ISO week in the range that has entries (one report each) |
| `/kalti-weekly <week> <member>` | restrict to one member's folder (default: whole lab) |

Compute the week's Monday–Sunday date bounds. Derive the ISO week label with `date -d <date> +%G-W%V` (note `%G`, the ISO-week-year, not `%Y`). For `--backfill`, iterate weeks across the range and build only those with at least one entry — and **`log`/report which weeks were skipped as empty** so the coverage is explicit.

## Gather the week's entries

Walk `$VAULT/journals/` **recursively** and select entries whose `date` frontmatter falls within the week's bounds (inclusive). For a member-scoped run, restrict to that author folder. Skip project-history files (`00-*.md`) — they are retrospectives, not week-dated work.

Prefer the **obsidian CLI** when present (`obsidian search`, `obsidian properties file=... format=json`) for accurate frontmatter reads; if `which obsidian` finds nothing (headless), read the files directly (graceful fallback — same result). For each selected entry, read: `author`, `project`, `type`, `title`, and the section bodies used below.

If **no** entries fall in the week, don't write an empty report — tell the user the week is empty and stop (for `--backfill`, just skip it).

## Classify into six buckets (reader-first)

Group the selected entries **domain → project → member**, and within each project render the relevant buckets. Pull each bucket from the entry's matching section — a one-liner in the report, detail stays in the journal:

| bucket | pulled from | notes |
|---|---|---|
| **진행·완료** (progress) | `한 일(방법)`, `type: build` | what was made/done |
| **발견·결과** (findings) | `결과/관찰`, `해석` (`experiment`·`investigation`) | values/observations as seen |
| **결정** (decisions) | `결정`, `type: decision` | what was decided and why |
| **막힌 점·이슈** (blockers) | `해석/막힌 점·해결` | failures & dead ends (so they aren't repeated) |
| **다음 주 계획** (next) | `다음 액션` | measurable next goals |
| **지식화 후보** (ontology candidates) | hypotheses/findings flagged in the body | feeds `/kalti-ontology` |

Every rendered item ends with a `[[link]]` to the source journal (**include the `YYYYMMDD-` prefix** — that is the filename). Omit empty buckets. The minimal core, if trimming, is 발견·결정·다음.

Domains are the recurring topic clusters (e.g. 메모리 시스템 / AI 에이전트 도구 / 금융·트레이딩 ML / ML 평가·검증 하네스 / 콘텐츠 생성 / 이미지 생성 / 연구방법론). Infer each project's domain from its work; when unsure, group by project alone rather than forcing a domain.

## Write the report (idempotent)

Copy `assets/weekly-template.md` and fill it. The report has a fixed shape:

- **Header** — title with week + period.
- **한 화면 TL;DR** — 3 highlight lines (the week's most important results/decisions, synthesized) + a member×count table with each member's active projects. This is the only part you *summarize*; the buckets are *extracted*.
- **Body** — the domain → project → bucket structure above.
- **Tail sections** — 열린 다음 액션 (carry-over), 지식화 후보, then the prev/next + index footer. The footer sits **inside** the auto region so it regenerates: when a neighboring week's report appears later, re-running updates the link automatically. The `## 운영자 코멘트 / 메모` area comes **after** the auto region (last in the file) so hand-written notes are preserved.

**Idempotency is the core requirement — running the same week repeatedly must not duplicate or clobber:**

1. **Deterministic filename** — `reports/weekly/YYYY-Www.md`. Same week → same file, always updated in place, never a `2026-W28 (1).md`.
2. **Auto region markers** — everything generated sits between `<!-- kalti-weekly:auto:start -->` and `<!-- kalti-weekly:auto:end -->`. On re-run, **replace only that region**; leave everything outside it (the `## 운영자 코멘트 / 메모` area) untouched. If the file doesn't exist yet, create it from the template.
3. **Deterministic ordering** — sort entries `date → project → author` so the same journals always produce byte-identical output. With no new/changed journals, a re-run yields no diff.
4. **Index upsert** — update the row for this week in `reports/weekly/README.md` if present, else add it (newest first). Never append a duplicate row.
5. **Neighbor link refresh** — after writing this week, if an adjacent week's report already exists, update *its* footer link to point back here (the newly-created week is that neighbor's prev/next). This keeps the chain consistent without needing to re-run the neighbors.

Because the auto region is regenerated from source, edits made to a journal after a report was built are picked up on the next run automatically. Mid-week runs are partial and fill in as the week progresses — that is expected.

The `prev/next` footer links the adjacent ISO weeks (`[[2026-W27]]` / `[[2026-W29]]`); use `(없음)` when a neighbor has no report.

## After writing: sync with git

Honor `KALTI_GIT_SYNC` (unset → `ask`), scoping the commit to the report layer so nothing else is swept in:

```
cd "$VAULT"
git add reports/
git commit -m "weekly: <week label> 주간 보고"
git pull --rebase --autostash
git push          # only in push mode, or when the user chose push in ask mode
```

Modes: `push` (commit+push), `commit` (local only), `ask` (AskUserQuestion: push/commit/skip), `off` (no git). Handle no-remote / permission-blocked push / rebase conflict the same graceful way the other skills do (the file is already saved; report the outcome in one line).

## What this skill touches (and what it leaves alone)

- Writes **only** under `reports/weekly/`. It **reads** `journals/` (all members) to aggregate, but never edits journals or `ontology/` — those are evidence and curated knowledge owned elsewhere.
- It does not create ontology objects; it only **surfaces candidates** in the 지식화 후보 bucket for `/kalti-ontology` to curate.
- It does not fix journal hygiene (empty folders, frontmatter drift); if it notices problems while reading, mention them in the run summary rather than editing.
