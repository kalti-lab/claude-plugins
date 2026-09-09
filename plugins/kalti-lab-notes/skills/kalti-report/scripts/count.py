#!/usr/bin/env python3
"""kalti-report --contrib — count the three numbers per member.

Reads the vault and prints (1) the ready-to-paste 요약 block, (2) per-member
fact rows, (3) the 참고 line, and (4) a READ list the model uses to pick which
journals to actually open. Everything printed above the READ marker is meant to
be reproduced verbatim in the report; the READ list is working material and
must not appear in the output.

Usage: count.py [VAULT]   (default: $KALTI_VAULT, then ~/dev/lab-notes)
"""
import collections
import datetime
import os
import re
import sys

TYPE_KO = {
    "build": "만들기",
    "investigation": "조사",
    "experiment": "실험",
    "decision": "결정",
    "retro": "회고",
    "reading": "읽기",
}

OVERVIEW = re.compile(r"^00-")
# Tolerates the column-aligned frontmatter style (`type:      build`).
KEY = lambda k: re.compile(r"^%s:[ \t]*(.+?)[ \t]*$" % k, re.M)
# 링크 대상의 종류를 이름 무늬로 맞히지 않는다. 일지인지 아닌지는 journals/의
# 실제 파일 집합에 있느냐로만 정한다.
WIKILINK = re.compile(r"\[\[([^\]|#^]*)")
BAR = 10


def resolve_vault(argv):
    for cand in (argv[1] if len(argv) > 1 else None,
                 os.environ.get("KALTI_VAULT"),
                 os.path.expanduser("~/dev/lab-notes")):
        if cand and os.path.isdir(os.path.join(cand, "journals")) \
                and os.path.isdir(os.path.join(cand, "ontology")):
            return cand
    sys.exit("볼트를 찾지 못했습니다. /kalti-setup을 먼저 실행하십시오.")


def read_head(path, n=2000):
    with open(path, encoding="utf-8") as f:
        return f.read(n)


def field(text, key, default=""):
    m = KEY(key).search(text)
    return m.group(1) if m else default


def collect(vault):
    """basename -> {author, date, type, project}. Excludes project histories
    (00-*.md — they summarize journals already counted) and pre-registrations
    (type: prereg — they carry no results of their own).

    Both exclusions read the file, never the filename: a journal titled
    "…사전등록 재실험…" is an experiment, and a name filter drops it silently."""
    out = {}
    jroot = os.path.join(vault, "journals")
    for author in sorted(d for d in os.listdir(jroot)
                         if os.path.isdir(os.path.join(jroot, d)) and not d.startswith(".")):
        for dirpath, _, files in os.walk(os.path.join(jroot, author)):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                base = fn[:-3]
                if OVERVIEW.match(base):
                    continue
                head = read_head(os.path.join(dirpath, fn))
                ty = field(head, "type", "?")
                if ty == "prereg":
                    continue
                ds = field(head, "date")
                try:
                    d = datetime.date(int(ds[:4]), int(ds[5:7]), int(ds[8:10]))
                except ValueError:
                    sys.stderr.write("date를 읽을 수 없습니다: %s/%s (%r)\n"
                                     % (author, fn, ds))
                    continue
                out[base] = {
                    "author": author,
                    "date": d,
                    "type": ty,
                    "project": (re.search(r'^project:[ \t]*"?\[\[([^\]]+)', head, re.M)
                                or [None, "-"])[1],
                }
    return out


def count_cards(vault, journals):
    """A card that draws on three journals counts one for each of them.

    Walks ontology/ recursively: the documents (project, concept, person,
    source) sit at its top level and the project-scoped cards (hypothesis,
    finding) under ontology/세부/. A flat listdir would count only the top
    level and quietly report near-zero 카드 for everyone."""
    cards = collections.Counter()
    oroot = os.path.join(vault, "ontology")
    for dirpath, _, files in os.walk(oroot):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                for base in set(WIKILINK.findall(f.read())):
                    if base in journals:
                        cards[base] += 1
    return cards


def cross_citations(vault, journals):
    """Times a member's journal points at another member's journal."""
    n = 0
    jroot = os.path.join(vault, "journals")
    for base, meta in journals.items():
        path = None
        for dirpath, _, files in os.walk(os.path.join(jroot, meta["author"])):
            if base + ".md" in files:
                path = os.path.join(dirpath, base + ".md")
                break
        if not path:
            continue
        with open(path, encoding="utf-8") as f:
            for ref in set(WIKILINK.findall(f.read())):
                if ref in journals and journals[ref]["author"] != meta["author"]:
                    n += 1
    return n


def vlen(s):
    """Display width — CJK glyphs take two terminal columns, len() says one."""
    return sum(2 if ord(c) > 0x2E7F else 1 for c in s)


def vpad(s, n):
    return s + " " * max(0, n - vlen(s))


def bar(value, top):
    if value <= 0:
        return ""
    return "█" * max(1, round(BAR * value / top)) if top else ""


def main():
    vault = resolve_vault(sys.argv)
    journals = collect(vault)
    if not journals:
        sys.exit("연구노트를 찾지 못했습니다.")
    cards = count_cards(vault, journals)

    stat = {}
    for base, meta in journals.items():
        s = stat.setdefault(meta["author"], {
            "n": 0, "cards": 0, "dates": [],
            "types": collections.Counter(), "projects": collections.Counter()})
        s["n"] += 1
        s["cards"] += cards[base]
        s["dates"].append(meta["date"])
        s["types"][meta["type"]] += 1
        s["projects"][meta["project"]] += 1
    for s in stat.values():
        s["density"] = s["cards"] / s["n"]
        s["weeks"] = max(1, round(((max(s["dates"]) - min(s["dates"])).days + 1) / 7))

    order = sorted(stat, key=lambda a: -stat[a]["n"])
    alld = [d for s in stat.values() for d in s["dates"]]
    w = max(len(a) for a in order) + 2
    tops = (max(s["n"] for s in stat.values()),
            max(s["cards"] for s in stat.values()),
            max(s["density"] for s in stat.values()))

    print(f"kalti-report --contrib · 전체 기간 ({min(alld)} ~ {max(alld)})")
    print()
    print("── 요약 " + "─" * 56)
    print()
    col = 4 + 1 + BAR + 3  # number, space, bar field
    print(vpad("", w) + vpad(" " * 5 + "연구노트", col)
          + vpad(" " * 7 + "카드", col) + " " * 7 + "밀도")
    for a in order:
        s = stat[a]
        print(f"{a:{w}}{s['n']:>4} {bar(s['n'], tops[0]):<{BAR + 3}}"
              f"{s['cards']:>4} {bar(s['cards'], tops[1]):<{BAR + 3}}"
              f"{s['density']:>4.1f} {bar(s['density'], tops[2])}")
    print()
    print("밀도 = 카드 ÷ 연구노트.  노트 한 편이 카드에 몇 번 재료로 쓰였나.")
    print("세 칸의 순서가 서로 다르다. 총점은 매기지 않는다.")
    print()
    print("── 상세 " + "─" * 56)
    for a in order:
        s = stat[a]
        types = " · ".join(f"{TYPE_KO.get(k, k)} {v}" for k, v in s["types"].most_common())
        top4 = " · ".join(f"{k} {v}" for k, v in s["projects"].most_common(4))
        rest = len(s["projects"]) - 4
        if rest > 0:
            top4 += f" · 그 외 {rest}"
        print()
        print(f"{a}")
        print(f"  기간    {min(s['dates'])} ~ {max(s['dates'])} · {s['weeks']}주"
              f" · 주 {s['n'] / s['weeks']:.1f}편")
        print(f"  종류    {types}")
        print(f"  프로젝트 {top4}")
    print()
    print("── 참고 " + "─" * 56)
    print()
    print("· 밀도는 기록 방식에 반응한다. 결론이 한 문장으로 떨어지고 숫자가 표로")
    print("  있는 노트가 카드를 많이 낸다. 연구 실력보다 기록 습관에 가까운 값이다.")
    print(f"· 서로의 노트를 인용한 건 통틀어 {cross_citations(vault, journals)}건이다.")
    print()
    print("=== READ (작업용 — 보고서에 넣지 말 것) " + "=" * 22)
    for a in order:
        mine = sorted((b for b in journals if journals[b]["author"] == a),
                      key=lambda b: -cards[b])[:3]
        print(f"{a}: " + " | ".join(f"{cards[b]}장 {b}" for b in mine))


if __name__ == "__main__":
    main()
