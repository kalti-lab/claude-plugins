#!/usr/bin/env python3
"""폴더를 Obsidian 볼트로 등록한다 (obsidian.json의 vaults에 항목 추가, 멱등).

사용: register_obsidian_vault.py <vault_path>
출력: ALREADY_REGISTERED / REGISTERED / NOT_A_DIR <path> / OBSIDIAN_JSON_UNREADABLE

- 이미 같은 경로가 등록돼 있으면 그대로 두고 ALREADY_REGISTERED.
- 없으면 16자리 hex id로 항목을 더한다. open:true 는 넣지 않는다 — 지금 열려
  있는 볼트와 다투지 않게(등록만 하고, 어느 걸 열지는 Obsidian이 정함).
- 원자적 쓰기(임시파일 → os.replace)로 obsidian.json 손상을 막는다.

주의: Obsidian은 실행 중 종료할 때 obsidian.json을 제 메모리 상태로 다시 쓰면서
방금 더한 항목을 지울 수 있다. 그래서 이 스크립트는 Obsidian이 꺼져 있을 때
돌려야 등록이 남는다(호출하는 쪽에서 pgrep으로 확인 후 결정).
"""
import json
import os
import platform
import secrets
import sys
import time


def obsidian_json_path():
    home = os.path.expanduser("~")
    system = platform.system()
    if system == "Darwin":
        return os.path.join(home, "Library", "Application Support", "obsidian", "obsidian.json")
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        return os.path.join(base, "obsidian", "obsidian.json")
    base = os.environ.get("XDG_CONFIG_HOME", os.path.join(home, ".config"))
    return os.path.join(base, "obsidian", "obsidian.json")


def main():
    if len(sys.argv) < 2:
        print("usage: register_obsidian_vault.py <vault_path>")
        return 2
    vault = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if not os.path.isdir(vault):
        print(f"NOT_A_DIR {vault}")
        return 1

    oj = obsidian_json_path()
    os.makedirs(os.path.dirname(oj), exist_ok=True)
    try:
        data = json.load(open(oj)) if os.path.exists(oj) else {}
    except Exception:
        print("OBSIDIAN_JSON_UNREADABLE")
        return 1

    vaults = data.setdefault("vaults", {})
    for entry in vaults.values():
        if os.path.abspath(os.path.expanduser(entry.get("path", ""))) == vault:
            print("ALREADY_REGISTERED")
            return 0

    vaults[secrets.token_hex(8)] = {"path": vault, "ts": int(time.time() * 1000)}
    tmp = oj + ".kalti.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, oj)
    print("REGISTERED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
