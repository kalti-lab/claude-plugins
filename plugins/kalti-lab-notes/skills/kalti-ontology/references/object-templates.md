# 온톨로지 객체 템플릿

`ontology/`에 객체를 만들 때 쓴다. 링크는 **파일 이름**으로 건다. id는 frontmatter 안에서만 쓰고 링크에는 쓰지 않는다. `#` 주석은 실제 파일에서 지운다.

## 종목 (project)

```markdown
---
id: proj-
title:
type: project
status: 진행      # 진행 / 보류 / 완료 / 보관
tags: []
---

# (제목)

(이 종목이 무엇을 목표로 하는지 한 문단)

## 현재 가설
- [[(가설 노트 이름)]]

## 실험
- [[(실험 일지 이름)]]

## 발견
- [[(발견 노트 이름)]]

## 참여
- [[(사람 노트 이름)]]
```

## 가설 (hypothesis)

```markdown
---
id: hyp-
title:
type: hypothesis
status: 제안      # 제안 / 채택 / 기각 / 대체됨
partOf: "[[(종목 노트 이름)]]"
# supersedes: "[[(옛 가설 노트 이름)]]"   # 대체하면
tags: []
---

# (제목)

(가설을 한 문장으로)

## 상태
제안 (YYYY-MM-DD)

## 근거
(어느 실험·발견이 근거인지)
```

## 발견 (finding)

```markdown
---
id: find-
title:
type: finding
date:             # YYYY-MM-DD
partOf: "[[(종목 노트 이름)]]"
derivedFrom: "[[(실험 일지 이름)]]"
# supports: "[[(가설 노트 이름)]]"   # 뒷받침하면
# refutes: "[[(가설 노트 이름)]]"    # 반박하면
tags: []
---

# (제목)

(결론을 한 문장으로)

(메커니즘·근거 문단)
```

## 개념 (concept)

```markdown
---
id: con-
title:
type: concept
tags: []
---

# (제목)

(이 개념이 무엇인지 쉽게 3~5문장. 우리 연구에서 왜 중요한지)
```

## 자료 (source)

```markdown
---
id: src-
title:
type: source
url:
tags: []
---

# (제목)

(무엇인지 + 어디서 보는지(URL) + 우리 연구에 어떤 대목이 쓸모인지)
```

## 사람 (person)

```markdown
---
id: per-
title:
type: person
worksOn: "[[(종목 노트 이름)]]"
tags: []
---

# (제목)

(한 줄 소개)

## 주로 보는 것
-
```
