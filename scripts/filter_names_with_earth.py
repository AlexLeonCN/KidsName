#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从完整吉名表中筛选「字义五行含土」的名字，生成新 Markdown。"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "梁姓男孩三字名_五格三才吉名.md"
OUT = ROOT / "梁姓男孩三字名_字义五行含土.md"


def parse_rows(text: str) -> tuple[str, list[list[str]]]:
    lines = text.splitlines()
    header_idx = next(
        i for i, ln in enumerate(lines) if ln.startswith("| 序号 |") and "字义五行" in ln
    )
    header = lines[header_idx]
    rows: list[list[str]] = []
    for ln in lines[header_idx + 2 :]:
        if not ln.startswith("|"):
            break
        parts = [p.strip() for p in ln.strip("|").split("|")]
        if len(parts) >= 7:
            rows.append(parts)
    return header, rows


def earth_chars_in_wuxing(cell: str) -> list[str]:
    elems = re.findall(r"([\u4e00-\u9fff])([木火土金水])", cell)
    return [ch for ch, e in elems if e == "土"]


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    _header, rows = parse_rows(text)

    filtered = []
    for parts in rows:
        earth = earth_chars_in_wuxing(parts[5])
        if earth:
            filtered.append((parts, earth))

    freq = Counter()
    for _, earth in filtered:
        freq.update(earth)

    lines = [
        "# 梁姓男孩三字名（字义五行含土）",
        "",
        f"> 本表自 [`{SRC.name}`](./{SRC.name}) 筛选得出。",
        ">",
        "> **筛选条件**：在原「五格/三才已符合」名单基础上，进一步要求"
        "**姓名字义五行中至少有一字属土**。",
        f"> （梁字义五行属火，故实际为名中至少一字属土；共 **{len(filtered)}** 个。）",
        ">",
        "> 原表规则仍适用：人格/地格/外格/总格为吉或半吉；三才为吉或半吉；"
        "三才半吉时四格须全吉。字义五行 ≠ 三才数理五行。",
        ">",
        "> 常见属土用字（本表出现次数）："
        + "、".join(f"{ch}（{n}）" for ch, n in freq.most_common(12)),
        "",
        "## 符合条件名字一览",
        "",
        "| 序号 | 姓名 | 康熙笔画（繁） | 五格（数/吉凶） | 三才（数理五行/吉凶） | 字义五行 | 属土用字 | 释义 |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for i, (parts, earth) in enumerate(filtered, 1):
        lines.append(
            f"| {i} | {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} | "
            f"{parts[5]} | {'、'.join(earth)} | {parts[6]} |"
        )

    # 保留原附录
    appendix_start = next(
        (i for i, ln in enumerate(text.splitlines()) if ln.startswith("## 附录")),
        None,
    )
    if appendix_start is not None:
        lines.append("")
        lines.extend(text.splitlines()[appendix_start:])

    content = "\n".join(lines) + "\n"
    content = content.replace(
        "*生成脚本：`scripts/generate_liang_boy_names.py`。",
        "*本表由 `scripts/filter_names_with_earth.py` 自完整吉名表筛选；"
        "原始生成脚本：`scripts/generate_liang_boy_names.py`。",
    )
    OUT.write_text(content, encoding="utf-8")
    print(f"filtered={len(filtered)} -> {OUT}")


if __name__ == "__main__":
    main()
