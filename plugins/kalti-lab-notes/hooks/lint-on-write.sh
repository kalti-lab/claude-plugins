#!/bin/bash
# 볼트 안 .md를 쓴 직후 낱말·번역투 검사를 자동으로 돌린다.
#
# 왜 훅인가 — 낱말 규칙은 세 겹(전역 지침·메모리·writing.md)으로 있어도
# 글을 만드는 턴에서는 집계·템플릿에 주의가 쏠려 계속 샜다. 훅은 규칙을
# 잊어도 무조건 발화한다. 잡는 범위는 lint의 STIFF·PATTERNS뿐이고(기계 바닥),
# 표에 없는 새 비유는 교정 절차(writing.md) 몫이다.
#
# 이 훅은 모든 세션의 모든 Write·Edit 뒤에 발화하므로 볼트 밖 파일은
# 한 줄이라도 빨리 통과시킨다.

input=$(cat)
file=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    pass' 2>/dev/null)

case "$file" in
  *.md) ;;
  *) exit 0 ;;
esac

. ~/.config/kalti/notes.env 2>/dev/null
VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"
[ -d "$VAULT/journals" ] || exit 0
case "$file" in
  "$VAULT"/*) ;;
  *) exit 0 ;;
esac

here="$(cd "$(dirname "$0")" && pwd)"
out=$(python3 "$here/../shared/lint.py" "$VAULT" --file "$file" 2>&1)
if [ $? -ne 0 ]; then
  # exit 2 + stderr — 방금 글을 쓴 모델에게 같은 턴에 되먹여 바로 고치게 한다.
  {
    echo "낱말 검사(lint)에 걸렸습니다. shared/writing.md의 규칙대로 쉬운 말로 고치십시오."
    echo "$out"
  } >&2
  exit 2
fi
exit 0
