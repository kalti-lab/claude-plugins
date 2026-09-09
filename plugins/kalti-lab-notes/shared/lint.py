#!/usr/bin/env python3
"""kalti 볼트 검사 — 규약이 실제로 지켜졌는지 기계로 확인한다.

규약이 글로만 있으면 지켜지지 않는다. 여기서 잡는 것은 사람이 판단할 필요가 없는
것들뿐이고, 고도(어느 높이로 쓸 것인가) 같은 판단은 여전히 사람과 모델 몫이다.

사용:
    lint.py VAULT                  일지·온톨로지 둘 다
    lint.py VAULT --journals       일지만
    lint.py VAULT --ontology       온톨로지만
    lint.py VAULT --detail         건별로 어느 파일인지까지
    lint.py VAULT --quiet          오류만, 경고 생략

나가는 값: 오류가 하나라도 있으면 1, 없으면 0.
오류는 고쳐야 하는 것(구조가 깨져 다른 도구가 오작동한다), 경고는 봐야 하는 것이다.
"""
import argparse, os, re, sys, collections

TYPES = {"prereg", "experiment", "investigation", "build",
         "reading", "meeting", "decision", "retro"}
TAGS = {"infra", "security", "storage", "network", "ai", "data", "tooling",
        "report", "diffusion", "sdxl", "sampling", "image", "prompt"}
FM_ORDER = ["id", "title", "date", "author", "type", "tags", "project",
            "summary", "updated"]
FM_REQUIRED = FM_ORDER   # 280편 소급 완료(2026-09-09) — summary도 이제 필수다
SECTIONS = ["질문 / 목적", "배경", "한 일", "결과 / 관찰", "해석", "결정", "다음 액션"]
PREREG_SECTIONS = ["무엇을 정하려고 재나", "정답으로 볼 것",
                   "표본과 그것으로 충분한 이유", "어떤 결과면 무엇을 정하나"]
ONTO_REQUIRED = {
    "project":    ["id", "title", "type", "status", "tags"],
    "hypothesis": ["id", "title", "type", "status", "partOf"],
    "finding":    ["id", "title", "type", "date", "partOf", "derivedFrom"],
    "concept":    ["id", "title", "type", "tags"],
    "source":     ["id", "title", "type", "url"],
    "person":     ["id", "title", "type", "name", "role", "worksOn"],
}
ONTO_PREFIX = {"가설-": "hypothesis", "발견-": "finding", "개념-": "concept",
               "자료-": "source", "사람-": "person"}
LINK_KEYS = ["partOf", "derivedFrom", "supports", "refutes", "concept",
             "supersedes", "worksOn", "project", "tests"]

# 사람이 판단할 필요 없이 일지에서 빼야 하는 것들. 값이 아니라 배선(配線)이다.
NOISE = [
    (re.compile(r"(?<![\w/])[0-9a-f]{7,40}(?![\w/])"), "커밋 해시로 보이는 것"),
    (re.compile(r"\(~\d+\)|\.\w{1,4}:\d+\b|\d+ ?번째 ?줄|줄 ?번호 ?\d+"), "줄 번호"),
    (re.compile(r"\bPID ?\d+"),                          "프로세스 번호"),
    (re.compile(r"/tmp/|/scratch/|scratchpad"),          "임시 경로"),
    (re.compile(r"\d+ ?[+]{3,}|\d+ ?insertions?|\d+ ?deletions?"), "diff 수치"),
    (re.compile(r"[\w.-]*[\w-]\.(?:py|js|ts|tsx|jsx|sh|json|ya?ml|toml|rs|go|java)\b"), "소스 파일 이름"),
]
FENCE = re.compile(r"```.*?```", re.S)
WIKILINK = re.compile(r"\[\[([^\]|#^]+)")


def walk(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in sorted(files):
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def split_fm(text):
    """꼬리표 칸을 (순서 있는 [(키, 값)], 본문)으로 가른다. 없으면 (None, 본문)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    fm, body = text[4:end], text[end + 4:]
    pairs = []
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z_][\w]*):(.*)$", line)
        if m:
            pairs.append((m.group(1), m.group(2).strip()))
    return pairs, body


class Report:
    def __init__(self):
        self.errors, self.warns = [], []

    def err(self, path, msg):
        self.errors.append((path, msg))

    def warn(self, path, msg):
        self.warns.append((path, msg))


def check_journals(vault, rep, only=None):
    root = os.path.join(vault, "journals")
    if not os.path.isdir(root):
        rep.err("journals/", "폴더가 없습니다")
        return {}
    seen_base, seen_id, names = {}, {}, {}
    for path in walk(root):
        rel = os.path.relpath(path, vault)
        base = os.path.basename(path)[:-3]
        names[base] = rel
        text = open(path, encoding="utf-8", errors="replace").read()
        fm, body = split_fm(text)

        # 이름·id 고유성 — 날짜 접두가 사라지면 이것이 유일한 방어선이다
        if base in seen_base:
            rep.err(rel, "파일 이름이 %s와 겹칩니다 — 위키링크가 둘을 구별할 수 없습니다" % seen_base[base])
        seen_base[base] = rel

        if fm is None:
            rep.err(rel, "꼬리표 칸(frontmatter)이 없습니다")
            continue
        d = dict(fm)
        keys = [k for k, _ in fm]

        jid = d.get("id", "")
        if not jid:
            rep.err(rel, "id 칸이 비었습니다")
        elif jid in seen_id:
            rep.err(rel, "id가 %s와 겹칩니다" % seen_id[jid])
        else:
            seen_id[jid] = rel

        for k in FM_REQUIRED:
            if k not in d:
                rep.err(rel, "%s 칸이 없습니다" % k)
        # 따옴표를 벗겨야 summary: "" 같은 빈 칸이 잡힌다
        if "summary" in d and not d["summary"].strip().strip("\"'").strip():
            rep.err(rel, "summary 칸이 비었습니다 — 이게 없으면 주간·기여·정제가 매번 본문을 다시 읽습니다")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.get("updated", "")):
            rep.err(rel, "updated가 YYYY-MM-DD가 아닙니다 (%r)" % d.get("updated", ""))
        present = [k for k in keys if k in FM_ORDER]
        if present != [k for k in FM_ORDER if k in d]:
            rep.warn(rel, "칸 순서가 규약과 다릅니다 (%s)" % " ".join(present))
        for line in text.split("\n---", 1)[0].splitlines():
            if re.match(r"^[A-Za-z_]\w*:[ \t]{2,}\S", line):
                rep.warn(rel, "칸 값을 공백으로 정렬했습니다 — 느슨한 정규식이 아니면 못 읽습니다")
                break

        date = d.get("date", "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            rep.err(rel, "date가 YYYY-MM-DD가 아닙니다 (%r)" % date)
        m = re.match(r"^(\d{8})-", base)
        if m and date and m.group(1) != date.replace("-", ""):
            rep.err(rel, "파일 이름의 날짜(%s)와 date 칸(%s)이 다릅니다" % (m.group(1), date))

        ty = d.get("type", "")
        if ty not in TYPES:
            rep.err(rel, "type이 허용 목록 밖입니다 (%r)" % ty)

        author = d.get("author", "")
        folder = os.path.relpath(path, root).split(os.sep)[0]
        if author and author != folder:
            rep.err(rel, "author(%s)와 실제 폴더(%s)가 다릅니다" % (author, folder))

        for t in re.findall(r"[\w가-힣-]+", d.get("tags", "")):
            if t not in TAGS:
                rep.warn(rel, "합의 목록 밖의 태그: %s" % t)

        # 절 이름과 순서
        heads = [h.strip() for h in re.findall(r"(?m)^## (.+)$", body)]
        if base.startswith("00-"):
            pass
        elif ty == "prereg":
            for s in PREREG_SECTIONS:
                if not any(h.startswith(s) for h in heads):
                    rep.err(rel, "사전등록 절이 없습니다: %s" % s)
        else:
            idx, order_ok = -1, True
            for s in SECTIONS:
                hit = next((i for i, h in enumerate(heads) if h.startswith(s)), None)
                if hit is None:
                    rep.err(rel, "절이 없습니다: %s" % s)
                    order_ok = False
                elif hit < idx:
                    order_ok = False
                else:
                    idx = hit
            if heads and not order_ok and not any("절이 없습니다" in m for p, m in rep.errors if p == rel):
                rep.warn(rel, "절 순서가 규약과 다릅니다")

        # 채팅 찌꺼기 — 코드 블록 안은 값일 수 있으니 뺀다
        prose = FENCE.sub("", body)
        for pat, label in NOISE:
            hits = {h if isinstance(h, str) else h[0] for h in pat.findall(prose)}
            hits = {h for h in hits if not re.fullmatch(r"\d+", str(h))}
            if hits:
                rep.warn(rel, "%s %d건: %s" % (label, len(hits),
                                               ", ".join(sorted(map(str, hits))[:3])))
    return names


def check_ontology(vault, rep, journal_names):
    root = os.path.join(vault, "ontology")
    if not os.path.isdir(root):
        rep.err("ontology/", "폴더가 없습니다")
        return
    cards, seen_id, links, incoming = {}, {}, [], collections.Counter()
    nested = 0
    for path in walk(root):
        rel = os.path.relpath(path, vault)
        base = os.path.basename(path)[:-3]
        if os.path.dirname(os.path.relpath(path, root)):
            nested += 1
        if base.upper() in ("README", "INDEX"):
            continue        # 객체가 아니라 이 폴더를 설명하는 글이다
        text = open(path, encoding="utf-8", errors="replace").read()
        fm, body = split_fm(text)
        if fm is None:
            rep.err(rel, "꼬리표 칸이 없습니다 — 객체인지 설명글인지 구별되지 않습니다")
            continue
        d = dict(fm)
        ty = d.get("type", "")
        if base in cards:
            rep.err(rel, "파일 이름이 %s와 겹칩니다" % cards[base][0])
        cards[base] = (rel, ty, d)

        if ty not in ONTO_REQUIRED:
            rep.err(rel, "type이 6종 밖입니다 (%r)" % ty)
            continue
        pre = next((p for p in ONTO_PREFIX if base.startswith(p)), None)
        if pre and ONTO_PREFIX[pre] != ty:
            rep.err(rel, "이름 접두(%s)와 type(%s)이 어긋납니다" % (pre, ty))
        if not pre and ty != "project":
            rep.warn(rel, "type이 %s인데 이름에 접두가 없습니다" % ty)
        for k in ONTO_REQUIRED[ty] + ["updated"]:
            if k not in d:
                rep.err(rel, "%s 칸이 없습니다 (%s의 필수 칸)" % (k, ty))
        if ty == "person" and ({"email", "phone"} & set(d)):
            rep.err(rel, "사람 카드에 연락처가 있습니다 — 위키로 나가면 되돌릴 수 없습니다")
        cid = d.get("id", "")
        if cid and cid in seen_id:
            rep.err(rel, "id가 %s와 겹칩니다" % seen_id[cid])
        elif cid:
            seen_id[cid] = rel
        for k in LINK_KEYS:
            for tgt in WIKILINK.findall(d.get(k, "")):
                links.append((rel, k, tgt.strip()))
        for tgt in WIKILINK.findall(FENCE.sub("", body)):
            incoming[tgt.strip()] += 1
        if ty == "finding" and "concept" not in d:
            rep.warn(rel, "개념이 안 붙어 종목 밖에서 찾을 수 없습니다")

    for rel, key, tgt in links:
        if tgt not in cards and tgt not in journal_names:
            rep.err(rel, "%s가 없는 노트를 가리킵니다: [[%s]]" % (key, tgt))
    for base, (rel, ty, d) in cards.items():
        if ty in ("hypothesis", "finding") and not incoming[base] \
                and not any(t == base for _, _, t in links):
            rep.warn(rel, "아무도 가리키지 않는 고아 카드입니다")

    print("  온톨로지 배치: 최상위 %d장 · 하위 폴더 %d장" % (len(cards) - nested, nested))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--journals", action="store_true")
    ap.add_argument("--ontology", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--detail", action="store_true", help="건별로 파일까지 보여준다")
    a = ap.parse_args()
    both = not (a.journals or a.ontology)
    rep = Report()

    names = check_journals(a.vault, rep, None) if (both or a.journals) else {}
    if both or a.ontology:
        if not names:
            names = {os.path.basename(p)[:-3]
                     for p in walk(os.path.join(a.vault, "journals"))} \
                if os.path.isdir(os.path.join(a.vault, "journals")) else set()
        check_ontology(a.vault, rep, names)

    for label, items in (("오류", rep.errors), ("경고", rep.warns)):
        if label == "경고" and a.quiet:
            continue
        if not items:
            print("\n%s 없음" % label)
            continue
        print("\n=== %s %d건 ===" % (label, len(items)))
        by_kind = collections.defaultdict(list)
        for path, m in items:
            kind = re.sub(r"\s*\d+건.*$", "", re.sub(r"[:(].*", "", m)).strip()
            by_kind[kind].append((path, m))
        for kind, rows in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
            print("  %-44s %3d건" % (kind[:44], len(rows)))
            if a.detail:
                for path, m in rows[:6]:
                    print("       %s" % path)
                    print("         %s" % m)
                if len(rows) > 6:
                    print("       … 외 %d건" % (len(rows) - 6))
    print()
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
