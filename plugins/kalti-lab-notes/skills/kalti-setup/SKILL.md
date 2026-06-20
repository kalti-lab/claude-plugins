---
name: kalti-setup
disable-model-invocation: true
description: "kalti 연구일지 시스템을 처음 쓰기 전 1회 셋업. lab-notes 볼트 위치(KALTI_VAULT)와 본인 일지 폴더(KALTI_AUTHOR)를 잡아 셸 설정에 영구화하고, 볼트가 없으면 git clone하며, 그래프 탐색용 Obsidian 공식 CLI와 kepano obsidian-skills 설치를 안내한다. /kalti-setup 으로 호출 — '셋업'·'처음 설정'·'환경변수 잡아줘'·'볼트 연결해줘' 같은 요청이나, kalti-journal/kalti-ontology가 KALTI_VAULT·KALTI_AUTHOR 미설정으로 막혔을 때 사용. 전역 플러그인이라 작업 디렉터리와 무관하게 동작한다."
---

# kalti 셋업 (1회)

`KALTI_VAULT`(볼트 루트)와 `KALTI_AUTHOR`(본인 일지 폴더 핸들) 두 값을 잡아 셸 설정에 박는 게 전부다.

**조용히 실행한다.** 단계마다 이유·과정을 늘어놓거나 사소한 걸 재확인하지 말 것. 꼭 필요한 것만 묻고(예: 새 폴더 이름) 나머지는 그냥 하고, 끝나면 짧게 요약한다.

## 볼트 (`KALTI_VAULT`)

1. `$KALTI_VAULT` 안에 `journals/`가 있으면 그걸로.
2. 없으면 `~/dev/lab-notes`를 시도.
3. 그것도 없으면 한 번 묻는다(경로 직접 / clone). clone은 `git clone https://github.com/kalti-lab/lab-notes.git <경로>`.

## 본인 폴더 (`KALTI_AUTHOR`)

1. `$KALTI_AUTHOR` 폴더가 `$VAULT/journals/`에 실재하면 그걸로.
2. 없으면 `journals/`의 폴더 목록을 AskUserQuestion으로 고르게 한다.
3. **"새로 만들기"를 고르면 핸들만 묻고 바로 `mkdir -p "$VAULT/journals/<핸들>"`.** 설명 붙이지 말 것.

## 영구화

`~/.zshrc`(zsh / bash면 `~/.bashrc`)에 아래 두 줄을 **멱등하게** 추가한다 — 같은 값이 이미 있으면 건너뛰고, 값이 다르면 그때만 사용자에게 알린다. 큰 블록을 펼쳐 보이거나 다시 확인받지 말고 그냥 추가한다.
```
export KALTI_VAULT="<경로>"
export KALTI_AUTHOR="<핸들>"
```
(이 스킬이 띄운 셸의 export는 사용자 셸에 안 남으므로 rc 편집이 핵심. 요약에서 `source ~/.zshrc` 한 줄만 안내.)

## Obsidian CLI · kepano (둘 다 선택)

- `which obsidian` 있으면 아무 말 없이 넘어간다. 없으면 요약에 한 줄: "설정 → General → Command line interface 켜면 정제 탐색이 빨라진다(없어도 파일 읽기로 동작)."
- kepano 스킬은 요약에 한 줄만: 더 풍부한 Obsidian 작업 원하면 `/plugin marketplace add kepano/obsidian-skills` → `/plugin install obsidian@obsidian-skills` (사용자가 직접 — `/plugin`은 모델이 못 침).

## 끝나면

확정값(`KALTI_VAULT`·`KALTI_AUTHOR`)과 한 일(폴더 생성/ rc 추가)만 짧게 보여주고 "이제 `/kalti-journal`·`/kalti-ontology` 쓰면 된다"로 닫는다.

## 하지 말 것

- 군더더기 설명·재확인. 본인 폴더를 추측해 만들기(반드시 묻고). 시크릿(토큰 등) 취급.
