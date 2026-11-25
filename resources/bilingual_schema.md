# 双语对照输出与中间结构

## 中间文件（工作目录 /app/work）

### source.json —— 原文抽取清单

```json
{
  "source_file": "paper.pdf",
  "extraction_method": "pdf-text-tool | ocr-tool",
  "paragraphs": [
    {
      "para_id": "P1",
      "page": 1,
      "section": "Abstract",
      "kind": "body | heading | caption | table | formula | reference",
      "text": "…"
    }
  ]
}
```

要求：
- `para_id` 全文唯一、稳定，与原文一一对应。
- `kind` 区分正文/标题/图注/表/公式/参考文献，便于核验图表题注、表头、公式编号、引用标记是否覆盖。
- 跨页、跨栏段落：合并为一段，但在 `text` 前标注接续位置，例如 `…(continued from p.3)…`。

### alignment.json —— 段落对齐框架

```json
{
  "alignment": [
    { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body" }
  ]
}
```

翻译时逐段按此框架推进，确保不漏段、不重段、不错位。

## 双语对照输出（/app/output/bilingual.md）

Markdown 表格，每段一行：

```markdown
| para_id | 原文 | 译文 | 页码 | 章节 | 类型 | 译法依据/备注 |
|---|---|---|---|---|---|---|
| P1 | The ... | …… | 1 | Abstract | body | 术语锁定：… |
| P2 | ... | …… | 2 | Intro | body | 【待确认】… |
```

备注列用法：
- `术语锁定：X→Y` —— 说明关键译法依据。
- `【未译】` —— 保留原文未译（公式/编号/专名等）。
- `【待确认】` —— 译不准或歧义，需人工确认。
- `【OCR 存疑】` —— OCR 识别质量差，原文可能不准。

## result.json 的 evidence 结构

```json
"evidence": [
  { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body", "locator": "页1第1段" }
]
```

每段译文必须有对应的 `evidence` 条目（可核验性要求）。
