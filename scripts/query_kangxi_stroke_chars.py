#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询指定康熙笔画的起名字，剔除偏旁部首类构件后输出表格。"""

from __future__ import annotations

import csv
import json
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
WUXING_JSON = ROOT / "data" / "char_wuxing.json"
STROKE_JSON = ROOT / "data" / "name_char_strokes.json"
KANGXI_CSV = ROOT / "data" / "kangxi-strokecount.csv"
KANGXI_URL = (
    "https://raw.githubusercontent.com/breezyreeds/kangxi-strokecount/"
    "master/kangxi-strokecount.csv"
)

TARGET_STROKES = (4, 10, 14, 20, 21)
WUXING_ORDER = {"木": 0, "火": 1, "土": 2, "金": 3, "水": 4}

# OpenCC 一对多时会改成另一个字；起名按本字计康熙笔画
S2T_OVERRIDE = {
    "丑": "丑",  # 地支，不是「醜」
    "后": "后",  # 后妃，不是「後」
    "斗": "斗",  # 北斗，不是「鬥」
    "干": "干",  # 天干，不是「幹/乾」
    "台": "台",  # 台辅，不是「臺」
    "里": "里",
    "面": "面",
    "系": "系",
    "余": "余",
    "只": "只",
    "才": "才",
    "冲": "沖",
    "征": "征",
    "采": "采",
}

# 几乎只作偏旁、部首、笔画构件，不作独立起名字
RADICAL_ONLY = set(
    "丨丶丿亅乀乁乚乛丂丄丅丆丒丩丮丯丱丷乄"
    "亠冂冖冫凵勹匕匚匸卩厶夊宀尢尸屮巛巳巾幺广廴廾弋彐彡彳"
    "攴攵殳爻爿爫禸辵釆髟鬯鬲曰毋"
    "欠歹爪片犬戈止父牙氏廿"
    "氵忄扌亻牜犭礻衤饣纟讠钅釒飠辶阝刂灬艹⺮⺝⺼丬"
)


def _tz_shanghai() -> timezone:
    return timezone(timedelta(hours=8), name="CST")


def timestamp_now() -> str:
    return datetime.now(_tz_shanghai()).strftime("%Y%m%d%H%M%S")


def ensure_kangxi_csv() -> Path:
    if KANGXI_CSV.exists():
        return KANGXI_CSV
    KANGXI_CSV.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(KANGXI_URL, KANGXI_CSV)
    return KANGXI_CSV


def load_kangxi_strokes(path: Path) -> Dict[str, int]:
    data: Dict[str, int] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            if "CodePoint" in line:
                f.seek(pos)
                break
        for row in csv.DictReader(f):
            data[row["Character"]] = int(row["Strokes"])
    return data


def load_wuxing() -> Dict[str, str]:
    return json.loads(WUXING_JSON.read_text(encoding="utf-8"))


def load_curated_trad() -> Dict[str, Tuple[str, int]]:
    """已人工校对的繁体与笔画（优先于 OpenCC）。"""
    if not STROKE_JSON.exists():
        return {}
    raw = json.loads(STROKE_JSON.read_text(encoding="utf-8"))
    out: Dict[str, Tuple[str, int]] = {}
    for ch, info in raw.items():
        out[ch] = (info["trad"], int(info["strokes"]))
    return out


def is_cjk_unified(ch: str) -> bool:
    if len(ch) != 1:
        return False
    o = ord(ch)
    return (
        0x4E00 <= o <= 0x9FFF
        or 0x3400 <= o <= 0x4DBF
        or 0x20000 <= o <= 0x2A6DF
    )


def is_radical_or_stroke(ch: str) -> bool:
    if ch in RADICAL_ONLY:
        return True
    o = ord(ch)
    if (
        0x2E80 <= o <= 0x2EFF  # CJK Radicals Supplement
        or 0x2F00 <= o <= 0x2FDF  # Kangxi Radicals
        or 0x2FF0 <= o <= 0x2FFF  # Ideographic Description
        or 0x31C0 <= o <= 0x31EF  # CJK Strokes
        or 0xF900 <= o <= 0xFAFF  # Compatibility Ideographs
    ):
        return True
    name = unicodedata.name(ch, "")
    return "RADICAL" in name or "CJK STROKE" in name


def lookup_trad_strokes(
    ch: str,
    cc: OpenCC,
    kangxi: Dict[str, int],
    curated: Dict[str, Tuple[str, int]],
) -> Optional[Tuple[str, int]]:
    if ch in S2T_OVERRIDE:
        trad = S2T_OVERRIDE[ch]
        st = kangxi.get(trad, kangxi.get(ch))
        if st is None:
            return None
        return trad, st
    if ch in curated:
        trad, st = curated[ch]
        return trad, st
    trad = cc.convert(ch)
    st = kangxi.get(trad, kangxi.get(ch))
    if st is None:
        return None
    return trad, st


def collect_chars(
    wuxing: Dict[str, str],
    kangxi: Dict[str, int],
    curated: Dict[str, Tuple[str, int]],
    cc: OpenCC,
    targets: Iterable[int] = TARGET_STROKES,
) -> Dict[int, List[Tuple[str, str, str, int]]]:
    target_set = set(targets)
    grouped: Dict[int, List[Tuple[str, str, str, int]]] = defaultdict(list)
    seen = set()
    for ch, wx in wuxing.items():
        if not is_cjk_unified(ch) or is_radical_or_stroke(ch):
            continue
        looked = lookup_trad_strokes(ch, cc, kangxi, curated)
        if looked is None:
            continue
        trad, st = looked
        if is_radical_or_stroke(trad):
            continue
        if st not in target_set:
            continue
        key = (ch, st)
        if key in seen:
            continue
        seen.add(key)
        grouped[st].append((ch, trad, wx, st))

    for st, rows in grouped.items():
        rows.sort(key=lambda r: (WUXING_ORDER.get(r[2], 9), r[0]))
    return grouped


def write_markdown(
    grouped: Dict[int, List[Tuple[str, str, str, int]]],
    out_path: Path,
    ts: str,
) -> None:
    total = sum(len(v) for v in grouped.values())
    lines = [
        f"# 康熙笔画字_{ts}",
        "",
        "> 数据范围：起名字典（`data/char_wuxing.json`）∩《康熙字典》繁体笔画。",
        ">",
        "> **笔画**：4、10、14、20、21（按繁体及特殊部首还原，与本仓库五格计画一致）。",
        ">",
        "> **已剔除**：偏旁部首专用字、笔画构件、康熙部首区/兼容汉字；"
        "日、月、木、水、火、心等既是部首也是独立汉字的，予以保留。",
        ">",
        f"> 合计 **{total}** 字。字义五行来自起名字典，供参考。",
        "",
        "## 各画字数",
        "",
        "| 康熙笔画 | 字数 |",
        "| ---: | ---: |",
    ]
    for st in TARGET_STROKES:
        lines.append(f"| {st} | {len(grouped.get(st, []))} |")
    lines.append("")

    for st in TARGET_STROKES:
        rows = grouped.get(st, [])
        chars = "".join(r[0] for r in rows)
        lines += [
            f"## {st}画（{len(rows)}字）",
            "",
            f"{chars}",
            "",
            "| 序号 | 简体 | 繁体 | 康熙笔画 | 字义五行 |",
            "| ---: | :---: | :---: | ---: | :---: |",
        ]
        for i, (ch, trad, wx, strokes) in enumerate(rows, 1):
            lines.append(f"| {i} | {ch} | {trad} | {strokes} | {wx} |")
        lines.append("")

    lines += [
        "---",
        "",
        "*生成脚本：`scripts/query_kangxi_stroke_chars.py`。"
        "笔画数据来源：breezyreeds/kangxi-strokecount。*",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(
    grouped: Dict[int, List[Tuple[str, str, str, int]]],
    out_path: Path,
) -> None:
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["序号", "简体", "繁体", "康熙笔画", "字义五行"])
        n = 0
        for st in TARGET_STROKES:
            for ch, trad, wx, strokes in grouped.get(st, []):
                n += 1
                w.writerow([n, ch, trad, strokes, wx])


def main() -> None:
    cc = OpenCC("s2t")
    kangxi = load_kangxi_strokes(ensure_kangxi_csv())
    wuxing = load_wuxing()
    curated = load_curated_trad()
    grouped = collect_chars(wuxing, kangxi, curated, cc)

    ts = timestamp_now()
    md_path = ROOT / f"康熙笔画字_{ts}.md"
    csv_path = ROOT / f"康熙笔画字_{ts}.csv"
    write_markdown(grouped, md_path, ts)
    write_csv(grouped, csv_path)

    print(f"timestamp={ts}")
    for st in TARGET_STROKES:
        print(f"  {st}画: {len(grouped.get(st, []))}")
    print(f"-> {md_path.name}")
    print(f"-> {csv_path.name}")

    # 抽查：已知起名字应在对应笔画中
    checks = {
        4: "月日心文方少仁斗丑",
        10: "桐家恩轩哲",
        14: "荣瑞睿福豪",
        20: "宝曦瀚潇耀",
        21: "巍鹤澜誉铎",
    }
    for st, sample in checks.items():
        have = {r[0] for r in grouped.get(st, [])}
        missing = [c for c in sample if c not in have]
        if missing:
            raise SystemExit(f"CHECK FAIL {st}画 missing {missing}")
        print(f"check {st}画 ok")

    banned = "氵忄扌亻辶阝丨丶丿亅亠冂冖冫曰毋爻爿攴殳髟鬯鬲欠歹爪片犬戈止父牙氏廿"
    present = {r[0] for rows in grouped.values() for r in rows}
    leaked = [c for c in banned if c in present]
    if leaked:
        raise SystemExit(f"CHECK FAIL radical leaked {leaked}")
    print("check radicals excluded ok")


if __name__ == "__main__":
    main()
