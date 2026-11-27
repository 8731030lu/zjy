---
name: literature-translation
description: 将科研论文翻译为可核验的双语对照结果，锁定术语表并全篇回填、段落级对齐、保护数字单位公式与文献编号、逐段指回原文证据。用于文献翻译、双语对照、术语一致性翻译、长文分段续译与译文核验。
---

# 文献翻译 Skill

把一篇（或一个明确段落区间的）真实科研论文翻译为**可复核的双语对照结果**。验收只有四个口径：**术语稳、段落全、关系准、可核验**。

## 触发与适用

- 适用：科研论文的全文 / 摘要 / 章节 / 指定段落区间的翻译；双语段落对照；术语一致性翻译；长文分段续译；译文核验与修改建议。
- 边界：面向"内容准确、可复核"的学术翻译，不做文学化润色；若目标文本不是学术文献，仍按本流程处理，并在 `result.json.status_reason` 说明。

## 输入与输出

环境提供：
- `/input/case.json`：`case_id`、任务说明、材料路径、输出字段要求（若含 `output_contract`，必须逐字保留其字段名）
- `/input/task.md`：本次翻译的目标语言、范围（全文/指定区间）、格式等具体要求
- 材料文件：论文 PDF 或文本（路径见 case.json / task.md，**读实际文件，不凭标签猜内容**）

工作目录 `/app/work/`，最终产物 `/app/output/`：

| 产物 | 路径 | 说明 |
|---|---|---|
| 原文抽取清单 | `/app/work/source.json` | 每段一行：段号、页码、章节、类型、原文 |
| 锁定术语表 | `/app/output/terminology.tsv` | 源词→译名→首现位置→备注 |
| 双语对照 | `/app/output/bilingual.md` | 段级原文/译文对照 |
| 核验报告 | `/app/output/verification.md` | 四查结果与待人工确认清单 |
| 结构化结果 | `/app/output/result.json` | 见下 |

### result.json 必含字段

```json
{
  "case_id": "…",
  "status": "success | partial | cannot_judge | refused",
  "status_reason": "…",
  "main_result": { "translation": "…", "bilingual": "…", "terminology": "…" },
  "evidence": [ { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body", "sentence": "S1" } ],
  "uncertainty": { "unreported": [], "ambiguous": [], "untranslated": [] },
  "verification": { "terminology_ok": true, "paragraph_ok": true, "relation_ok": true },
  "change_log": ["…"]
}
```

若 `case.json` 声明了 `output_contract`，把它的**每个字段**原样并入 `main_result`，不得改名、漏项。

## 执行步骤（严格顺序）

### 第 1 步：读输入，划边界
读 `/input/case.json` 与 `/input/task.md`，确定：目标语言、翻译范围（全文还是某区间）、输出字段。记录 `case_id` 与材料路径。若范围是区间，先定位起始页与段落，只译区间内，但术语口径仍取全文。

### 第 2 步：抽取原文并编号
读材料实际文件，抽取全文文本，保留结构。给每个**语义段落**分配稳定 `para_id`（P1、P2…），规则见 `resources/bilingual_schema.md`。关键规则：
- 按阅读顺序编号，跨页、跨栏、跨章节的续段**合并为一段**并标注接续位置；
- 图注、表头、公式块、文献条目是独立段，用 `kind` 区分 `body/heading/caption/table/formula/reference`；
- 每段记录 `page`、`section`、`sentence` 起止，写入 `/app/work/source.json`。

### 第 3 步：建术语表并锁定
从标题、摘要、正文、图注、结论抽取领域术语与缩写，为每个术语定**唯一译名**，写入 `/app/output/terminology.tsv`（格式见 `resources/terminology_schema.md`）。
**锁定后再翻译**：翻译中只准用术语表里的译名；遇到新术语先回填术语表（源词、译名、首现位置）再用。全篇"先锁定、后使用、遇新回填"。

### 第 4 步：逐段翻译（硬约束）
逐段翻译，携带"上一段要点 + 当前活动术语表"。每段必须遵守：
- **数字与单位**：数值、量纲、误差、区间符号（±、~、≤、≥、×、^）原样保留；不换算单位、不四舍五入。
- **公式**：公式内容与编号保留，只译包围文字。
- **编号**：文献 `[1]`、图 `Fig. 3`、表 `Table 2`、公式 `Eq. (4)` 原样保留。
- **否定与限定**：not / only / unless / at least / at most / no / without / approximately / up to 精确译出，不丢、不反。
- **指代**：this / it / they / former / latter / the former / the latter 指代不明时译成显式名词（如"该方法""前者（X）"）。
- **因果与让步**：because / due to / although / despite / whereas / however 关系保留。
- **术语**：一律用锁定译名，禁止临时改译；缩写首次给出全称，之后保持。

### 第 5 步：双语对照输出
每段输出一行：`para_id | 原文 | 译文 | 页码 | 章节 | 类型 | 备注`，写入 `/app/output/bilingual.md`（格式见 `resources/bilingual_schema.md`）。译不准、保留原文、OCR 存疑处显式标注 `【未译】/【待确认】/【OCR 存疑】`，不静默跳过。

### 第 6 步：译文核验（四查）
按 `resources/verification_checklist.md` 逐项核对，结果写入 `/app/output/verification.md`：
1. **术语稳**：同一术语在标题/摘要/正文/图注/结论中译名一致；术语表条目齐全、无空译名。
2. **段落全**：`para_id` 数量与顺序同 `source.json` 一致，无漏段、重段、错位；跨页/跨栏接续正确。
3. **关系准**：数字、单位、公式、图表与文献编号、否定限定、指代、因果让步与原文一致。
4. **可核验**：每段译文有页码/段落/句子定位；未译、存疑项已标注并列入 `uncertainty`。

核验发现问题就地修正；无法判定者列入 `uncertainty.ambiguous`，不写成事实。

### 第 7 步：写结构化结果
写 `/app/output/result.json`（结构见上）。`status` 取值：全部完成 `success`；有缺漏/存疑 `partial` 并在 `status_reason` 说明；材料冲突 `cannot_judge`；材料缺失 `refused`。`evidence` 至少覆盖每个关键结论的定位；`change_log` 记录锁定、回填、修正等关键动作。

## 异常处理

按 `resources/error_handling.md` 处置：文字层缺失→OCR；公式/表格为图片→保留并标注；参考文献无法解析→原样保留；原文残缺→`partial` 并写明；材料缺失→`refused`。**不编造原文没有的内容。**

## 资源

- `resources/terminology_schema.md`：术语表格式、锁定/回填/验证规则
- `resources/bilingual_schema.md`：段号生成、段落对齐、双语对照与 evidence 格式
- `resources/verification_checklist.md`：四查清单
- `resources/error_handling.md`：异常处理手册
- `resources/usage.md`：使用与方法说明、最小调用示例

## 最小调用示例（示意，非正式案例）

输入 `case.json`：`{"case_id": "demo", "task": "翻译摘要为中文"}`，`task.md`：`目标语言=中文，范围=摘要`。
执行：读输入 → 抽摘要段（P1）→ 锁术语 → 译 P1 → 四查 → 写结果。
输出 `result.json`：`status:"success"`，`main_result.translation` 为摘要译文，`evidence:[{para_id:"P1", page:1, section:"Abstract", kind:"body"}]`。
