#!/bin/bash
# 볼트 안에서 git commit을 하기 전에 전수 검사를 강제한다.
#
# 왜 있나 — "커밋 전에 lint를 돌리고 오류를 다 고친다"는 규칙이 스킬 두 곳에
# 적혀 있는데 글로만 있었다. 저장할 때 도는 훅은 낱말만 보고, 구조 검사는
# 모델이 기억해야만 돌았다. 그래서 스킬을 안 거친 일지가 옛 모양 그대로
# 들어온 적이 있다(2026-09-14). 기억에 기대는 한 규칙을 늘려도 같은 식으로
# 샌다 — 그래서 기계가 막는다.
#
# 오류만 막는다. 경고는 판단이 필요한 것이라 통과시킨다.

input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("command", ""))
except Exception:
    pass' 2>/dev/null)

case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

. ~/.config/kalti/notes.env 2>/dev/null
VAULT="${KALTI_VAULT:-$HOME/dev/lab-notes}"
[ -d "$VAULT/journals" ] || exit 0

# 볼트에 커밋할 것이 없으면 볼 일이 없다
here="$(cd "$(dirname "$0")" && pwd)"
staged=$(git -C "$VAULT" diff --cached --name-only 2>/dev/null | head -1)
[ -n "$staged" ] || exit 0

out=$(python3 "$here/../shared/lint.py" "$VAULT" --quiet 2>&1)
if [ $? -ne 0 ]; then
  {
    echo "볼트 검사에 오류가 있어 커밋을 멈춥니다. 오류를 고친 뒤 다시 커밋하십시오."
    echo "(경고는 막지 않습니다. 오류만입니다.)"
    echo "$out"
  } >&2
  exit 2
fi
exit 0
