"""rBOM操作説明書PDFを、目次の「機能」単位のMarkdownに分割し、索引を作る。

使い方:
    python -I build_manual.py [PDFパス] [出力フォルダ]

依存: pymupdf（pip install pymupdf）
出力: manual/ 配下（INDEX.md、部/章フォルダ、各章の _INDEX.md、機能ごとの .md）
要約・キーワード: summaries.json（キー=manual からの相対パス）があれば、
    各 .md の先頭情報と _INDEX.md に取り込む。再生成しても要約は失われない。
"""
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "V4.0_rBOM操作説明書.pdf"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "manual"
SUMMARIES = HERE / "summaries.json"

TOC_PAGES = range(4, 15)  # 目次が載っているPDFページ（1始まり）
BAD_FILENAME = str.maketrans({c: "_" for c in '\\:*?"<>|'} | {"/": "／"})

TOC_LINE = re.compile(r"^(?P<title>.+?)\s*\.{3,}\s*(?P<page>\d+)\s*$")
PART = re.compile(r"^第(\d+)部\s*(.*)$")
CHAPTER = re.compile(r"^第(\d+)\s*章\s*(.*)$")
ENTRY_ID = re.compile(r"^\[(?P<id>[^\]]+)\]\s*(?P<name>.*)$")


def nfkc(s):
    """PDFには康熙部首（⽀・⼿ 等）や半角カナが混在し、grepで当たらなくなるため正規化する。"""
    return unicodedata.normalize("NFKC", s)


def safe_name(s):
    return nfkc(s).translate(BAD_FILENAME).strip().rstrip(".")


def parse_toc(doc):
    """目次を (kind, title, start_page) のリストにする。kind = part / chapter / entry"""
    items = []
    for pno in TOC_PAGES:
        for line in doc[pno - 1].get_text().splitlines():
            m = TOC_LINE.match(nfkc(line).strip())
            if not m:
                continue
            title, page = m["title"].strip(), int(m["page"])
            if PART.match(title):
                kind = "part"
            elif CHAPTER.match(title):
                kind = "chapter"
            else:
                kind = "entry"
            items.append((kind, title, page))
    return items


def clean_page(text, pno):
    """ヘッダー（部名）・著作権表記・ページ番号を除き、空行を詰める。"""
    lines = [nfkc(l).rstrip() for l in text.splitlines()]
    out = []
    for i, l in enumerate(lines):
        s = l.strip()
        if not s:
            out.append("")
        elif s.startswith("©"):
            continue
        elif s == str(pno):
            continue
        elif PART.match(s) and not out:
            continue  # ページ先頭の部名（ランニングヘッダー）
        else:
            out.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    doc = pymupdf.open(PDF)
    toc = parse_toc(doc)
    summaries = json.loads(SUMMARIES.read_text(encoding="utf-8")) if SUMMARIES.exists() else {}

    # 見出し(部/章)と機能を、ページ順の「境界」として並べる。機能の終わり = 次の境界の直前
    bounds = [p for _, _, p in toc] + [doc.page_count + 1]

    # 親(部/章)を割り当てながら、書き出し対象を組み立てる
    part = chapter = None
    part_dir = chapter_dir = None
    entries = []  # dict(部, 章, id, name, start, end, path)
    chapters = {}  # chapter_dir -> dict
    for idx, (kind, title, start) in enumerate(toc):
        end = max(start, bounds[idx + 1] - 1)
        if kind == "part":
            m = PART.match(title)
            part = f"第{m[1]}部 {m[2]}".strip()
            part_dir = safe_name(f"第{m[1]}部_{m[2]}")
            chapter = chapter_dir = None
            continue
        if kind == "chapter":
            m = CHAPTER.match(title)
            chapter = f"第{m[1]}章 {m[2]}".strip()
            chapter_dir = safe_name(f"第{m[1]}章_{m[2]}")
            chapters[(part_dir, chapter_dir)] = dict(part=part, chapter=chapter, start=start, entries=[])
            # 章の扉〜最初の機能の間に本文があるものは「章の概要」として残す
            first = next((p for k, _, p in toc[idx + 1:] if k == "entry"), None)
            if first and first > start:
                entries.append(dict(part=part, chapter=chapter, part_dir=part_dir, chapter_dir=chapter_dir,
                                    id="00", name="章の概要", start=start, end=first - 1, lead=True))
            continue
        m = ENTRY_ID.match(title)
        eid, name = (m["id"], m["name"]) if m else ("", title)
        entries.append(dict(part=part, chapter=chapter, part_dir=part_dir, chapter_dir=chapter_dir,
                            id=eid, name=name.strip(), start=start, end=end, lead=False))

    # 書き出し
    for d in OUT.glob("第*部_*"):
        shutil.rmtree(d)
    seen = set()
    written = skipped = 0
    for e in entries:
        label = f"[{e['id']}]{e['name']}" if e["id"] and not e["lead"] else e["name"]
        e["label"] = label
        fname = (f"{e['id']}_{safe_name(e['name'])}" if e["id"] else safe_name(e["name"])) + ".md"
        rel = f"{e['part_dir']}/{e['chapter_dir']}/{fname}" if e["chapter_dir"] else f"{e['part_dir']}/{fname}"
        assert rel not in seen, f"ファイル名が重複: {rel}"
        seen.add(rel)

        body, plain, imgs_total = [], [], 0
        for pno in range(e["start"], e["end"] + 1):
            page = doc[pno - 1]
            imgs = len(page.get_images())
            imgs_total += imgs
            ptext = clean_page(page.get_text(), pno)
            plain.append(ptext)
            body.append(f"<!-- P{pno} img={imgs} -->\n{ptext}")
        text = "\n\n".join(body)
        # 章の扉は背景画像が1点あるだけ。文字が章名のみなら中身なしとして省く
        only_title = len(re.sub(r"\s", "", "".join(plain).replace(e["chapter"], ""))) < 40
        if e["lead"] and only_title:
            skipped += 1  # 扉だけで中身が無い
            e["skip"] = True
            continue

        e["rel"], e["images"], e["chars"] = rel, imgs_total, len(text)
        s = summaries.get(rel, {})
        e["summary"], e["keywords"] = s.get("summary", ""), s.get("keywords", "")
        pages = f"{e['start']}-{e['end']}" if e["end"] > e["start"] else f"{e['start']}"
        e["pages"] = pages
        head = ["---", f"部: {e['part']}", f"章: {e['chapter']}", f"機能: {label}", f"PDFページ: {pages}",
                f"画像: {imgs_total}点"]
        if e["summary"]:
            head.append(f"要約: {e['summary']}")
        if e["keywords"]:
            head.append(f"キーワード: {e['keywords']}")
        head += ["---", f"# {label}（P{pages}）", ""]
        path = OUT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(head) + text + "\n", encoding="utf-8", newline="\n")
        written += 1

    # 章ごとの索引
    by_chapter = {}
    for e in entries:
        if e.get("skip"):
            continue
        by_chapter.setdefault((e["part_dir"], e["chapter_dir"]), []).append(e)
    for (pd, cd), es in by_chapter.items():
        if not cd:
            continue
        lines = [f"# {es[0]['part']} / {es[0]['chapter']}", "",
                 "| ファイル | PDFページ | 画像 | 要約 / キーワード |", "|---|---|---|---|"]
        for e in es:
            sk = " ／ ".join(x for x in (e["summary"], e["keywords"] and f"キーワード: {e['keywords']}") if x)
            lines.append(f"| {Path(e['rel']).name} | P{e['pages']} | {e['images']} | {sk} |")
        (OUT / pd / cd / "_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    # 全体索引
    top = ["# rBOM操作説明書 V4.0 索引", "",
           f"元PDF: {PDF.name}（{doc.page_count}ページ）。機能（目次の[NN]）単位に分割。",
           "各章フォルダの `_INDEX.md` に、機能ごとのファイル名・PDFページ・要約が載っている。",
           "本文中の `<!-- P184 img=3 -->` は元PDFのページ番号と画像数。画面図が必要なときはそのページをPDFから直接読む。",
           "機能名に `OP` が付くものはオプション機能。", ""]
    cur = None
    for (pd, cd), es in sorted(by_chapter.items(), key=lambda kv: kv[1][0]["start"]):
        if pd != cur:
            top += ["", f"## {es[0]['part']}", ""]
            cur = pd
        e0 = es[0]
        first, last = min(e["start"] for e in es), max(e["end"] for e in es)
        loc = f"{pd}/{cd}/_INDEX.md" if cd else f"{pd}/"
        top.append(f"- {e0['chapter'] or '(章なし)'}: {len(es)}件 P{first}-{last} → `{loc}`")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "INDEX.md").write_text("\n".join(top) + "\n", encoding="utf-8", newline="\n")

    total = sum(e["chars"] for e in entries if not e.get("skip"))
    print(f"目次項目 {len(toc)} / 書き出し {written} ファイル / 扉のみで省略 {skipped} / 本文 {total:,} 文字")


if __name__ == "__main__":
    main()
