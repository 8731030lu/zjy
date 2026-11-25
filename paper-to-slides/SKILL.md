---
name: paper-to-slides
description: 将一篇科研论文组织成可编辑学术 PPT（PPTX）并输出结构化笔记。按论文自身章节顺序建页、把研究问题/数据/方法/结论/局限写入字段化内容、为每条关键结论保留页级证据锚点（页码·段落·图表）、为每页生成讲稿备注，并用 office-renderer 渲染真实 PDF/PNG 预览，最终写 result.json。触发词：把论文做成 PPT、文献总结幻灯片、论文结构化笔记、论文做成 slides、make slides from paper、paper to pptx、organize paper into slides、literature structured notes、文献阅读笔记、章节对齐笔记、证据回链笔记。
---

# paper-to-slides：论文 → 可编辑学术 PPT + 结构化笔记

把一个真实论文 PDF 组织成**可编辑的学术幻灯片（.pptx）**与**可复核的结构化笔记**。产出不是一段压缩通读摘要，而是与论文自身章节一一对应、字段齐备、每条论断可回到原文页/段/图表的笔记与讲稿。

## 目标四原则（必须逐条满足）

1. **对得上**：幻灯片骨架与论文自身章节顺序一致，不套通用摘要模板；保留章节间的承接关系。
2. **留得住**：研究问题、数据、方法条件、主要发现、局限都被记录，尤其写明让结论成立的前提条件（数据集、假设、超参、近似）。
3. **找得回**：每条关键论断带证据锚点，指向原文页码、段落、图/表/公式；锚点粒度与可核验性匹配。
4. **用得上**：产出可编辑 .pptx、Markdown 笔记、字段化 JSON，可检索、可比较、可继续加工；每条内容带来源与不确定性标注。

## 触发条件

- 用户要求把论文做成 PPT / slides / 讲义 / 文献汇报。
- 用户要求对论文做结构化笔记、章节对齐、证据回链、知识点提取。
- 输入是一个 PDF +（可选）任务说明，需要「给论文、出笔记/幻灯片」。

## 输入（运行时，事实依据以实际文件为准）

- `/input/case.json`：案例规格，含 `case_id`、任务要求、论文材料路径、`output_contract`（result.json 必须包含的字段）。
- `/input/task.md`：题目任务说明（若存在）。
- 论文材料：PDF（路径由 `case.json` 指定，通常在 `/input/` 或 `environment/reference/`）；若为扫描件，用 ocr-tool。
- **必须读取实际文件内容**，不得依据文件名或领域标签臆造内容。PDF 解析拿到的是原始 PDF，没有预抽取答案层。

## 输出（写入 `/app/output/`，工作目录用 `/app/work/`）

| 文件 | 内容 |
|---|---|
| `slides.json` | 结构化幻灯片内容（章节、要点、证据锚点、讲稿） |
| `paper_notes.md` | Markdown 版结构化笔记（章节对齐 + 证据回链） |
| `slides.pptx` | 可编辑学术 PPT（16:9，含讲稿备注、证据页脚） |
| `slides.pdf` | 由 PPTX 真实渲染的 PDF 预览 |
| `slides_preview/page-XX.png` | 每页 PNG 预览（供检查） |
| `result.json` | 结果契约：`case_id` + 全部 `output_contract` 字段 + 状态/来源/不确定性/变更记录 |

## 工作流

### Phase 0 — 读取输入与边界
1. 读 `/input/case.json`：取出 `case_id`、`output_contract`、论文路径、任务要求。
2. 读 `/input/task.md`（若有）。
3. 明确哪些字段可由机器判定、哪些必须人工确认；把「未报告 / 无法判断 / 材料冲突」作为合法结果，不要写成事实。

### Phase 1 — 提取原文（带页码）
运行 `scripts/extract_pdf.py <paper.pdf> --out /app/work/paper_text.json`，得到每页文本与页号。
- 文本层缺失（扫描件）→ 调用 ocr-tool；OCR 结果要标注 `ocr: true` 与置信度。
- 加密 / 权限受限 → 记录错误，产出「无法判断」状态，不编造。

### Phase 2 — 章节对齐（对得上）
按论文**自身**章节切分（标题、编号、先后顺序），不套模板。为每章生成至少一页，保留章节承接关系。识别不出的章节如实标注 `section: "未识别"`。

### Phase 3 — 关键内容抽取（留得住）
对每章提取：目的、方法条件、数据、主要结果、结论与局限。重点保留**让结论成立的前提**（数据规模、模型假设、参数、近似、适用范围）。数值、变量、方法条件必须与原文一致。

### Phase 4 — 证据锚点（找得回）
每条关键论断附锚点，格式（见 FIELD_DICTIONARY.md）：

```
{页码}{段落}{图表/公式}，例如：p.3¶2 · Fig.1 · "42.7 kJ/mol"
```

锚点必须指向真实对应位置；无法定位的写 `anchor: null, evidence_status: "unreported"`。

### Phase 5 — 生成可编辑 PPTX 与预览
运行 `scripts/build_ppt.py`，输入 `slides.json`，输出到 `/app/output/`：
1. 生成可编辑 `.pptx`（标准占位符文本，可在 PowerPoint/WPS 编辑）。
2. 每页写入讲稿备注（speaker notes）。
3. 页脚写入证据锚点。
4. 用 `office-renderer`（LibreOffice headless）把 `.pptx` 渲染为 `.pdf`，再转 `slides_preview/*.png`。
5. 渲染失败时诚实记录：仍交付 `slides.json` + `paper_notes.md` + `result.json`，并把 `.pptx` 标记为「未渲染预览」。

### Phase 6 — 写 result.json 与自检
`build_ppt.py` 会读取 `case.json` 的 `output_contract`，把结果映射到全部字段，并附加：
- `status`: `success` / `partial` / `unable`（+ 原因）
- `sources`: 每条结论的证据锚点
- `uncertainty`: 未报告 / 无法判断 / 冲突项
- `change_records`: 做了什么、为何这样做
- `artifacts`: 产物路径清单

## 证据锚点格式（详见 FIELD_DICTIONARY.md）

锚点 = `page + 段落 + 图表/公式 + 可选原文短引`，用 `·` 分隔，短引用用引号。示例：
`p.3¶2 · Fig.1 · "The activation energy is 42.7 kJ/mol"`

## 依赖与安装

- Python 3（scientific-python 工具）；`python-pptx`、`pypdf`（或 `pdfplumber`）。
- 渲染预览需要 `office-renderer`（LibreOffice headless）或 `browser-automation`；缺省则仅产出可编辑 PPTX，不产出预览，并在 result.json 中标注。
- 安装：`pip install python-pptx pypdf`。

## 异常处理

| 情况 | 处置 |
|---|---|
| 扫描件无文本层 | ocr-tool，标注 `ocr: true` 与置信度；失败则 `unable` |
| 加密/权限受限 PDF | 记录错误，产出 `unable` + 原因，不编造 |
| 双栏错序/页眉页脚噪声 | 按页提取后按段重排，噪声段标注跳过 |
| 图表/公式缺失 | 锚点写 `Fig/公式 缺失`，`evidence_status: missing` |
| 超长论文 | 按章节分块处理，逐块写 slides.json，再合并 |
| 非中文论文 | 保留原文，讲稿可中文，锚点与原文一致 |
| `python-pptx` 缺失 | 仍产出 slides.json / paper_notes.md / result.json，`.pptx` 标注「未生成」 |
| `office-renderer` 缺失 | 产出可编辑 `.pptx`，`.pdf`/`.png` 标注「未渲染」 |

## 最小调用示例（示意，非正式案例）

```
# 输入 /input/case.json（示意）
{"case_id":"demo","output_contract":["research_question","methods","findings","limitations","evidence"],"paper_path":"/input/paper.pdf"}

# 1) 提取
python scripts/extract_pdf.py /input/paper.pdf --out /app/work/paper_text.json
# 2) Agent 读原文，产出 slides.json（示意片段，标明为示例）
# 3) 生成 PPTX + 预览 + result.json
python scripts/build_ppt.py --case /input/case.json --slides /app/work/slides.json --out /app/output
```

示意输出（标明为示例，非正式案例结果）：

```
/app/output/slides.pptx        # 可编辑学术 PPT
/app/output/slides.pdf         # 渲染预览
/app/output/slides_preview/page-01.png
/app/output/result.json        # {"case_id":"demo","status":"success",...}
```

## 自检清单（交付前逐项确认）

- [ ] 每章至少一页，顺序与论文一致（对得上）
- [ ] 研究问题/数据/方法/发现/局限齐全（留得住）
- [ ] 每条论断有页码/段落/图表锚点（找得回）
- [ ] .pptx 可编辑，讲稿备注已写入（用得上）
- [ ] 渲染预览存在且与 .pptx 一致；缺预览已标注
- [ ] result.json 含 case_id 与全部 output_contract 字段，未报告/无法判断/冲突已如实标注
- [ ] 未编造任何测试成绩、正式案例答案或运行日志
