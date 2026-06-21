#!/usr/bin/env python3
"""폴더를 Obsidian 볼트로 등록 (obsidian.json의 vaults에 멱등 추가).

사용:
  register_obsidian_vault.py <vault_path> [--restart]

찍는 상태(한 단어 — 호출하는 쪽에서 이걸로 분기):
  ALREADY_REGISTERED       이미 등록돼 있음 (변경 없음)
  REGISTERED               등록 완료 (Obsidian이 꺼져 있었음)
  REGISTERED_WITH_RESTART  Obsidian을 곱게 닫고 등록 후 다시 열었음 (--restart, macOS)
  NEEDS_GUI                Obsidian이 떠 있는데 자동 불가 — GUI로 등록 필요
  NOT_A_DIR <path>         볼트 경로가 폴더가 아님
  OBSIDIAN_JSON_UNREADABLE obsidian.json을 읽을 수 없음

왜 이렇게: Obsidian은 실행 중에 obsidian.json을 고쳐도 종료할 때 제 메모리
상태로 다시 써서 추가분을 지운다. 그래서 등록은 앱이 꺼져 있을 때만 남는다.
--restart(맥)면 곱게 종료(강제 kill 아님 — 저장 후 정상 quit) → 닫힘 확인 →
등록 → 재실행 순으로 자동 처리한다. 닫히지 않으면(미저장 다이얼로그 등)
밀어붙이지 않고 NEEDS_GUI로 빠진다.
"""
import json
import os
import platform
import secrets
import subprocess
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


def is_running():
    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
            return "obsidian.exe" in out
        # macOS / Linux — 이름이 "Obsidian" 또는 "obsidian"
        for name in ("Obsidian", "obsidian"):
            if subprocess.run(["pgrep", "-x", name], capture_output=True).returncode == 0:
                return True
        return False
    except Exception:
        return False


def quit_obsidian_mac():
    subprocess.run(["osascript", "-e", 'tell application "Obsidian" to quit'], capture_output=True)


def wait_until_closed(timeout=12.0, interval=0.5):
    end = time.time() + timeout
    while time.time() < end:
        if not is_running():
            return True
        time.sleep(interval)
    return not is_running()


def relaunch_mac():
    subprocess.run(["open", "-a", "Obsidian"], capture_output=True)


def load_json(oj):
    if not os.path.exists(oj):
        return {}
    return json.load(open(oj))


def already_registered(data, vault):
    for entry in data.get("vaults", {}).values():
        if os.path.abspath(os.path.expanduser(entry.get("path", ""))) == vault:
            return True
    return False


def add_vault(oj, data, vault):
    data.setdefault("vaults", {})[secrets.token_hex(8)] = {"path": vault, "ts": int(time.time() * 1000)}
    os.makedirs(os.path.dirname(oj), exist_ok=True)
    tmp = oj + ".kalti.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, oj)


def main():
    args = sys.argv[1:]
    restart = "--restart" in args
    positional = [a for a in args if not a.startswith("--")]
    if not positional:
        print("usage: register_obsidian_vault.py <vault_path> [--restart]")
        return 2

    vault = os.path.abspath(os.path.expanduser(positional[0]))
    if not os.path.isdir(vault):
        print(f"NOT_A_DIR {vault}")
        return 1

    oj = obsidian_json_path()
    try:
        data = load_json(oj)
    except Exception:
        print("OBSIDIAN_JSON_UNREADABLE")
        return 1

    if already_registered(data, vault):
        print("ALREADY_REGISTERED")
        return 0

    if not is_running():
        add_vault(oj, data, vault)
        print("REGISTERED")
        return 0

    # 실행 중 + 미등록
    if restart and platform.system() == "Darwin":
        quit_obsidian_mac()
        if not wait_until_closed():
            print("NEEDS_GUI")  # 안 닫힘 — 강제하지 않음
            return 0
        try:
            data = load_json(oj)  # 종료하며 다시 썼을 수 있으니 재로딩
        except Exception:
            print("OBSIDIAN_JSON_UNREADABLE")
            return 1
        if already_registered(data, vault):
            relaunch_mac()
            print("ALREADY_REGISTERED")
            return 0
        add_vault(oj, data, vault)
        relaunch_mac()
        print("REGISTERED_WITH_RESTART")
        return 0

    print("NEEDS_GUI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
