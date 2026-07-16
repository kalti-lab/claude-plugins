---
name: kalti-weekly
disable-model-invocation: true
description: "Convention for rolling up a kalti member's research journals into a weekly report. By default it builds the invoking member's OWN report: gathers that author's entries in journals/<author>/ whose date falls in a given ISO week, groups them reader-first (domain → project) into six buckets (progress, findings, decisions, blockers, next actions, ontology candidates), and writes reports/weekly/<author>/YYYY-Www.md with a one-line summary + link per item. Invoke with /kalti-weekly (my current week), /kalti-weekly 2026-W28 (my week 28), /kalti-weekly 2026-W28 jinsik (another member), /kalti-weekly --backfill 2026-W22..2026-W28 (past weeks), or /kalti-weekly --all (optional whole-lab combined report). Re-running is idempotent: everything above the `## 📝 운영자 코멘트 / 메모` heading is regenerated, that section and below is preserved. The report contains no HTML comments."
---

# kalti weekly report

The journal system has three layers.

- **Journal layer `journals/<name>/`** — each member's record of work = **evidence**. Entries are filed under per-project subfolders (`_inbox/` when no project), with `YYYYMMDD-`prefixed filenames — so read it **recursively**.
- **Ontology layer `ontology/`** — the curated knowledge (managed by the group).
- **Report layer `reports/weekly/<author>/`** — each member's periodic roll-up: one file per ISO week, per member, plus an index. **This skill writes here.**

This skill is the **weekly roll-up** side. A weekly report defaults to **one member's own work** (the invoking author) — it is not a lab-wide report unless explicitly asked with `--all`. A report is a **navigation map, not a copy**: each item is a one-line summary plus a link back to the source journal, so a reader scans fast and clicks through for detail. It is a **derived view** — everything above the operator-notes heading is regenerated from the journals on every run (unlike a journal, which is append-only evidence).

The two principles behind every choice here: **stay faithful to the journals** (one-liners must be backed by the entry — never invent progress that isn't recorded), and **be easy to reference** (lead with project, not with category).

## Where to work — resolve the vault and author first

As a global plugin this runs **from whatever directory it's called in**, so pin down the vault root and the author **first**. Order:

1. **Config file**: `. ~/.config/kalti/notes.env 2>/dev/null` reads `$KALTI_VAULT` and `$KALTI_AUTHOR` that setup wrote. If `$KALTI_VAULT` contains `journals/`, use it as `$VAULT`; use `$KALTI_AUTHOR` as the **default report author**.
2. If missing or empty, try the **default path** `~/dev/lab-notes`; for the author, list the folders in `$VAULT/journals/` and let the user pick (AskUserQuestion) rather than guessing.
3. If neither resolves, point the user to run `/kalti-setup` first.

From there every path is absolute under `$VAULT`. Reports are written by **direct file write** into `$VAULT/reports/weekly/<author>/` (`mkdir -p` on demand; headless OK). `$KALTI_GIT_SYNC` (same file) controls git sync at the end.

## Resolve the target week(s) and author

The arguments decide **which author** and **which week(s)** to build. Weeks are **ISO 8601** (Monday–Sunday), labelled `YYYY-Www` (e.g. `2026-W28`). The **default author is `$KALTI_AUTHOR`** (the invoker) — the report covers only that member's work unless `--all` is given.

| invocation | author | week |
|---|---|---|
| `/kalti-weekly` | me (`$KALTI_AUTHOR`) | current ISO week |
| `/kalti-weekly 2026-W28` | me | that week |
| `/kalti-weekly 2026-07-08` | me | the week containing that date |
| `/kalti-weekly 2026-W28 jinsik` | that member | that week |
| `/kalti-weekly --backfill 2026-W22..2026-W28` | me (or trailing member) | each week in range with entries |
| `/kalti-weekly --all [week]` | **whole lab (combined)** | that week (default: current) |

Compute the week's Monday–Sunday bounds. Derive the ISO week label with `date -d <date> +%G-W%V` (note `%G`, the ISO-week-year, not `%Y`). For `--backfill`, iterate the range and build only weeks with at least one entry — and **`log`/report which weeks were skipped as empty** so coverage is explicit.

Output paths:
- Personal (default / a named member): `reports/weekly/<author>/YYYY-Www.md`
- `--all` (whole lab): `reports/weekly/all/YYYY-Www.md`

## Gather the week's entries

Walk the journals **recursively** and select entries whose `date` frontmatter falls within the week's bounds (inclusive). **For the default/personal run, restrict to `journals/<author>/` only** — other members' folders are not read. For `--all`, read every author folder. Skip project-history files (`00-*.md`) — they are retrospectives, not week-dated work.

Prefer the **obsidian CLI** when present for accurate frontmatter reads; if `which obsidian` finds nothing (headless), read the files directly (graceful fallback — same result). For each selected entry, read: `project`, `type`, `title`, and the section bodies used below.

If **no** entries fall in the week, don't write an empty report — tell the user the week is empty and stop (for `--backfill`, just skip it).

## Classify into six buckets (reader-first)

Group the selected entries **domain → project** (a personal report is one member, so member headings are unnecessary; an `--all` report adds a member note per project). Pull each bucket from the entry's matching section — a one-liner in the report, detail stays in the journal:

| bucket | pulled from | notes |
|---|---|---|
| **진행·완료** (progress) | `한 일(방법)`, `type: build` | what was made/done |
| **발견·결과** (findings) | `결과/관찰`, `해석` (`experiment`·`investigation`) | values/observations as seen |
| **결정** (decisions) | `결정`, `type: decision` | what was decided and why |
| **막힌 점·이슈** (blockers) | `해석/막힌 점·해결` | failures & dead ends (so they aren't repeated) |
| **다음 주 계획** (next) | `다음 액션` | measurable next goals |
| **지식화 후보** (ontology candidates) | hypotheses/findings flagged in the body | feeds `/kalti-ontology` |

Every rendered item ends with a `[[YYYYMMDD-…]]` wikilink to the source journal (journal basenames are unique, so wikilinks are safe there). Omit empty buckets. The minimal core, if trimming, is 발견·결정·다음.

Domains are the recurring topic clusters (e.g. 메모리 시스템 / AI 에이전트 도구 / 금융·트레이딩 ML / ML 평가·검증 하네스 / 콘텐츠 생성 / 이미지 생성 / 연구방법론). Infer each project's domain from its work; when unsure, group by project alone.

## Write the report (idempotent)

Copy `assets/weekly-template.md` and fill it. **The report body is written in Korean** (the team's working language) — title, highlights, bucket items, and tables all in Korean. Shape:

- **Header** — title with week + author + period (e.g. `주간 보고 2026-W28 · sunghyun (07-06 ~ 07-12)`).
- **한 화면 TL;DR** — up to 3 highlight lines (the week's most important results/decisions, synthesized) + a per-project count table for this member. This is the only part you *summarize*; the buckets are *extracted*.
- **Body** — the domain → project → bucket structure above.
- **Tail** — 열린 다음 액션 (carry-over), 지식화 후보, then the prev/next + index footer (the footer regenerates too, so neighbor links stay current). The `## 📝 운영자 코멘트 / 메모` heading comes **last** and marks the preserve boundary: it and everything below it are hand-written and kept verbatim across runs.

**No HTML comments in the report.** Do not emit `<!-- … -->` anywhere — not as region markers, not as instructions. Authoring guidance lives in this SKILL, not in the output. The preserve boundary is the `## 📝 운영자 코멘트 / 메모` heading itself, not a comment marker.

**Links between weekly reports use relative markdown paths, NOT wikilinks.** Per-member folders mean several files share the basename `2026-W28.md`, so a `[[2026-W28]]` wikilink would be ambiguous. Use `[2026-W27](2026-W27.md)` for same-folder prev/next, and `[2026-W28](sunghyun/2026-W28.md)` from the index. (Journal links stay wikilinks — those basenames are unique.)

**Idempotency — running the same week repeatedly must not duplicate or clobber:**

1. **Deterministic path** — `reports/weekly/<author>/YYYY-Www.md`. Same author+week → same file, updated in place, never a `2026-W28 (1).md`. A personal run never touches another member's file or the `all/` report.
2. **Heading boundary (no markers, no comments)** — on re-run, regenerate everything from the top of the file down to — but **not** including — the `## 📝 운영자 코멘트 / 메모` heading, and preserve that heading and everything below it verbatim. If the heading is absent (new file), build the full template with an empty 운영자 코멘트 section at the end. The report never contains HTML comments.
3. **Deterministic ordering** — sort entries `date → project` (add `author` for `--all`) so the same journals produce byte-identical output. No new/changed journals → no diff.
4. **Index upsert** — update this report's row in `reports/weekly/README.md` (keyed by member+week) if present, else add it (newest first). Never append a duplicate row.
5. **Neighbor link refresh** — after writing, if the same member's adjacent-week report exists, update *its* footer link to point back here, so the per-member chain stays consistent.

Because the regenerated part is rebuilt from source each run, journal edits are picked up on the next run. Mid-week runs are partial and fill in as the week progresses — expected.

## After writing: sync with git

Honor `KALTI_GIT_SYNC` (unset → `ask`), scoping the commit to the report layer:

```
cd "$VAULT"
git add reports/
git commit -m "weekly: <author> <week label> 주간 보고"
git pull --rebase --autostash
git push          # only in push mode, or when the user chose push in ask mode
```

Modes: `push` / `commit` / `ask` (AskUserQuestion) / `off`. Handle no-remote / permission-blocked push / rebase conflict the graceful way the other skills do (the file is already saved; report the outcome in one line).

## What this skill touches (and what it leaves alone)

- Writes **only** under `reports/weekly/`. A default run **reads only the invoking author's** `journals/<author>/`; `--all` reads every member's journals to combine. It never edits journals or `ontology/`.
- It does not create ontology objects; it only **surfaces candidates** in the 지식화 후보 bucket for `/kalti-ontology`.
- It does not fix journal hygiene; if it notices problems while reading, mention them in the run summary rather than editing.
