# kalti-lab Claude Code 플러그인

kalti 연구실의 Claude Code 플러그인 마켓플레이스.

## kalti-lab-notes

연구일지 작성·온톨로지 정제 규약을 LLM에 주입하는 스킬 묶음.
- `kalti-setup` — 1회 셋업(볼트·본인 폴더·환경변수 자동, Obsidian CLI·kepano 스킬 안내)
- `kalti-journal` — 일지 작성 규약(증거 남기기, **파일 직접 쓰기**)
- `kalti-ontology` — 온톨로지 정제 규약(증거를 지식 객체로, 다같이; **그래프 탐색은 Obsidian CLI**)

### 설치
```
/plugin marketplace add kalti-lab/claude-plugins
/plugin install kalti-lab-notes@kalti-lab
```
설치 후 **한 번** `/kalti-setup`을 돌리면 볼트 위치·본인 폴더·환경변수가 잡힌다. 그다음부턴 **호출 위치는 자유** — 작업하던 코드·실험 폴더 어디서 `/kalti-journal`(일지)·`/kalti-ontology`(정제)를 불러도, **일지는 항상 셋업에서 지정한 `journals/<본인>/`에 저장**된다. (저장 위치가 자유로운 게 아니라, *부르는 곳*이 자유로운 것 — 연구 작업이 보통 볼트 밖에서 일어나므로 호출만 전역으로 푼 것이다.)

### 환경변수 (kalti-setup이 잡아줌)
스킬이 볼트와 본인 폴더를 찾는 순서:

- **`KALTI_VAULT`** — lab-notes 볼트(클론) 루트. 없으면 기본 `~/dev/lab-notes` → 그래도 없으면 물어봄.
- **`KALTI_AUTHOR`** — 본인 일지 폴더 핸들(예: `aram`). 없으면 `journals/`의 기존 폴더 중 고르게 함(추측 안 함).

`/kalti-setup`이 이 둘을 셸 설정에 영구화한다 — **zsh는 `~/.zshenv`**(비대화형 셸도 읽는 곳; `~/.zshrc`는 Claude Code가 스킬 돌릴 때 안 읽혀 무용). 수동으로 한다면 `~/.zshenv`에:
```
export KALTI_VAULT="$HOME/dev/lab-notes"
export KALTI_AUTHOR="aram"
```
볼트가 없으면 먼저 클론(또는 `/kalti-setup`이 대신 해줌):
```
git clone https://github.com/kalti-lab/lab-notes.git ~/dev/lab-notes
```

### Obsidian 공식 CLI (그래프 탐색·정제용, 권장)
온톨로지 정제·탐색은 Obsidian 공식 CLI로 그래프를 질의한다(`backlinks`·`unresolved`·`orphans`…) — grep보다 정확하고 토큰도 적다. **앱에 내장**돼 있어 플러그인이 아니라 GUI에서 켠다:

1. Obsidian 데스크톱 최신(1.12.4+)으로 업데이트
2. 설정 → General → **"Command line interface"** 켜기 → 안내대로 PATH 등록(터미널 재시작)

CLI는 켜져 있는 Obsidian 앱을 원격 조종한다(닫혀 있으면 첫 명령이 자동으로 띄움). 헤드리스 환경에선 정제 스킬이 파일 읽기로 fallback 한다. *일지 쓰기는 CLI를 쓰지 않고 파일을 직접 쓴다* — 앱 없이도 캡처되게.

### kepano obsidian-skills (필수)
Obsidian CLI 사용법과 Obsidian 문법(마크다운·Bases·Canvas)을 모델에 가르치는 **공식 스킬 묶음**(Obsidian CEO 제작). `/kalti-setup`이 설치를 요구하는 필수 구성요소다 — 다음 두 줄을 직접 실행한다:
```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```
(마켓플레이스 이름 `obsidian-skills`, 설치 플러그인 이름 `obsidian`.)

---
연구일지 볼트는 [`kalti-lab/lab-notes`](https://github.com/kalti-lab/lab-notes) — `journals/`(증거)와 `ontology/`(지식 그래프)가 한 볼트에 함께 있어 Obsidian 그래프로 이어 본다.
