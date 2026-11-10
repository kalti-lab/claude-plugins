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
parsed=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    is_agy = "conversationId" in d or "toolCall" in d
    file = d.get("tool_input", {}).get("file_path") or d.get("tool_input", {}).get("path")
    if not file:
        tc = d.get("toolCall", {})
        args = tc.get("args") or tc.get("arguments") or {}
        file = args.get("Path") or args.get("path") or args.get("filePath")
    val = file or ""
    print(str(is_agy) + "\t" + val)
except Exception:
    print("False\t")
' 2>/dev/null)

is_agy=$(printf '%s' "$parsed" | cut -f1)
file=$(printf '%s' "$parsed" | cut -f2-)

pass_hook() {
  [ "$is_agy" = "True" ] && echo "{}"
  exit 0
}

case "$file" in
  # 소식은 .html이라 .md만 보던 때는 훅을 통째로 빠져나갔다 — 낱말 규칙이
  # 가장 많이 새는 산출물이 정작 검사 밖이었다(2026-09-16에 찾음).
  *.md|*.html) ;;
  *) pass_hook ;;
esac

. ~/.config/kalti/notes.env 2>/dev/null
VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"
[ -d "$VAULT/journals" ] || pass_hook
case "$file" in
  "$VAULT"/*) ;;
  *) pass_hook ;;
esac

here="$(cd "$(dirname "$0")" && pwd)"
out=$(python3 "$here/../shared/lint.py" "$VAULT" --file "$file" 2>&1)
if [ $? -ne 0 ]; then
  # exit 2 + stderr — 방금 글을 쓴 모델에게 같은 턴에 되먹여 바로 고치게 한다.
  {
    echo "낱말 검사(lint)에 걸렸습니다. shared/writing.md의 규칙대로 쉬운 말로 고치십시오."
    echo "$out"
  } >&2
  [ "$is_agy" = "True" ] && echo "{}"
  exit 2
fi
pass_hook
