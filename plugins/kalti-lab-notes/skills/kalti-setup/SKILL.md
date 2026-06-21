---
name: kalti-setup
disable-model-invocation: true
description: "kalti 연구일지 시스템을 처음 쓰기 전 1회 셋업. lab-notes 볼트 위치(KALTI_VAULT)와 본인 일지 폴더(KALTI_AUTHOR)를 잡아 설정 파일 ~/.config/kalti/notes.env에 박고, 볼트가 없으면 git clone하고 그 폴더를 Obsidian 앱에 볼트로 등록하며, 그래프 탐색용 Obsidian 공식 CLI와 kepano obsidian-skills 설치를 안내한다. /kalti-setup 으로 호출 — '셋업'·'처음 설정'·'볼트 연결해줘' 같은 요청이나, kalti-journal/kalti-ontology가 KALTI_VAULT·KALTI_AUTHOR 미설정으로 막혔을 때 사용. 이미 설정한 값을 잘못 박았거나 본인 폴더·볼트를 바꾸고 싶을 때 다시 호출하면 현재 값을 보여주고 고친다(재설정). 전역 플러그인이라 작업 디렉터리와 무관하게 동작한다."
---

# kalti 셋업 (1회)

하는 일은 단순하다 — 볼트 루트(`KALTI_VAULT`)와 본인 일지 폴더(`KALTI_AUTHOR`) 두 값을 알아내 `~/.config/kalti/notes.env`에 적어두는 것. 그러면 `/kalti-journal`·`/kalti-ontology`가 어느 폴더에서 불려도 이 파일을 읽어 볼트와 본인 폴더를 안다.

이건 연구 작업 자체가 아니라 그 **전에 한 번 하는 준비**라, 유저는 빨리 끝나길 바란다. 그러니 확실한 건 합리적 기본값으로 그냥 처리하고, 정말 사람만 아는 것(새 폴더 이름 등)만 물은 뒤, 끝에 한 일과 확정값을 짧게 요약하면 충분하다. 단계마다 이유를 늘어놓을수록 준비가 길어져 본 작업이 밀린다.

## 호출되면 맨 먼저: 신규냐, 이미 설정돼 있냐

`/kalti-setup`은 유저가 일부러 친다. 이미 설정된 상태에서 또 불렀다면 보통 **뭔가 고치려는** 신호다. 그래서 `. ~/.config/kalti/notes.env 2>/dev/null`로 현재 값을 먼저 읽고 상황에 맞춰 간다:

- **파일이 없거나 비었으면** — 신규다. 아래 "볼트" → "본인 폴더" → "영구화" 순서로.
- **값이 있는데 가리키는 곳이 깨졌으면**(`$KALTI_VAULT`에 `journals/`가 없거나 `$VAULT/journals/$KALTI_AUTHOR/`가 사라짐) — 뭐가 어긋났는지 한 줄로 알리고 그 항목만 해당 섹션으로 다시 잡는다. 유저가 고치러 온 거니, 여기서 "이미 설정됨"이라며 끝내면 헛걸음이 된다.
- **값이 멀쩡하면** — 현재 `KALTI_VAULT`·`KALTI_AUTHOR`를 보여주고 무엇을 할지 고르게 한다(AskUserQuestion): ① 그대로 둔다 ② 본인 폴더 바꾸기 ③ 볼트 바꾸기 ④ 처음부터. 바꾸기를 골랐다면 그 값이 지금 유효하더라도 새로 고르게 한다 — 바꾸러 온 사람에게 기존 값을 다시 들이밀면 목적과 어긋난다. 고른 뒤 "영구화"로 `notes.env`를 덮어쓴다.

## 볼트 (`KALTI_VAULT`)

볼트는 아래 세 단계로 충분히 찾는다 — 순서대로 내려가다 처음 걸리는 데서 멈춘다. 파일시스템을 넓게 뒤지는 길(예: `find ~/dev`)은 피하는 게 좋다. 유저가 예상 못 한 곳을 긁으면 느리고 놀라운 데다, 같은 답을 사람한테 물으면 1초면 나오기 때문이다.

1. `notes.env`의 `$KALTI_VAULT`가 유효하면(그 안에 `journals/`) 그걸로 끝.
2. 아니면 **현재 폴더나 바로 위 한두 단계**에 `journals/`+`ontology/`가 같이 있나 본다 — 있으면 클론 안에서 부른 것이니 그게 볼트다. 그대로 쓴다.
3. 그래도 못 찾으면, 이 시점엔 유저가 제일 빠른 답이다. AskUserQuestion으로 두 갈래를 준다:
   1. **현재 폴더에 셋팅** — 여기(`<pwd>`)에 `git clone https://github.com/kalti-lab/lab-notes.git`로 받아 쓴다
   2. **지정 경로 있어?** — "기타(직접 입력)"로 경로를 받는다(이미 볼트가 있으면 그 경로, 없으면 거기에 clone)

## 본인 폴더 (`KALTI_AUTHOR`)

볼트를 잡았으면 본인 일지 폴더를 정한다. 이름은 **실재하는 폴더에서 고르게** 하는 게 안전하다 — 추측해서 만들면 오타 하나로 엉뚱한 폴더(`journals/Aram/` 같은)가 생겨 일지가 둘로 흩어진다.

1. `$KALTI_AUTHOR`가 이미 `$VAULT/journals/`에 실재하면 그걸로.
2. 아니면 `journals/`의 폴더 목록을 AskUserQuestion으로 고르게 한다.
3. "새로 만들기"를 고르면 폴더 이름 하나만 받아(`폴더 이름 뭘로 할까?`) `mkdir -p "$VAULT/journals/<이름>"`로 만든다.

## 영구화

확정한 두 값을 `~/.config/kalti/notes.env`에 적는다. 셸 설정(`~/.zshrc`·`~/.zshenv`)은 손대지 않는다 — 스킬이 호출 때마다 이 파일을 직접 읽으니 셸 환경에 기댈 필요가 없고, 덕분에 비대화형 셸이 rc를 안 읽어 생기던 문제도 사라진다. 파일은 통째로 새로 쓰면 된다(기존 값이 있으면 그대로 갈음):
```
mkdir -p ~/.config/kalti
cat > ~/.config/kalti/notes.env <<EOF
KALTI_VAULT=<경로>
KALTI_AUTHOR=<이름>
EOF
```
(인프라 시크릿이 든 `~/.kalti/`와는 다른 경로다.)

## Obsidian에 볼트 등록

`notes.env`를 써도 그건 kalti 쪽 설정일 뿐, **Obsidian 앱은 그 폴더가 볼트인 줄 모른다.** 그래서 등록 단계가 없으면 유저가 Obsidian을 열어도 lab-notes가 안 보인다(이번에 빠졌던 부분). 사람이 그래프를 보고 정제 때 CLI도 동작하려면, 클론했거나 Obsidian이 아직 모르는 볼트는 앱의 볼트 목록(`obsidian.json`)에 넣어줘야 한다.

이 등록은 번들 스크립트로 안전하게 한다(멱등·원자적 쓰기·OS별 경로 처리):
```
python3 <이 스킬 경로>/scripts/register_obsidian_vault.py "$VAULT"
```
`ALREADY_REGISTERED`(이미 있음)·`REGISTERED`(새로 더함) 중 하나를 찍는다. 이미 클론 안에서 셋업해 등록돼 있으면 조용히 넘어간다.

단, **타이밍이 중요하다.** Obsidian은 실행 중에 종료할 때 `obsidian.json`을 제 상태로 다시 써서 방금 더한 항목을 지울 수 있다. 그래서 `pgrep -x Obsidian`로 먼저 본다:

- **꺼져 있으면** — 스크립트를 돌린다. 다음에 Obsidian을 열면 볼트 목록에 뜬다.
- **떠 있으면** — 종료 때 덮어써져 날아갈 수 있으니, 유저에게 한 번만 직접 등록하도록 안내하는 게 확실하다: Obsidian 좌하단 볼트 아이콘 → '다른 볼트 열기' → '폴더를 볼트로 열기'에서 `$VAULT` 선택. (Obsidian을 잠깐 끄고 이 단계를 다시 돌려도 된다.)

요약에 "Obsidian에서 lab-notes 볼트를 열면 그래프가 보인다"를 한 줄 남긴다.

## Obsidian CLI

`which obsidian`으로 있는지만 본다. 있으면 그냥 넘어가고, 없으면 요약에 한 줄 곁들인다: "설정 → General → Command line interface를 켜면 온톨로지 정제 때 그래프 탐색이 빨라진다(없어도 파일 읽기로 동작)."

## kepano obsidian-skills (필수)

Obsidian 문법과 CLI 사용법을 모델에 가르치는 공식 스킬 묶음이라, 이게 깔려 있어야 정제 단계가 제대로 돈다 — 셋업의 필수 구성요소다. 아직 없으면 유저에게 다음 두 줄을 직접 실행해 달라고 분명히 청한다(`/plugin`은 모델이 칠 수 없다):
```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```
요약에서도 "kepano까지 깔아야 셋업 완료"임을 분명히 남겨, 유저가 빠뜨리지 않게 한다.

## 끝나면

확정값(`KALTI_VAULT`·`KALTI_AUTHOR`)과 한 일(폴더 생성 / `notes.env` 작성 / Obsidian 볼트 등록 / kepano 설치 여부)을 짧게 보여준다.

그리고 이제 쓸 수 있게 된 두 스킬이 각각 뭔지 **한 줄씩 쉬운 말로** 알려준다 — 유저는 방금 셋업만 끝낸 참이라 이게 뭘 하는 건지 모르는 경우가 많고, 이름만 던지면 결국 안 쓰게 되기 때문이다:

- **`/kalti-journal`** — 연구하다 한 일을 **연구일지로 남기는** 스킬. "방금 한 거 일지로 남겨줘" 하면 본인 폴더(`journals/<본인>/`)에 형식 맞춰 기록한다(증거 남기기).
- **`/kalti-ontology`** — 쌓인 일지에서 **가설·발견을 뽑아 지식 그래프로 정제**하는 스킬(주로 모아서 정리할 때). 일지가 "증거"라면 이건 그걸 "지식"으로 끌어올리는 쪽이다.

둘 다 어느 폴더에서 불러도 방금 저장한 설정을 읽어 동작한다는 점을 한마디 곁들여 닫는다.

(이 셋업은 시크릿을 다룰 일이 없다 — 토큰이나 `~/.kalti/`의 인프라 키를 혹시 마주쳐도 화면에 찍거나 옮기지 않고 그대로 둔다.)
