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
    "decision":   ["id", "title", "type", "status", "date", "partOf", "derivedFrom"],
}
# 종류는 이름 접두가 아니라 폴더가 말한다. 붙임표가 이름 안에도 쓰이므로
# (이미지생성-파이프라인) 접두로는 종류와 이름을 구별할 수 없었다.
# 상태 낱말은 정확히 일치해야 한다 — 커서·주간이 `^status: 기각$` 같은 문자열로 찾기
# 때문에, 한 글자만 달라도 그 카드는 조용히 집계에서 빠진다.
STATUS = {
    "project":    {"진행", "보류", "완료", "보관"},
    "hypothesis": {"제안", "채택", "기각", "대체됨"},
    "decision":   {"유효", "번복됨"},
}
ONTO_DIR = {"종목": "project", "가설": "hypothesis", "발견": "finding",
            "개념": "concept", "자료": "source", "사람": "person",
            "결정": "decision"}
LINK_KEYS = ["partOf", "derivedFrom", "supports", "refutes", "concept",
             "supersedes", "worksOn", "project", "tests", "basedOn"]

# 사람이 판단할 필요 없이 일지에서 빼야 하는 것들. 값이 아니라 배선(配線)이다.
# 코드 파일 확장자만. json·yaml·toml은 뺐다 — package.json처럼 누구나 아는
# 산출물 이름이라 뜻을 가리지 않는데 경고만 쏟아졌다.
CODE_EXT = "py|js|mjs|cjs|ts|tsx|jsx|sh|bash|rs|go|java|rb|c|cpp|h|swift|kt"
# 제품·라이브러리 이름은 파일 이름이 아니다. 사람이 읽는 고유명이라 그대로 둔다.
PRODUCT_NAMES = {"Next.js", "Node.js", "Nuxt.js", "Vue.js", "React.js", "PDF.js",
                 "Three.js", "D3.js", "xterm.js", "LiteGraph.js", "Chart.js",
                 "Express.js", "Nest.js", "Socket.io", "whisper.cpp", "llama.cpp"}

NOISE = [
    # UUID 조각과 주소 안의 16진 덩어리는 뺀다 — 앞뒤로 붙임표가 오면 커밋 해시가 아니다.
    (re.compile(r"(?<![\w/-])[0-9a-f]{7,40}(?![\w/-])"), "커밋 해시로 보이는 것"),
    # 진짜 코드 위치(sampler.py:120)만. 127.0.0.1:8001 같은 포트와
    # 4.5:1 같은 대비비는 확장자가 코드가 아니라서 안 걸린다.
    (re.compile(r"\(~\d+\)|\.(?:" + CODE_EXT + r"):\d+\b|\d+ ?번째 ?줄|줄 ?번호 ?\d+"),
     "줄 번호"),
    (re.compile(r"\bPID ?\d+"),                          "프로세스 번호"),
    (re.compile(r"/tmp/|/scratch/|scratchpad"),          "임시 경로"),
    (re.compile(r"\d+ ?[+]{3,}|\d+ ?insertions?|\d+ ?deletions?"), "diff 수치"),
    # 뒤에 점이 또 오면 도메인이다(case.ftc.go.kr) — 그건 파일 이름이 아니다.
    (re.compile(r"[\w.-]*[\w-]\.(?:" + CODE_EXT + r")\b(?!\.)"), "소스 파일 이름"),
]
# 딱딱한 낱말 — shared/writing.md 참고.
# 넓게 잡으면 안 된다. 이 볼트에서 재 봤더니 넓은 목록은 1,873건이 걸리는데
# 그중 82%가 `게이트`(dsforge의 공정 이름)·`실측`·`하네스`·`전사`처럼
# 그 팀이 원래 쓰는 말이었다. 다른 뜻으로 쓰일 여지가 없는 것만 남긴다.
# 지금 목록으로 볼트 전체 119건. 늘릴 때는 먼저 세어 보고 늘린다.
# 뺀 것 셋 — `자루`는 빗자루(지우개 옆 아이콘)에 걸렸고, `뒤집힌 것`은
# "상관 0.14로 뒤집힌 것을 잡아내"처럼 멀쩡한 쓰임이 있고, `공허 통과`는
# dsforge가 만들어 쓰는 이름이자 카드 이름이라 게이트·하네스와 같은 종류다.
STIFF = [
    ("씻겨나",    "없어진다 · 사라진다"),
    ("둔한 자",   "결과가 들쭉날쭉해진다"),
    ("평면이다",  "한 군데가 아니라 전체에서 쓴다"),
    ("일반칙",    "어디에나 통하는 규칙"),
    ("검출기",    "눈으로 봐야만 잡힌다"),
    ("방어선",    "실제로 사고를 막았다"),
    ("미증명",    "아직 확인 못 했다"),
    ("대체안",    "대신할 방법"),
    ("층위",      "성격"),
    ("절벽이",    "뚝 끊긴다"),
    ("기제",      "어떻게 그렇게 되는지"),
    ("기전",      "어떻게 그렇게 되는지"),
    # 2026-09-11 일지 교정에서 걸린 일곱 개 중 둘. 나머지 다섯(규율 20건·왕복 87건·
    # 부류 28건·닫았다 11건·정상 경로 0건이지만 happy path와 겹침)은 writing.md 표에만.
    ("무게 중심",  "손이 가장 많이 가는 곳"),      # 볼트 0건
    ("본능적",    "바로"),                       # 볼트 0건
]

FENCE = re.compile(r"```.*?```", re.S)
WIKILINK = re.compile(r"\[\[([^\]|#^]+)")

# 번역투 문법 — 낱말과 오탐의 성질이 다르다. 낱말의 오탐은 팀이 그 말을 다른
# 뜻으로 쓰는 것이라(게이트·하네스) 목록에서 빼는 수밖에 없지만, 문법의 오탐은
# 짧은 문자열이 다른 문법과 겹치는 것이라 어미를 붙여 좁히면 없어진다 —
# `에 있어`는 볼트에서 12건 전부 "DB에 있어" 같은 장소격 오탐이었는데
# `함에 있어`로 좁히니 0건이다(2026-09-11, 719편 실측). 한글에는 정규식의
# 낱말 경계가 안 통하므로 어미·조사를 문자열에 직접 넣는다. 아래는 전부 실측
# 0건 — 지금 있는 걸 잡는 게 아니라 앞으로 나오면 바로 걸리는 지뢰선이다.
# 늘릴 때는 STIFF와 같은 절차: 먼저 볼트 전체를 세고, 0이거나 전수 확인한
# 것만 넣는다. `에 대한`(38건)·`것으로 보인다`(3건)는 멀쩡한 쓰임이 섞여 보류.
PATTERNS = [
    ("되어지",       "…된다 (이중 피동)"),
    ("되어진",       "…된다 (이중 피동)"),   # 되어진다 — '되어지'로는 안 걸린다
    ("되어져",       "…돼서 (이중 피동)"),
    ("에 다름 아니", "바로 …다"),
    ("라고 할 수 있", "…다 (돌려 말하지 않는다)"),
    ("함으로써",     "…해서 · …하니"),
    ("함에 있어",    "…할 때 · …에서"),
    ("적인 측면",    "…쪽 · …면"),
    ("필요가 있다",  "…해야 한다"),
    ("바 있다",      "…한 적이 있다 · …했다"),
    ("진행하였",     "…했다"),
    ("것으로 사료",  "…로 보인다 · …인 듯하다"),
]


def strip_quoted(body):
    """검사에서 뺄 곳을 걷어낸 산문만 남긴다.
    - 위키링크 안쪽: 파일 이름은 링크가 찾아가는 주소라 못 바꾼다.
    - 본문 맨 위 제목 줄: 파일 이름을 그대로 되풀이한 것이라 같은 이유로 못 바꾼다.
      (`가설/사고를-켜면-포맷차이가-씻겨나간다` 같은 카드가 실제로 그렇다.)
    - 코드 블록: 값일 수 있다."""
    plain = re.sub(r"(?m)^#[^\n]*$", "", body, count=1)
    plain = FENCE.sub("", plain)
    # 따옴표 안과 인용 줄은 남의 문장이다. 카드는 일지 문장을 그대로 옮겨 근거로
    # 삼는 것이 규약이라, 여기를 고치면 근거가 아니게 된다. 그래서 검사에서 뺀다.
    plain = re.sub(r"(?m)^>[^\n]*$", "", plain)
    plain = re.sub(r'"[^"\n]{0,400}"|\u201c[^\u201d\n]{0,400}\u201d', "", plain)
    plain = WIKILINK.sub("", plain)
    return plain


def check_stiff(rel, body, rep):
    """말로는 안 쓰는 낱말과 번역투 문법. 어디를 빼고 보는지는 strip_quoted 참고."""
    plain = strip_quoted(body)
    stiff = [(w, alt) for w, alt in STIFF if w in plain]
    if stiff:
        rep.warn(rel, "말로는 안 쓰는 낱말 %d개: %s" % (
            len(stiff), " · ".join("%s→%s" % (w, a) for w, a in stiff[:3])))
    pats = [(w, alt) for w, alt in PATTERNS if w in plain]
    if pats:
        rep.warn(rel, "번역투 문법 %d개: %s" % (
            len(pats), " · ".join("%s→%s" % (w, a) for w, a in pats[:3])))


def walk(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in sorted(files):
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def blank(v):
    """칸은 있는데 값이 비었으면 없는 것과 같다. `summary: ""`가 검사를 그냥
    통과하던 것을 한 번 고쳤는데, `concept:`·`worksOn:`·`project: ""`에도
    같은 구멍이 있었다(11 + 3 + 1장). 그래서 한 군데로 모은다."""
    return not v.strip().strip("\"'").strip("[]").strip()


def split_fm(text):
    """꼬리표 칸을 (순서 있는 [(키, 값)], 본문)으로 가른다. 없으면 (None, 본문)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    fm, body = text[4:end], text[end + 4:]
    pairs = []
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][\w]*):(.*)$", lines[i])
        i += 1
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        # 값을 줄 바꿔 목록으로 적은 칸(`concept:` 다음 줄에 `  - "[[개념]]"`).
        # 한 줄만 읽던 때는 이게 빈 칸으로 보여서 링크 검사에서 통째로 빠졌다 —
        # 발견 11장의 concept, 사람 카드 3장의 worksOn, 일지 6편의 tags가
        # 그렇게 안 보이고 있었다. 한 줄로 이어 붙여 같은 값으로 만든다.
        if not val:
            items = []
            while i < len(lines) and re.match(r"^\s+-\s", lines[i]):
                items.append(lines[i].split("-", 1)[1].strip())
                i += 1
            if items:
                val = ", ".join(items)
        pairs.append((key, val))
    return pairs, body


def read_text(path, rel, rep):
    """깨진 바이트가 한 개만 섞여도 grep -r는 그 파일을 통째로 건너뛴다 — 경고도
    종료코드도 없이. 그러면 정제 커서의 분모에서 일지 한 편이 사라지거나 카드 한 장의
    링크가 통째로 빠지고, 주간 보고는 그 줄어든 숫자를 맞는 값처럼 싣는다.
    조용히 틀리느니 여기서 시끄럽게 잡는다."""
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        rep.err(rel, "UTF-8로 못 읽는 바이트가 %d번째 자리에 있습니다 — "
                     "grep -r가 이 파일을 조용히 건너뛰어 커서·링크 집계에서 빠집니다"
                     % e.start)
        return raw.decode("utf-8", errors="replace")


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
        text = read_text(path, rel, rep)
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
            elif blank(d[k]):
                # `_inbox/`는 종목이 정해지지 않은 일지를 두는 자리라
                # project가 빈 것이 정상이다.
                if k == "project" and os.sep + "_inbox" + os.sep in path:
                    pass
                # 빈 태그는 깨진 게 아니라 안 붙인 것뿐이라 경고로 둔다
                else:
                    (rep.warn if k == "tags" else rep.err)(
                        rel, "%s 칸이 있는데 비었습니다" % k)
        if "summary" in d and blank(d["summary"]):
            rep.err(rel, "summary가 없으면 주간·기여·정제가 매번 본문을 다시 읽습니다")
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
            hits -= PRODUCT_NAMES
            if hits:
                rep.warn(rel, "%s %d건: %s" % (label, len(hits),
                                               ", ".join(sorted(map(str, hits))[:3])))

        check_stiff(rel, body, rep)
    return names


def check_ontology(vault, rep, journal_names):
    root = os.path.join(vault, "ontology")
    no_concept = []
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
        text = read_text(path, rel, rep)
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
        holder = os.path.basename(os.path.dirname(path))
        if holder not in ONTO_DIR:
            rep.err(rel, "ontology/ 바로 밑에 있습니다 — 종류 폴더(%s) 안에 두십시오"
                         % " · ".join(ONTO_DIR))
        elif ONTO_DIR[holder] != ty:
            rep.err(rel, "%s/ 안에 있는데 type이 %s입니다" % (holder, ty))
        for k in ONTO_REQUIRED[ty] + ["updated"]:
            if k not in d:
                rep.err(rel, "%s 칸이 없습니다 (%s의 필수 칸)" % (k, ty))
            elif blank(d[k]):
                rep.err(rel, "%s 칸이 있는데 비었습니다 (%s의 필수 칸)" % (k, ty))
        if ty in STATUS:
            st = d.get("status", "").strip().strip("\"'")
            if st and st not in STATUS[ty]:
                rep.err(rel, "status가 %s에 없는 낱말입니다 (%r) — 쓸 수 있는 것: %s"
                             % (ty, st, " · ".join(sorted(STATUS[ty]))))
            # 결론이 난 날은 꼬리표 칸에 있어야 한다. 본문 `## 상태` 줄에서
            # 긁는 방식은 관행이지 규약이 아니어서, 소식·주간이 기계로 셀 때
            # 형식이 어긋난 장이 조용히 빠진다(개수 세는 검사가 못 잡는
            # 종류의 누락이다). 2026-09-11에 68+1장을 소급하며 규약으로 올렸다.
            date_field = {"hypothesis": ("closed", {"채택", "기각", "대체됨"}),
                          "decision":   ("reversed", {"번복됨"})}.get(ty)
            if date_field:
                key, closing = date_field
                if st in closing:
                    if key not in d:
                        rep.err(rel, "status가 %s인데 %s 칸이 없습니다 — 언제 결론이 났는지를 기계가 못 셉니다" % (st, key))
                    elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d[key].strip().strip("\"'")):
                        rep.err(rel, "%s가 YYYY-MM-DD가 아닙니다 (%r)" % (key, d[key]))
                elif key in d:
                    rep.err(rel, "status가 %s인데 %s 칸이 있습니다 — 아직 결론이 나지 않았습니다" % (st, key))
        elif "status" in d:
            rep.warn(rel, "%s에는 status 칸이 없습니다" % ty)
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
        # 개념이 안 붙은 발견은 장마다 경고하지 않는다. 대부분은 한 종목
        # 안에서만 뜻이 있는 결론이라 영영 개념이 안 붙고(86장을 훑었을 때
        # 기존 개념에 붙은 건 5장뿐이었다), 그러면 경고가 0이 될 수 없어
        # 뜻을 잃는다. 예전 "아무도 안 가리키는 카드" 검사를 없앤 것과 같은
        # 이유다. 장마다 알리는 대신 끝에 수만 한 줄로 적는다.
        if ty == "finding" and ("concept" not in d or blank(d.get("concept", ""))):
            no_concept.append(rel)
        check_stiff(rel, body, rep)

    for rel, key, tgt in links:
        if tgt not in cards and tgt not in journal_names:
            rep.err(rel, "%s가 없는 노트를 가리킵니다: [[%s]]" % (key, tgt))
    # 가설·발견은 partOf로 종목에 매달려 있어 되짚는 링크와 표 뷰로 늘 닿는다.
    # 예전에는 "아무도 안 가리킨다"를 경고했는데, 그건 종목 카드가 손으로 적은
    # 목록을 이고 있을 때만 뜻이 있었다. 그 목록이 낡아서 없앴으므로 검사도 뺀다.
    # 대신 정말로 매달릴 곳이 없는 쪽을 본다 — 발견이 하나도 안 붙은 개념(빈 허브)과
    # 아무도 인용하지 않는 자료.
    declared = collections.Counter()
    for _, key, tgt in links:
        if key == "concept":
            declared[tgt] += 1
    for base, (rel, ty, d) in cards.items():
        if ty == "concept" and d.get("role") != "glossary" and not declared[base]:
            rep.warn(rel, "발견이 하나도 안 붙은 개념입니다 — 허브가 아니면 용어집(role: glossary)이거나 지울 것입니다")
        if ty == "source" and not incoming[base] \
                and not any(t == base for _, _, t in links):
            rep.warn(rel, "아무도 인용하지 않는 자료입니다")

    # 용어 풀이(role: glossary)는 개념 수에서 따로 뺀다 — 종목을 잇는 허브가 아니라
    # 낱말 뜻을 적어둔 글이라, 섞어 세면 개념층이 실제보다 두터워 보인다.
    byd, gloss = {}, 0
    for rel, ty, d in cards.values():
        k = os.path.basename(os.path.dirname(rel))
        byd[k] = byd.get(k, 0) + 1
        if ty == "concept" and d.get("role") == "glossary":
            gloss += 1
    if no_concept:
        tot = sum(byd.get(k, 0) for k in ("발견",)) or len(no_concept)
        print("  개념이 안 붙은 발견 %d장 / %d장 — 한 종목 안에서만 뜻이 있는 결론이면 "
              "그대로 두고, 세 종목 넘게 같은 데 닿았으면 개념을 만든다" % (len(no_concept), tot))
    print("  온톨로지 배치: " + " · ".join(
        "%s %d장%s" % (k, byd[k], "(용어풀이 %d 포함)" % gloss
                       if k == "개념" and gloss else "")
        for k in sorted(byd)))


def check_file(vault, path):
    """파일 하나만 낱말·번역투 검사. 훅(글을 쓴 직후)과 교정 절차가 쓴다.
    구조 검사(꼬리표 칸·절·링크)는 볼트 전체 맥락이 필요해서 여기서는 안 한다.
    걸리면 1로 나가 — 훅이 이 값을 보고 같은 턴에 되먹인다."""
    rep = Report()
    rel = os.path.relpath(path, vault) if vault else path
    text = read_text(path, rel, rep)
    _, body = split_fm(text)
    check_stiff(rel, body, rep)
    for _, msg in rep.errors + rep.warns:
        print("%s: %s" % (rel, msg))
    return 1 if (rep.errors or rep.warns) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--journals", action="store_true")
    ap.add_argument("--ontology", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--detail", action="store_true", help="건별로 파일까지 보여준다")
    ap.add_argument("--file", help="이 파일 하나만 낱말·번역투 검사")
    a = ap.parse_args()
    if a.file:
        return check_file(a.vault, a.file)
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
