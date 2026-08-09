# 梁姓男孩三字名（五格·三才）

为姓「梁」的男孩生成符合五格、三才要求的三字名列表。

## 文档

- [`梁姓男孩三字名_五格三才吉名.md`](./梁姓男孩三字名_五格三才吉名.md)：符合条件的名字表格（含康熙笔画、五格、三才、五行、释义）

## 规则摘要

- 笔画按《康熙字典》繁体（含氵=4、辶=7、左阝=8 等特殊部首）
- 人格、地格、外格、总格为吉或半吉
- 三才为吉或半吉；若三才为半吉，则上述四格须全部为吉
- 天格由姓氏决定（梁→12，传统多判凶），筛选时不否决，仅作标注

## 重新生成

```bash
pip install opencc-python-reimplemented
python3 scripts/generate_liang_boy_names.py
```

笔画数据见 `data/name_char_strokes.json`（由 Kangxi stroke count 表抽取）。
