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


def read_text(path, n=None):
    """깨진 바이트가 섞이면 여기서 파일 이름과 함께 멈춘다.
    세는 도구라 조용히 건너뛰면 틀린 숫자가 사람 이름 옆에 붙는다."""
    # 바이트로 잘라 읽으면 안 된다 — 경계에서 한글 한 글자가 반토막 나
    # 멀쩡한 파일이 깨진 파일로 보고된다(실제로 그렇게 한 번 틀렸다).
    # 통째로 읽어 디코딩한 뒤 글자 단위로 자른다.
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        sys.exit("%s: UTF-8로 못 읽는 바이트가 %d번째 자리에 있습니다.\n"
                 "grep도 이 파일을 조용히 건너뜁니다 — lint를 돌려 고친 뒤 다시 세십시오."
                 % (path, e.start))
    return text if n is None else text[:n]


def read_head(path, n=2000):
    return read_text(path, n)


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
    finding) under ontology/<종류>/. A flat listdir would count only the top
    level and quietly report near-zero 카드 for everyone."""
    cards = collections.Counter()
    oroot = os.path.join(vault, "ontology")
    for dirpath, _, files in os.walk(oroot):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            for base in set(WIKILINK.findall(
                    read_text(os.path.join(dirpath, fn)))):
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
        for ref in set(WIKILINK.findall(read_text(path))):
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


def project_rollup(vault, journals, cards):
    """종목 축. 사람 축이 "누가 얼마나 썼나"를 보는 자리라면 이쪽은
    "무엇이 굴러가고 무엇이 멈췄나"를 본다 — 조용해진 종목과, 일지는 쌓였는데
    카드가 안 나온 종목이 사람 축에서는 보이지 않는다."""
    P = {}
    for base, meta in journals.items():
        pr = meta["project"] or "(종목 없음)"
        s = P.setdefault(pr, {"n": 0, "cards": 0, "dates": [], "who": set()})
        s["n"] += 1
        s["cards"] += cards[base]
        s["dates"].append(meta["date"])
        s["who"].add(meta["author"])
    # 종목 카드의 status
    oroot = os.path.join(vault, "ontology", "종목")
    if os.path.isdir(oroot):
        for fn in os.listdir(oroot):
            if fn.endswith(".md") and fn[:-3] in P:
                P[fn[:-3]]["status"] = field(read_head(os.path.join(oroot, fn)), "status")
    return P


def onto_heads(vault):
    """ontology/ 전체를 한 번 걷어 (상대경로, 머리 텍스트) 목록으로."""
    out = []
    for dirpath, _, files in os.walk(os.path.join(vault, "ontology")):
        for fn in sorted(files):
            if fn.endswith(".md"):
                out.append((fn[:-3], read_head(os.path.join(dirpath, fn), 3000)))
    return out


def digest(vault, journals, cards, month):
    """--digest YYYY-MM. 월간 소식의 숫자를 전부 한 번에 뽑는다.

    글은 사람이(스킬이) 쓰고, 여기서는 세는 것만 한다 — 손으로나 즉석
    grep으로 세면 실행마다 수가 달라진다는 contrib의 규칙이 여기에도 그대로
    적용된다. 판가름 난 날은 본문이 아니라 꼬리표 칸(closed/reversed)에서
    읽는다. 본문 줄에서 긁으면 형식이 어긋난 장이 조용히 빠진다."""
    mj = {b: m for b, m in journals.items() if str(m["date"])[:7] == month}
    heads = onto_heads(vault)

    finds, decs, closed, rev = [], [], [], []
    superseded_by = {}   # 옛 카드 이름 -> 새 카드 이름 (supersedes/refutes 역방향)
    for base, h in heads:
        ty = field(h, "type")
        for k in ("supersedes", "refutes"):
            m = re.search(r'^%s:[ \t]*"?\[\[([^\]]+)' % k, h, re.M)
            if m:
                superseded_by[m.group(1)] = base
        d = field(h, "date")
        if ty == "finding" and d[:7] == month:
            finds.append((base, field(h, "partOf")))
        if ty == "decision" and d[:7] == month:
            decs.append((base, field(h, "partOf")))
        if ty == "hypothesis" and field(h, "closed")[:7] == month:
            closed.append((base, field(h, "status"), field(h, "closed"), field(h, "partOf")))
        if ty == "decision" and field(h, "reversed")[:7] == month:
            rev.append((base, field(h, "reversed"), field(h, "partOf")))

    pj = lambda v: (re.search(r"\[\[([^\]]+)", v) or [None, v or "-"])[1]

    # 아직 안 본 일지 — 온톨로지가 가리키지 않고 검토기록에도 없는 것
    checked = set()
    try:
        rec = read_text(os.path.join(vault, "reports", "정제", "검토기록.md"))
        checked = {m.group(1) for m in re.finditer(r"(?m)^- (\S+)", rec)}
    except OSError:
        pass
    pending = [b for b in journals if cards[b] == 0 and b not in checked]

    print("kalti-report --digest · %s" % month)
    print()
    print("── 숫자 다섯 칸 " + "─" * 40)
    st = collections.Counter(s for _, s, _, _ in closed)
    print("  일지 %d편 · 새로 알아낸 것 %d장 · 새로 정한 것 %d장 · "
          "판가름 난 생각 %d건(%s) · 아직 안 본 일지 %d"
          % (len(mj), len(finds), len(decs), len(closed) + len(rev),
             " ".join("%s %d" % kv for kv in st.most_common()) or "-",
             len(pending)))

    print()
    print("── 종목 순위 (새로 알아낸 것 + 새로 정한 것 + 판가름 난 생각) " + "─" * 8)
    chg = collections.Counter()
    for _, po in finds: chg[pj(po)] += 1
    for _, po in decs: chg[pj(po)] += 1
    for _, _, _, po in closed: chg[pj(po)] += 1
    for _, _, po in rev: chg[pj(po)] += 1
    jn = collections.Counter(m["project"] for m in mj.values())
    for p, n in chg.most_common():
        print("  %s %2d   (그 달 일지 %d편)" % (vpad(p, 26), n, jn.get(p, 0)))
    quiet = [p for p in jn if p not in chg]
    if quiet:
        print("  카드 없이 일지만 있는 종목: " + " · ".join(sorted(quiet)))

    print()
    print("── 예상이 빗나간 것 (기각·대체됨·번복됨) " + "─" * 22)
    for base, s, d, po in sorted(closed, key=lambda x: x[2]):
        if s == "채택":
            continue
        print("  %s (%s, %s, %s)" % (base, s, d, pj(po)))
        if base in superseded_by:
            print("      → 대신: %s" % superseded_by[base])
    for base, d, po in rev:
        print("  %s (번복됨, %s, %s)" % (base, d, pj(po)))
    print("  채택: " + (" · ".join(b for b, s, _, _ in closed if s == "채택") or "-"))

    print()
    print("── 기여 (그 달, 회고 제외) " + "─" * 32)
    ppl = collections.defaultdict(lambda: {"n": 0, "c": 0,
                                           "types": collections.Counter()})
    for b, m in mj.items():
        if m["type"] == "retro":
            continue
        s = ppl[m["author"]]
        s["n"] += 1; s["c"] += cards[b]; s["types"][m["type"]] += 1
    for a in sorted(ppl):
        s = ppl[a]
        print("  %-9s 연구노트 %2d · 카드 %3d · 밀도 %.1f · %s"
              % (a, s["n"], s["c"], s["c"] / s["n"] if s["n"] else 0,
                 " ".join("%s %d" % (TYPE_KO.get(k, k), v)
                          for k, v in s["types"].most_common())))
    retro = sum(1 for m in mj.values() if m["type"] == "retro")
    if retro:
        print("  (회고 %d편은 다른 일지를 간추린 글이라 뺐다 — 일지 칸과 그만큼 어긋난다)" % retro)

    print()
    print("── 다음 호 예고 후보 (그 달 `## 다음 액션` 중 날짜·숫자 붙은 줄) " + "─" * 5)
    jroot = os.path.join(vault, "journals")
    hits = 0
    for b, m in sorted(mj.items(), key=lambda kv: kv[1]["date"]):
        path = None
        for dirpath, _, files in os.walk(os.path.join(jroot, m["author"])):
            if b + ".md" in files:
                path = os.path.join(dirpath, b + ".md"); break
        if not path:
            continue
        sec = re.search(r"(?ms)^## 다음 액션\s*\n(.+?)(?=\n## |\Z)", read_text(path))
        if not sec:
            continue
        for line in sec.group(1).splitlines():
            s = line.strip()
            if s.startswith(("-", "*")) and re.search(
                    r"\d{4}-\d{2}-\d{2}|\d+[%%건편개층mm]|\dB\b", s):
                print("  [%s] %s" % (m["project"], s.lstrip("-* ")[:110]))
                hits += 1
    if not hits:
        print("  (없음)")


def main():
    vault = resolve_vault(sys.argv)
    journals = collect(vault)
    if not journals:
        sys.exit("연구노트를 찾지 못했습니다.")
    cards = count_cards(vault, journals)

    for i, a in enumerate(sys.argv):
        if a == "--digest":
            if i + 1 >= len(sys.argv) or not re.fullmatch(r"\d{4}-\d{2}", sys.argv[i + 1]):
                sys.exit("--digest 뒤에 YYYY-MM을 적어야 합니다.")
            digest(vault, journals, cards, sys.argv[i + 1])
            return

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
    if "--projects" in sys.argv:
        P = project_rollup(vault, journals, cards)
        today = max(alld)
        print("── 종목 " + "─" * 56)
        print()
        pw = max(vlen(p) for p in P) + 2   # 한글은 두 칸이라 vlen으로 재야 맞는다
        print(vpad("종목", pw) + "일지  카드  사람  마지막      쉰 날  상태")
        for pr in sorted(P, key=lambda k: -P[k]["n"]):
            s = P[pr]
            idle = (today - max(s["dates"])).days
            print(vpad(pr, pw) + "%4d  %4d  %4d  %s  %5d  %s"
                  % (s["n"], s["cards"], len(s["who"]), max(s["dates"]),
                     idle, s.get("status", "-")))
        print()
        dry = [p for p, s in P.items() if s["cards"] == 0]
        if dry:
            print("· 일지는 쌓였는데 카드가 한 장도 안 나온 종목 %d개: %s"
                  % (len(dry), " · ".join(sorted(dry))))
        quiet = sorted(((today - max(s["dates"])).days, p) for p, s in P.items()
                       if (today - max(s["dates"])).days >= 60
                       and s.get("status") == "진행")
        if quiet:
            print("· 60일 넘게 조용한데 상태가 '진행'인 종목 %d개:" % len(quiet))
            for d, p in quiet:
                print("    %s — %d일" % (p, d))
            print("  쉰 것과 접은 것은 다르다. 접었으면 상태를 바꾸고, 아니면 그대로 둔다.")
        print()

    print("=== READ (작업용 — 보고서에 넣지 말 것) " + "=" * 22)
    for a in order:
        mine = sorted((b for b in journals if journals[b]["author"] == a),
                      key=lambda b: -cards[b])[:3]
        print(f"{a}: " + " | ".join(f"{cards[b]}장 {b}" for b in mine))


if __name__ == "__main__":
    main()
