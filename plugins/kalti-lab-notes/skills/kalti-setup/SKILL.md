---
name: kalti-setup
disable-model-invocation: true
description: "kalti 연구일지 시스템을 처음 쓰기 전 1회 셋업. lab-notes 볼트 위치(KALTI_VAULT)와 본인 일지 폴더(KALTI_AUTHOR)를 잡아 셸 설정에 영구화하고, 볼트가 없으면 git clone하며, 그래프 탐색용 Obsidian 공식 CLI 활성화와 kepano obsidian-skills 플러그인 설치를 안내한다. /kalti-setup 으로 호출 — '셋업'·'처음 설정'·'환경변수 잡아줘'·'볼트 연결해줘' 같은 요청이나, kalti-journal/kalti-ontology가 KALTI_VAULT·KALTI_AUTHOR 미설정으로 막혔을 때 반드시 사용. 전역 플러그인이라 작업 디렉터리와 무관하게 동작한다."
---

# kalti 셋업 (1회)

연구일지 플러그인을 깐 뒤 **한 번** 돌리는 온보딩. 끝나면 어느 작업 폴더에서든 `/kalti-journal`(일지)·`/kalti-ontology`(정제)가 바로 동작한다. 사용자가 답할 것만 묻고(핑퐁), 나머지는 직접 처리한다.

**자동으로 하는 것**: 볼트 위치(`KALTI_VAULT`)·본인 폴더(`KALTI_AUTHOR`) 확정 → 셸 설정에 영구화, 볼트 없으면 clone.
**안내만 하는 것(직접 실행 불가)**: Obsidian 공식 CLI 켜기(앱 GUI 토글), kepano obsidian-skills 설치(`/plugin` 명령은 모델이 못 침).

파괴적이거나 사용자 환경을 바꾸는 단계(셸 설정 편집, git clone)는 **실행 전에 무엇을 할지 보여주고 확인**받는다.

## 1단계 — 볼트 위치 (`KALTI_VAULT`)

lab-notes 볼트(일지+온톨로지가 함께 있는 git 클론)의 루트를 정한다. 순서:

1. `echo "$KALTI_VAULT"` — 값이 있고 그 안에 `journals/`가 있으면 그대로 확정.
2. 없으면 기본 경로 `~/dev/lab-notes`에 `journals/`가 있는지 확인 → 있으면 그걸로.
3. 둘 다 아니면 **AskUserQuestion**으로 묻는다: 「볼트를 새로 clone / 이미 있는데 경로 다름(직접 입력) / 취소」.
   - **clone**: 위치를 확인받고(기본 `~/dev/lab-notes`) `git clone https://github.com/kalti-lab/lab-notes.git <경로>` 실행.
   - **경로 다름**: 사용자가 준 경로에 `journals/`가 있는지 검증.

확정한 절대경로를 `$VAULT`로 삼는다.

## 2단계 — 본인 일지 폴더 (`KALTI_AUTHOR`)

"내 폴더가 어디냐"를 추측하지 않는다(추측하면 오타로 `journals/Aram/` 같은 새 폴더를 파버린다). 순서:

1. `echo "$KALTI_AUTHOR"` — 값이 있고 `$VAULT/journals/<값>/`이 실재하면 그대로 확정.
2. 없으면 `$VAULT/journals/`의 **기존 폴더 목록**을 뽑아(`ls`) **AskUserQuestion**으로 고르게 한다 — 선택지엔 기존 폴더들을, 그리고 "기타(직접 입력)"로 **새 폴더(=새 멤버)** 를 만들 수 있게.
3. 새 폴더를 고르면 핸들(영문 소문자 권장, 예: `aram`)을 받아 `mkdir -p "$VAULT/journals/<핸들>"`.

확정한 핸들을 `$AUTHOR`로 삼는다.

## 3단계 — 셸 설정에 영구화 (다음부턴 안 묻게)

`$KALTI_VAULT`·`$KALTI_AUTHOR`를 셸 시작 파일에 넣어 매 세션 자동 적용시킨다.

1. 셸 판별: `$SHELL` 보고 zsh면 `~/.zshrc`, bash면 `~/.bashrc`(macOS 로그인셸이면 `~/.bash_profile`). 기본은 zsh.
2. **멱등하게**: 먼저 `grep -n 'KALTI_VAULT\|KALTI_AUTHOR' <rc파일>`로 기존 줄을 확인한다.
   - 같은 값이 이미 있으면 건드리지 않는다.
   - 다른 값이 있으면 **덮어쓰지 말고** 사용자에게 보여주고 어떻게 할지 확인.
   - 없으면 아래 블록을 **편집 내용 보여준 뒤 확인받고** 추가:
     ```
     # kalti 연구일지
     export KALTI_VAULT="<경로>"
     export KALTI_AUTHOR="<핸들>"
     ```
3. 추가 후, 이번 세션에도 즉시 적용되도록 사용자에게 `source <rc파일>`(또는 새 터미널)을 안내한다. (이 스킬이 띄운 셸에 export 해봤자 사용자 셸엔 안 남으므로, rc 편집이 핵심이다.)

## 4단계 — Obsidian 공식 CLI (그래프 탐색용)

온톨로지 정제·탐색(`kalti-ontology`)은 Obsidian 공식 CLI로 그래프를 질의한다(backlinks·unresolved·orphans 등). 이건 **Obsidian 앱에 내장**돼 있고 **플러그인이 아니다** — 앱 GUI에서 켜야 한다(스크립트로 못 켬).

1. `which obsidian` — 나오면 이미 활성. `cd "$VAULT" && obsidian vault info=name`로 동작 확인하고 4단계 끝.
2. 안 나오면 **안내**(직접 실행 불가):
   - Obsidian을 최신(데스크톱 1.12.4+)으로 업데이트.
   - **설정 → General → "Command line interface" 켜기** → 안내대로 PATH 등록(macOS는 `/usr/local/bin/obsidian` 심링크, admin 권한). 터미널 재시작.
   - CLI는 **켜져 있는 Obsidian 앱을 원격 조종**한다(닫혀 있으면 첫 명령이 앱을 띄움). 헤드리스 서버에선 동작 안 함 — 그 경우 정제 스킬이 파일 읽기로 fallback 하니 셋업은 계속 진행해도 된다.

## 5단계 — kepano obsidian-skills 플러그인 (선택, 권장)

Obsidian CLI 사용법과 Obsidian 문법(마크다운·Bases·Canvas)을 모델에 더 풍부하게 가르치는 **공식 스킬 묶음**(Obsidian CEO 제작). 우리 `kalti-ontology`에 핵심 CLI 명령은 이미 들어 있어 없어도 동작하지만, 더 폭넓은 Obsidian 작업엔 이게 낫다.

`/plugin` 명령은 모델이 대신 못 치므로 **사용자가 직접 실행**하게 두 줄을 안내한다:

```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```

(마켓플레이스 이름은 `obsidian-skills`, 설치되는 플러그인 이름은 `obsidian`이다 — `obsidian@obsidian-skills` 형식.)

## 6단계 — 요약·검증

마지막에 확정값을 한눈에 보여준다:
- `KALTI_VAULT` = `<경로>` (clone했으면 그 사실도)
- `KALTI_AUTHOR` = `<핸들>` (새로 만들었으면 그 사실도)
- 셸 설정 영구화: 됨/건너뜀 + `source` 안내
- Obsidian CLI: 활성/안내함
- kepano 스킬: 안내함

그리고 다음 한 줄로 닫는다: 「이제 아무 작업 폴더에서 `/kalti-journal`로 일지를, `/kalti-ontology`로 정제를 호출하면 된다.」

## 하지 말 것

- 셸 설정·기존 파일을 **확인 없이** 덮어쓰지 않는다.
- 본인 폴더를 추측해 새로 파지 않는다(반드시 묻고 만든다).
- `/plugin`·Obsidian GUI 토글을 "실행했다"고 말하지 않는다 — 이건 안내만 가능하다.
- 실제 계정·시크릿(토큰 등)을 다루지 않는다 — 이 셋업은 경로·핸들·환경변수만 만진다.
