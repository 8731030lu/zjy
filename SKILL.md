---
name: literature-translation
description: 将科研论文（或指定段落区间）翻译为可核验的双语对照结果：锁定术语表、段落级原文对齐、保护数字/单位/公式/文献编号、逐段指回原文证据。当任务为文献翻译、双语对照、术语一致性翻译、长文分段翻译或译文核验时使用。
---

# 文献翻译 Skill（术语锁定 · 段落对齐 · 可核验）

把一篇真实科研论文（PDF 或文本）翻译成**可复核的双语对照结果**，而不是只给大意或改写。
核心原则：**术语表真正被执行**、**段落不漏不重不错位**、**数字单位公式引用准确保留**、**每段译文能指回原文并说明译法依据**。

## 何时使用

- 任务要求"翻译论文 / 双语对照 / 逐段翻译 / 术语一致性翻译 / 译文核验"。
- 输入是科研论文 PDF 或带页码的文本，要求给出中文译文并保留原文定位。
- 需要在标题、摘要、正文、图注、结论中统一同一术语译名。

## 输入输出契约

运行环境（Harbor / DeepSeek Harness）提供：

| 路径 | 内容 |
|---|---|
| `/input/case.json` | 案例标识 `case_id`、任务说明、材料路径、输出字段契约 `output_contract`（若给出） |
| `/input/task.md` | 本次翻译任务的具体要求、目标语言、范围、约束 |
| 材料文件 | 论文 PDF（或文本），路径见 `case.json` / `task.md` |

工作目录 `/app/work`，最终结果与可编辑产物写入 `/app/output`。
**必须输出** `/app/output/result.json`：包含 `case_id` 与 `output_contract` 要求的全部字段，并补上本 Skill 的标准字段（见下）。

### result.json 标准字段

```json
{
  "case_id": "…",
  "status": "success | partial | cannot_judge | refused",
  "status_reason": "…",
  "main_result": { "…": "按 output_contract 的主结果，或指向完整产物" },
  "bilingual_file": "bilingual.md",
  "terminology_file": "terminology.tsv",
  "verification_file": "verification.md",
  "evidence": [
    { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body|caption|table|formula|reference", "locator": "页1第1段" }
  ],
  "uncertainty": {
    "unreported": ["…"],
    "ambiguous": ["…"],
    "conflicting": ["…"],
    "untranslated": ["…"]
  },
  "verification": { "checks_run": ["…"], "terminology_ok": true, "paragraph_ok": true, "relation_ok": true },
  "change_log": ["…"]
}
```

`status` 取值：全部完成=`success`；部分可译=`partial`（须写明限制）；无法判断=`cannot_judge`（须写原因）；无法执行=`refused`（须写原因与可人工接管位置）。
**不要编造原文没有的内容**；译不准处显式标注，不要含混。

## 工作流（按顺序执行，尽早保存部分产物）

### 第 0 步 读输入、定边界
1. 读 `/input/case.json` 与 `/input/task.md`。
2. 确认：目标语言、翻译范围（全文/指定段落区间）、是否要求图表题注/表头/公式/参考文献一并翻译。
3. 若 `case.json` 定义了 `output_contract`，记录其字段名——`result.json` 必须逐字包含这些字段。
4. 读实际材料文件；**不要按文件名或标签臆测内容**，以真实文件为准。

### 第 1 步 抽取原文并保留结构
- 有文字层：用 `pdf-text-tool` 按页抽取，保留页码、段落边界、栏顺序、标题层级。
- 无文字层（扫描件）：用 `pdf-render-tool` 渲染页 → `ocr-tool` 识别；对识别质量差处标注"OCR 待确认"。
- 结构标记（必须保留）：
  - 段落 `para_id`（稳定编号 P1…Pn，全文唯一）
  - 页码、章节（Section）、栏
  - 元素类型 `kind`：`body`(正文段) / `heading`(标题) / `caption`(图注/表题) / `table`(表头/表体) / `formula`(公式) / `reference`(参考文献条目)
  - 公式编号、图表编号、文献编号 `[n]`、脚注
- 产出 `source_manifest`（写入 `/app/work/source.json`）：段落清单，每段含 `para_id, page, section, kind, text`。

### 第 2 步 建立并锁定术语表
1. 从标题、摘要、关键词、各级标题、正文、图注、结论抽取**领域术语**与缩写。
2. 每个术语给出：源词、锁定译名、领域、首现位置、备注（如"保留原文不译""行业标准译名"）。
3. **先锁定后翻译**：全文翻译只能使用术语表内的译名；遇到新术语先回填术语表再使用。
4. 规则：
   - 数字、单位、公式、变量符号、文献编号**不进术语表、不翻译**（见第 4 步保护规则）。
   - 专有名词（人名/机构/软件/数据集）按标准译名或保留原文，全篇一致。
   - 缩写首次出现处写"全称（缩写，译名）"，之后只用锁定译名。
   - 一个源词只允许一个译名；若确有歧义，显式标注"待人工确认"，不悄悄换译名。

### 第 3 步 段落切分与对齐
- 检查跨页、跨栏、跨章节段落：不得漏段、重复、错位、把一段拆成两段或把两段并成一段。
- 段号 `para_id` 必须与原文一一对应；补齐因分页/分栏导致的接续。
- 表格按行/列结构保留；公式作为独立单元（编号保留）；图注与对应图号绑定。
- 产出段落级对齐框架（写入 `/app/work/alignment.json`）：`para_id ↔ (page, section, kind)`。

### 第 4 步 逐段翻译（携带上下文 + 硬约束）
按语义边界逐段翻译；翻译下一段时携带：上一段要点、活动术语表、指代对象缓存。

**硬约束（违反即扣正确性分）**：
- **数字与单位**：数值、量纲、误差、范围符号原样保留；不换算、不四舍五入；确需换算须显式注明。
- **公式**：LaTeX/公式内容原样保留；只翻译公式周围文字；公式编号保留。
- **文献编号与引用标记**：`[1]`、`(Smith, 2020)`、`Fig. 3`、`Table 2`、`Eq. (4)` 原样保留，不翻译、不改写。
- **否定与限定**：not / only / unless / at least / at most / ≤ / ≥ / approximately / exactly / except 必须精确译出，不得丢失或反转。
- **指代**：this / it / the former / the latter / which 若指代不明，译为显式名词（可加括号说明），保持一致。
- **因果与让步**：because / although / however / therefore / since / despite 逻辑关系保留。
- **术语**：一律用锁定术语表译名，禁止临时改译。

### 第 5 步 双语对照输出
- 每段输出 `para_id | 原文 | 译文 | 页码 | 章节 | 类型 | 译法依据/备注`。
- 译不准、保留原文、OCR 不确定处，显式标注 `【未译】` / `【待确认】` / `【OCR 存疑】`，不混入正文假装已译。
- 可编辑产物写入 `/app/output/bilingual.md`（Markdown 对照表）。

### 第 6 步 译文核验（自检）
按 `resources/verification_checklist.md` 逐项检查并写核验报告：
1. **术语稳**：在标题/摘要/正文/图注/结论中扫描每个锁定术语，确认译名一致、无临时改译。
2. **段落全**：核对 `para_id` 数量与顺序，确认无漏段/重段/错位/误并。
3. **关系准**：抽查+模式扫描数字、单位、公式、图表编号、文献编号、否定与限定、指代、因果让步。
4. **可核验**：每段译文有原文定位；待确认项清单明确。
- 产出 `/app/output/verification.md`：检查项、发现的问题、需要人工确认的清单。

### 第 7 步 写结果与可编辑产物
1. `/app/output/terminology.tsv`：术语表（TSV，含来源位置）。
2. `/app/output/bilingual.md`：双语对照全文。
3. `/app/output/verification.md`：核验报告。
4. `/app/output/result.json`：见上文标准字段；**确保包含 `case.json` 声明的全部 `output_contract` 字段**。
5. 若任务要求 Office/PPT/图表等可编辑产物：用 `office-renderer` / `latex-compiler` 产出**真实渲染的 PDF/PNG 预览**，与可编辑源文件一起放入 `/app/output`，并在 `result.json` 注明。
6. 部分完成时，明确写出已覆盖范围与未完成限制；**失败也要保存已得到的部分产物**。

## 异常处理（详细见 resources/error_handling.md）
- 无文字层 → OCR；质量差处标注。
- 公式/表格为图片 → 保留图片，标注"图内公式/表格未译"。
- 参考文献无法解析 → 保留原样，不猜测补全。
- 原文残缺/语言混杂 → 注明并给 `partial` 状态。
- 材料缺失 → `refused` + 原因，不得编造数据。

## 最小调用示例（示意，非正式案例）

输入 `/input/case.json`：
```json
{ "case_id": "example-001", "task": "translate abstract", "output_contract": { "fields": ["abstract_zh"] } }
```

示意输出 `/app/output/result.json`（**仅为示例，标明示例**）：
```json
{
  "case_id": "example-001",
  "status": "success",
  "status_reason": "",
  "main_result": { "abstract_zh": "【示例】……（示意译文）……" },
  "bilingual_file": "bilingual.md",
  "terminology_file": "terminology.tsv",
  "verification_file": "verification.md",
  "evidence": [ { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body" } ],
  "uncertainty": { "unreported": [], "ambiguous": [], "conflicting": [], "untranslated": [] },
  "verification": { "checks_run": ["terminology", "paragraph", "relation"], "terminology_ok": true, "paragraph_ok": true, "relation_ok": true },
  "change_log": ["示例：按术语表锁定译名"]
}
```

## 资源文件
- `resources/terminology_schema.md` — 术语表格式与抽取/锁定规则
- `resources/bilingual_schema.md` — 双语对照输出与 source/alignment JSON 结构
- `resources/verification_checklist.md` — 四类问题核验清单
- `resources/error_handling.md` — 异常处理手册
