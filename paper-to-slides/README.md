# paper-to-slides 使用说明

将论文组织成**可编辑学术 PPT** 与**结构化笔记**的 Skill。产出不是压缩摘要，而是章节对齐、字段齐备、每条论断可回到原文页/段/图表的笔记与讲稿。

## 一句话用法

> 给一篇论文 PDF 与任务说明，得到可编辑 `.pptx`、`.pdf`/`.png` 预览、Markdown 笔记与 `result.json`。

## 输入

- `/input/case.json`：`case_id`、任务要求、论文路径、`output_contract`。
- `/input/task.md`：任务说明（若有）。
- 论文 PDF（路径由 case.json 指定）。

## 调用步骤

```bash
# 1) 提取带页码的原文
python scripts/extract_pdf.py /input/paper.pdf --out /app/work/paper_text.json

# 2) Agent 读原文，按 FIELD_DICTIONARY.md 产出 /app/work/slides.json
#    （章节对齐 + 字段抽取 + 证据锚点 + 讲稿）

# 3) 生成 PPTX、渲染预览、写 result.json
python scripts/build_ppt.py --case /input/case.json --slides /app/work/slides.json --out /app/output
```

## 输出（`/app/output/`）

- `slides.pptx` — 可编辑学术 PPT（16:9，含讲稿备注与证据页脚）
- `slides.pdf` — 渲染预览
- `slides_preview/page-*.png` — 每页 PNG 预览
- `slides.json` — 结构化幻灯片内容
- `paper_notes.md` — Markdown 版结构化笔记
- `result.json` — `case_id` + 全部 `output_contract` 字段 + 状态/来源/不确定性/变更记录

## 依赖

- Python 3；`python-pptx`、`pypdf`（或 `pdfplumber`）。
  - 安装：`pip install python-pptx pypdf`
- 渲染预览：`soffice`/`libreoffice`（office-renderer 工具）+ `pdftoppm`（pdf-render-tool）。
  - 缺渲染器时仍产出可编辑 `.pptx`，但 `.pdf`/`.png` 缺失，并在 `result.json` 如实标注。

## 异常处理

| 情况 | 行为 |
|---|---|
| 扫描件无文本层 | 用 ocr-tool，标注 `ocr: true` 与置信度；失败则 `unable` |
| 加密/权限受限 PDF | 记录错误，`unable` + 原因，不编造 |
| 双栏错序、页眉页脚噪声 | 按页提取后按段重排，噪声段跳过并标注 |
| 图表/公式缺失 | 锚点标注 `missing` |
| `python-pptx` 缺失 | 仍产出 `slides.json`/`paper_notes.md`/`result.json`，`.pptx` 标注「未生成」 |
| 渲染器缺失 | 产出可编辑 `.pptx`，预览标注「未渲染」 |

## 最小示例（示意，非正式案例结果）

`/input/case.json`（示意）：

```json
{"case_id": "demo", "output_contract": ["research_question", "methods", "findings", "limitations", "evidence"], "paper_path": "/input/paper.pdf"}
```

`/app/work/slides.json`（示意片段，标明为示例）：

```json
{
  "paper": {"title": "示例论文（示意）", "authors": "A, B", "venue": "示例期刊", "year": 2024},
  "summary": {"research_question": "示例研究问题（示意）", "key_finding": "示例主要发现（示意）"},
  "slides": [
    {"title": "方法", "section": "Methods", "bullets": [
      {"text": "示例方法要点（示意）", "anchor": "p.3¶2 · Fig.1", "evidence_status": "reported"}
    ], "speaker_notes": "本页讲稿（示意）"}
  ],
  "limitations": [{"text": "示例局限（示意）", "anchor": "p.9¶2", "status": "reported"}]
}
```

运行 `build_ppt.py` 后得到（示意）：

```
/app/output/slides.pptx
/app/output/slides.pdf
/app/output/slides_preview/page-01.png
/app/output/result.json   # {"case_id":"demo","status":"success",...}
```

以上均为示意输入输出，**不冒充正式案例结果**；正式案例、白板与测评由平台提供。

## 自检清单

- [ ] 每章至少一页，顺序与论文一致（对得上）
- [ ] 研究问题/数据/方法/发现/局限齐全（留得住）
- [ ] 每条论断有页码/段落/图表锚点（找得回）
- [ ] `.pptx` 可编辑，讲稿备注已写入（用得上）
- [ ] 渲染预览存在且与 `.pptx` 一致；缺预览已标注
- [ ] `result.json` 含 `case_id` 与全部 `output_contract` 字段，未报告/无法判断/冲突已如实标注
- [ ] 未编造测试成绩、正式案例答案或运行日志
