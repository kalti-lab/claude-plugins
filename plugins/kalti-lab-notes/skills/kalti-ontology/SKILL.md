---
name: kalti-ontology
disable-model-invocation: true
description: "kalti 연구일지를 온톨로지(지식 그래프)로 정제하는 규약. journals/의 일지에서 가설·발견을 뽑아 ontology/에 6가지 객체(project·hypothesis·finding·concept·source·person)와 타입드 링크로 큐레이션한다. kalti 온톨로지 객체를 새로 만들거나, 일지를 정제·승격하거나, '온톨로지 정제'·'지식그래프 갱신'·'이번 주 일지 정제해줘'·'발견/가설 카드로 올려줘' 같은 요청 시 반드시 사용. 일지 작성(kalti-journal 스킬)이 증거를 남기는 쪽이라면 이건 그 증거를 지식으로 끌어올리는 쪽이다(다같이 관리). 근거 없는 객체를 만들지 않도록 일지 원문 인용으로 검증하는 게 핵심."
---

# kalti 온톨로지 정제

연구일지 시스템은 두 층이다.

- **일지 층 `journals/<이름>/`** — 각자 쓰는 작업 기록 = **증거**.
- **온톨로지 층 `ontology/`** — 일지에서 정제해 뽑은 "계속 살아있는 지식"을 객체로 만든 층. 그래프에 뜨는 의미 노드. **다같이 관리한다.**

이 스킬은 일지를 **온톨로지로 정제(큐레이션)**하는 쪽이다. 정제의 핵심은 "일지에 실제로 근거가 있는 결론만, 중복 없이" 객체로 끌어올리는 것 — 없는 사실을 만들면 그래프 전체의 신뢰가 깨진다.

## 어디서 작업하나 — 볼트 위치부터 잡기

전역 플러그인이라 **어느 디렉터리에서 호출되든** 동작하므로, 볼트(일지+온톨로지가 함께 있는 lab-notes 클론)의 루트를 **맨 먼저 확정**한다. 아래 `journals/`·`ontology/` 경로는 모두 이 루트(이하 `$VAULT`) 기준 절대경로다. 정하는 순서:

1. **환경변수**: `echo "$KALTI_VAULT"`로 확인. 값이 있고 그 안에 `journals/`·`ontology/`가 있으면 그걸 `$VAULT`로.
2. 없으면 **기본 경로** `~/dev/lab-notes`를 시도한다.
3. 둘 다 아니면 **사용자에게 한 번 묻고**, 다음부터 안 묻게 `export KALTI_VAULT=<경로>`를 셸 설정에 넣어두라고 안내한다.

(`ontology/`는 lab-notes 볼트에 `journals/`와 함께 있다 — clone하면 다같이 받는다.)

## 객체 타입 (6종)

| 타입 | 뜻 |
|---|---|
| `project` | 종목: 큰 연구 주제 |
| `hypothesis` | 가설: 검증 대상인 주장 |
| `finding` | 발견: 실험·조사에서 확인된 결론 |
| `concept` | 개념: 반복 등장하는 용어·기법 |
| `source` | 자료: 논문·문서·링크 |
| `person` | 사람: 참여자 |

## status (타입별)

- **project**: 진행 / 보류 / 완료 / 보관
- **hypothesis**: 제안 / 채택 / 기각 / 대체됨
- **finding · concept · source · person**: status 없음

가설은 살아 움직인다. 새 가설이 옛 가설을 갈음하면, 옛 가설 status를 `대체됨`으로 바꾸고 새 가설에서 `supersedes`로 옛 것을 가리킨다(지우지 않는다 — 이력이 곧 연구 서사다).

## id 규약

`타입약어-슬러그` (날짜·순번 금지): `proj-` / `hyp-` / `find-` / `con-` / `src-` / `per-`
예: `proj-image-pipeline`, `hyp-sampler`, `find-karras`, `con-nodes2`, `src-nodes2-doc`, `per-aram`

**링크는 파일 이름으로 건다(id 아님).** id는 frontmatter 안 고정 표지일 뿐, 위키링크 `[[ ]]`엔 노트의 파일 이름을 쓴다.

## 관계 링크 (타입드)

한 방향만 1번 적고, 반대 방향은 Obsidian 백링크로 본다(공통 허브 보일러플레이트를 피한다).

| 키 | 뜻 | 어느 글에 (출발) | 가리키는 대상 (도착) |
|---|---|---|---|
| `project` | ~에 속함 | 일지 | 종목 |
| `partOf` | ~에 속함 | 가설·발견 | 종목 |
| `tests` | ~를 검증함 | 실험 일지 | 가설 |
| `supersedes` | ~를 대체함 | 가설 | 가설 |
| `supports` / `refutes` | 뒷받침 / 반박 | 발견 | 가설 |
| `derivedFrom` | ~에서 나옴 | 발견 | 실험 일지 |
| `worksOn` | 참여함 | 사람 | 종목 |

## 타입별 필수칸

| 타입 | 필수칸 |
|---|---|
| project | id, title, type, status, tags |
| hypothesis | id, title, type, status, partOf (대체 시 supersedes) |
| finding | id, title, type, date, partOf, derivedFrom, (supports / refutes) |
| concept | id, title, type, tags |
| source | id, title, type, url |
| person | id, title, type, worksOn |

## 타입별 본문 틀 (요약)

- **project**: 목표 한 문단 + `## 현재 가설` + `## 실험` + `## 발견` + `## 참여`
- **hypothesis**: 가설 한 문장 + `## 상태`(값과 날짜) + `## 근거`
- **finding**: 결론 한 문장 + 메커니즘·근거 문단
- **concept**: 개념을 쉽게 3~5문장
- **source**: 무엇 · URL · 우리 연구에 쓸모
- **person**: 한 줄 소개 + `## 주로 보는 것`

각 객체를 실제로 만들 때 복사할 수 있는 전체 프론트매터+본문 블록은 **`references/object-templates.md`**에 있다. 객체를 생성하기 직전에 그 파일을 읽어 해당 타입 블록을 그대로 쓴다.

## 정제 (큐레이션) — 이 시스템의 심장

일지를 온톨로지로 끌어올리는 작업. **누구나** 할 수 있다 — 일지를 쓴 사람이 바로 객체로 올려도 되고, 정기적으로 모아서 해도 된다. 강제 게이트가 없는 만큼 **규율로 품질을 지킨다**: 근거 있는 것만, 중복 없이, 지우지 말고 고치기.

1. **입력**: 새로 쌓인 일지(+ 메모).
2. **AI 정제**: 일지에서 "아직 온톨로지에 없는 가설/발견 후보 + 링크"를 뽑게 한다(아래 프롬프트).
3. **반영**: 후보가 실제 일지에 근거하는지·중복 아닌지 확인하고 `ontology/`에 반영한다. 근거 없는 건 버린다.
4. **주기**: 정해진 건 없지만, 주 1회 몰아서 정제하면(주간 보고서 만들 때 같이) 빠짐없이 챙긴다.

### 재사용 정제 프롬프트

일지 → 온톨로지 후보를 뽑을 때 AI(서브에이전트 등)에 이렇게 시킨다:

```
journals/ 아래 각 멤버 폴더의 모든 일지와 ontology/의 기존 객체를 읽어라.
일지에는 결론·인사이트가 있는데 아직 온톨로지에 '발견(finding)'이나 '가설(hypothesis)'로
올라가지 않은 것을 찾아 후보로 제안하라.
- 이미 온톨로지에 있는 것은 다시 제안하지 마라.
- 각 후보는 근거가 된 일지 원문 문장을 그대로 인용하고(groundingQuote),
  derivedFrom으로 그 일지를 가리켜라.
- 없는 사실은 만들지 마라(일지에 적힌 결론만).
그다음 각 후보가 실제 그 일지에 근거하는지·중복 아닌지 검증해, 통과한 것만 남겨라.
```

통과한 후보만 `ontology/`에 파일로 만든다(`references/object-templates.md`의 블록 사용).

## 왜 두 층인가

일지는 증거, 온톨로지는 지식이다. 둘을 나눠 두면 — 최소한 일지만 써도 기여가 되고(부담 낮음), 정제를 거친 지식은 신뢰할 수 있으며, 그래프에서 관련된 것만 링크를 따라 정밀하게 뽑아낼 수 있어 AI에 줄 컨텍스트가 작고 정확해진다.

## 출처 (사람용 가이드의 근거)

- NIH — Best Practices for Keeping a Lab Notebook (2024)
- Harvard Medical School — Electronic Lab Notebooks
- UCSF McManus Lab — Notebook Guidelines
