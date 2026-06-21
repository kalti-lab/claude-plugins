---
name: kalti-setup
disable-model-invocation: true
description: "kalti 연구일지 시스템을 처음 쓰기 전 1회 셋업. lab-notes 볼트 위치(KALTI_VAULT)와 본인 일지 폴더(KALTI_AUTHOR)를 잡아 설정 파일 ~/.config/kalti/notes.env에 박고, 볼트가 없으면 git clone하며, 그래프 탐색용 Obsidian 공식 CLI와 kepano obsidian-skills 설치를 안내한다. /kalti-setup 으로 호출 — '셋업'·'처음 설정'·'볼트 연결해줘' 같은 요청이나, kalti-journal/kalti-ontology가 KALTI_VAULT·KALTI_AUTHOR 미설정으로 막혔을 때 사용. 전역 플러그인이라 작업 디렉터리와 무관하게 동작한다."
---

# kalti 셋업 (1회)

`KALTI_VAULT`(볼트 루트)와 `KALTI_AUTHOR`(본인 일지 폴더 이름) 두 값을 잡아 설정 파일 `~/.config/kalti/notes.env`에 박는 게 전부다.

**조용히 실행한다.** 단계마다 이유·과정을 늘어놓거나 사소한 걸 재확인하지 말 것. 꼭 필요한 것만 묻고(예: 새 폴더 이름) 나머지는 그냥 하고, 끝나면 짧게 요약한다.

## 볼트 (`KALTI_VAULT`)

1. `~/.config/kalti/notes.env`의 `$KALTI_VAULT`에 값이 있고 그 안에 `journals/`가 있으면 그걸로.
2. 없으면 **현재 폴더(또는 상위 디렉터리)**에 `journals/`+`ontology/`가 있는지 본다 — 있으면 그게 볼트다(이미 클론 안에서 실행한 경우). 안 묻고 그대로 쓴다.
3. 그래도 없으면 `~/dev/lab-notes`가 실재하는지 **조용히** 확인(README 권장 경로). 있으면 그걸로.
4. 끝까지 없으면 — 볼트를 새로 받아야 하니 — AskUserQuestion으로 **어디에 받을지** 묻는다. 이때 임의 경로(`~/dev/lab-notes`)를 라벨로 들이밀지 말고, **사용자가 지금 보는 위치 기준으로 구체적으로** 제시한다:
   - **여기에 받기** — 라벨에 실제 경로를 박아서: 예) "여기에 받기 (`<pwd>/lab-notes`)"
   - **직접 지정** — "기타(직접 입력)"로 경로를 받는다

   받기로 하면 `git clone https://github.com/kalti-lab/lab-notes.git <고른 경로>`.

`~/dev/lab-notes` 기본값을 **선택지 라벨로 보여주지 않는다** — 그 폴더가 없는 새 유저에겐 뜬금없다. 기본값은 3번의 *조용한 존재 확인*으로만 쓴다.

## 본인 폴더 (`KALTI_AUTHOR`)

1. `$KALTI_AUTHOR` 폴더가 `$VAULT/journals/`에 실재하면 그걸로.
2. 없으면 `journals/`의 폴더 목록을 AskUserQuestion으로 고르게 한다.
3. **"새로 만들기"를 고르면 폴더 이름만 묻고("폴더 이름 뭘로 할까?") 바로 `mkdir -p "$VAULT/journals/<이름>"`.** 설명 붙이지 말 것.

## 영구화

확정한 두 값을 **`~/.config/kalti/notes.env`** 한 파일에 적는다 — 셸 설정(`~/.zshrc`·`~/.zshenv`)은 안 건드린다. 스킬이 매번 이 파일을 직접 읽으므로 비대화형 셸 source 문제도 없다. 디렉터리 만들고 파일을 **통째로 덮어쓴다**(멱등 신경 X):
```
mkdir -p ~/.config/kalti
cat > ~/.config/kalti/notes.env <<EOF
KALTI_VAULT=<경로>
KALTI_AUTHOR=<이름>
EOF
```
`/kalti-journal`·`/kalti-ontology`는 호출될 때 `. ~/.config/kalti/notes.env`로 이 값을 읽는다 — 그래서 **어느 폴더에서 불러도** 볼트·본인 폴더를 안다. (시크릿이 든 `~/.kalti/`와는 다른 경로다.) source 안내 같은 건 필요 없다.

## Obsidian CLI (선택)

`which obsidian` 있으면 아무 말 없이 넘어간다. 없으면 요약에 한 줄: "설정 → General → Command line interface 켜면 정제 탐색이 빨라진다(없어도 파일 읽기로 동작)."

## kepano obsidian-skills (필수)

선택이 아니라 셋업의 **필수 단계**다. 이미 깔려 있지 않으면, 사용자에게 **지금 이 두 줄을 직접 실행하라고** 명확히 요청한다(`/plugin`은 모델이 못 치므로):
```
/plugin marketplace add kepano/obsidian-skills
/plugin install obsidian@obsidian-skills
```
이걸 안 깔면 셋업이 끝난 게 아니다 — 요약에서 "kepano 설치까지 해야 완료"임을 분명히 하고, 사용자가 실행할 때까지 그 점을 흐리지 말 것.

## 끝나면

확정값(`KALTI_VAULT`·`KALTI_AUTHOR`)과 한 일(폴더 생성 / `notes.env` 작성)만 짧게 보여주고 "이제 `/kalti-journal`·`/kalti-ontology` 쓰면 된다"로 닫는다.

## 하지 말 것

- 군더더기 설명·재확인. 본인 폴더를 추측해 만들기(반드시 묻고). 시크릿(토큰 등) 취급.
