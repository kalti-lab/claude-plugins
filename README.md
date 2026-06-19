# kalti-lab Claude Code 플러그인

kalti 연구실의 Claude Code 플러그인 마켓플레이스.

## kalti-lab-notes

연구일지 작성·온톨로지 정제 규약을 LLM에 주입하는 스킬 묶음.
- `kalti-journal` — 멤버용 일지 작성 규약
- `kalti-ontology` — 운영자용 온톨로지 정제 규약

### 설치
```
/plugin marketplace add kalti-lab/claude-plugins
/plugin install kalti-lab-notes@kalti-lab
```

전역 플러그인이라 **어느 작업 폴더에서든** `/kalti-journal`을 호출할 수 있다(연구 작업은 보통 볼트가 아닌 코드·실험 폴더에서 일어나므로).

### 볼트 위치 알려주기
일지는 lab-notes 볼트의 `journals/<본인이름>/`에 쓰인다. 스킬이 볼트를 찾는 순서:

1. 환경변수 `KALTI_VAULT`
2. 기본 경로 `~/dev/lab-notes`
3. 둘 다 없으면 호출 시 한 번 물어봄

볼트를 기본 경로가 아닌 곳에 클론했다면 셸 설정에 한 줄 넣어두면 매번 안 묻는다:
```
export KALTI_VAULT="$HOME/path/to/lab-notes"
```

먼저 볼트를 클론해 둔다:
```
git clone https://github.com/kalti-lab/lab-notes.git ~/dev/lab-notes
```

연구일지 볼트는 [`kalti-lab/lab-notes`](https://github.com/kalti-lab/lab-notes), 온톨로지는 [`kalti-lab/ontology`](https://github.com/kalti-lab/ontology).
