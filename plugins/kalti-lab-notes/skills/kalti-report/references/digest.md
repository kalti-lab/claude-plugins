# kalti report — digest mode (월간 연구실 소식)

A monthly two-page newspaper covering **the whole lab**, written once per month into
`$VAULT/reports/digest/YYYY-MM.html`. The weekly report is one member's map of their own week;
this is the one place all three members' work shares a page. It exists because the members do not
read each other's journals — measured: 2 cross-citations in 280 journals, while 4 of 10 concept
cards join all three people. They reach the same conclusions without knowing it.

**The test an issue must pass:** a member reads it and learns something they did not know,
especially from someone else's project. The August 창간호 was written by hand first to fix this
format — the issue *is* the spec, the same way weekly was skillified from a hand-made W28.

`/kalti-report --digest` builds last month; `--digest 2026-09` builds that month. Nothing else to
ask. Re-running **overwrites the whole file** — unlike weekly there is no hand-written region to
preserve (grounds: all 44 weekly reports' operator-comment sections went unused).

## Step 1 — every number comes from one command

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kalti-report/scripts/count.py" "$VAULT" --digest YYYY-MM
```

It prints the five headline figures, the project ranking, what got overturned (with what replaced
it, resolved through `supersedes`/`refutes` back-links), the month's contrib triple per member,
and next-issue candidates. **Never count by hand or by ad-hoc grep** — contrib's rule, same
reason: the numbers must come out identical run to run. Settlement dates are read from frontmatter
(`closed:` on hypotheses, `reversed:` on decisions), never scraped from body prose — a drifted
prose line is silently skipped, which is worse than a wrong count.

If the script errors or a figure looks impossible (e.g. 결론 난 생각 0 in an active month), stop
and say so rather than writing an issue around it.

## Step 2 — choose, in this order

1. **이달의 연구** — rank 1 of the project ranking. On a tie, prefer the project whose *question*
   got answered over one that shipped work: a study whose existential question settled (and
   especially one whose answer contradicted the intuition) leads the page. Say the tie-break in
   the run summary.
2. **2면 기사 4개** — ranks 2–5. Everything else folds into the 그 외 N개 line; if a folded
   project looks anomalous (most journals of the month but few cards), explain it in one line —
   readers will notice.
3. **한 줄 인용** — one verbatim sentence **from a journal body** of that month. Never from a
   weekly report: reports are derived, and a summary of a summary cannot carry grounding. Pick the
   sentence that best supports the month's lead *and* stands alone without context.
4. **예상이 빗나간 것** — the script's 기각·대체됨·번복됨 rows, restated in plain words.

## Step 3 — fill the template

Copy `${CLAUDE_PLUGIN_ROOT}/skills/kalti-report/assets/digest-template.html` and fill every
`{{ }}` slot. The layout is fixed — **never edit the CSS or the structure per issue**; issues must
look identical month to month so they can sit side by side. Design changes go to
`assets/digest.css` / the template, once, and past issues get re-exported.

Length caps, measured against the page (**counted with spaces**; these are the only overflow check
there is, since the issue is written without a browser):

| slot | cap |
|---|---|
| 제호 아래 그 달 문단 | 150자 |
| 이달의 연구 부제 | 130자 |
| 이달의 연구 본문 | 950자 (two-column capacity measured at 983) |
| 2면 기사 | 3–4 bullets each, 4 articles |
| 다음 호 예고 | 5 lines, only items carrying a date or number |

Writing rules that already bit once, so they are rules:

- **`${CLAUDE_PLUGIN_ROOT}/shared/writing.md` applies to every sentence.** Card names carrying
  stiff words are *not* copied into the paper — there are no wikilinks in HTML, so there is no
  reason to keep a name's wording; say it plainly.
- Headlines state what changed, not what was done. The lead's deck ends with the answer, and the
  `<b>` span in it gets the highlight bar.
- 기여 shows 연구노트 · 카드 · 밀도 per member with bars scaled to each column's max — **no total,
  no rank, no winner** (contrib's rule). Note the retro exclusion when it makes the 일지 figure
  disagree.
- 호수: 창간호, then 제2호, 제3호 … — count existing `YYYY-MM.html` files.

## Step 4 — export self-contained and register

1. Replace the template's `<link rel="stylesheet" href="digest.css">` with an inline
   `<style>…the full content of assets/digest.css…</style>` so the issue renders correctly
   anywhere on its own. The vault keeps **only** `README.md` and the issues — no css, no template.
2. Write to `$VAULT/reports/digest/YYYY-MM.html`.
3. Add the issue's row to the **지난 호** table in `$VAULT/reports/digest/README.md` — title line
   plus a `file://` open link like the existing rows.

## Step 4.5 — 발행 전 말 다듬기 패스 (서브에이전트)

소식을 만드는 턴은 집계·템플릿·글자 수 상한을 동시에 다루느라 낱말에 쓸 주의가
안 남는다 — 낱말 규칙이 세 겹으로 있어도 8월호 초안에서 18개가 걸린 이유다.
그래서 발행 직전에 **교정만 하는 서브에이전트**를 하나 띄운다. 프롬프트에는 딱
세 가지만 준다: 완성된 HTML 경로, `${CLAUDE_PLUGIN_ROOT}/skills/korean-polish/SKILL.md`
경로, 그리고 "HTML은 글자만 고치고 태그·구조는 건드리지 말 것". 소식 내용이나
집계 문맥은 주지 않는다 — 격리가 목적이다. 에이전트가 돌아오면 글자 수 상한
(Step 3의 표)을 다시 세고, 새로 걸린 낱말은 실행 요약에 옮겨 적는다.

## Step 5 — verify before reporting done

- Count every capped slot (spaces included) and state the counts in the run summary.
- Re-print the five headline figures from the script output verbatim — if what landed in the HTML
  differs, that is a defect, not a rounding choice.
- If a browser is available, open the file and check both `.sheet`s for overflow
  (`scrollHeight > clientHeight`); if not, say the check was cap-only.

Git scope stays `git add reports/` with message `digest: YYYY-MM 소식`. Digest never edits
`journals/` or `ontology/` — anything it notices wrong there goes in the run summary for
`/kalti-ontology` or the author.
