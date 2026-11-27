# 段落编号、对齐与双语对照格式

## 目的
长文跨页、跨栏、跨章节时**不漏段、不重复、不错位**，段号与原文一一对应，每段译文可指回原文。

## 段号（para_id）生成规则
- 按**阅读顺序**编号：P1、P2、P3…，全文唯一且稳定。
- 一个 `para_id` = 一个语义段落；标题、图注、表头、公式块、文献条目各自成段。
- `kind` 取值：
  - `body` 正文段 / `heading` 标题 / `caption` 图注 / `table` 表头与表体 / `formula` 公式块 / `reference` 参考文献条目。
- **跨页/跨栏/跨章节续段**：同一段落被分页符、分栏或章节边界切断时，**合并为一段**，`page` 写起始页，`note` 标注"跨页 P2→P3"。

## source.json（原文抽取清单）

```json
{
  "source_file": "paper.pdf",
  "extraction_method": "text | ocr",
  "paragraphs": [
    { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body",
      "sentence": "S1", "text": "…", "note": "" }
  ]
}
```

- `sentence` 记录段内句子起止（用于译文指回句子级位置）。
- 抽取完成后核对：`para_id` 数量 = 原文段落数；页码、章节连续无跳段。

## 双语对照输出（bilingual.md）

Markdown 表格，每段一行：

```markdown
| para_id | 原文 | 译文 | 页码 | 章节 | 类型 | 备注 |
|---|---|---|---|---|---|---|
| P1 | The proposed … | 本文提出的…… | 1 | Abstract | body | 术语锁定：beamforming→波束成形 |
| P2 | Fig. 3 shows … | 图 3 展示了…… | 2 | Results | caption | 【待确认】… |
```

- 每行一段，`para_id` 与 `source.json` 一一对应，顺序一致。
- 备注列标注：`术语锁定：X→Y`、`【未译】`、`【待确认】`、`【OCR 存疑】`、`跨页 P2→P3`。

## evidence 结构（result.json）

```json
"evidence": [ { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body", "sentence": "S1", "locator": "页1摘要段第1句" } ]
```

- 每个**关键结论**（术语译法、数字/公式/引用保留、存疑项）都要有对应 `evidence` 条目。
- `locator` 是可读的定位描述，便于人工复核。

## 完整性核对（段落全）
1. `bilingual.md` 的 `para_id` 数量与顺序 = `source.json` 一致；
2. 无漏段（原文有、译文无）、无重段（一段译两次）、无错位（顺序颠倒）；
3. 跨页/跨栏/跨章节续段已合并且标注接续。
