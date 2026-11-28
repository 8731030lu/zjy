---
name: literature-translation
description: 将科研论文翻译为可核验的双语对照结果：术语表锁定并全篇回填、段落级对齐、保护数字单位公式与文献编号、逐段指回原文证据、四查核验。用于文献翻译、双语对照、术语一致性翻译、长文分段续译与译文核验。
---

# 文献翻译 Skill（术语表驱动 + 段落级双语对照）

把一个真实科研论文（或指定段落区间）翻译为**可复核的双语对照结果**。验收只有四个口径：**术语稳、段落全、关系准、可核验**。

**主攻方向（明确聚焦）**：**术语表驱动翻译 + 段落级双语对照**。
- 术语表是"先锁定、后使用、遇新回填、译后审计"的**硬机制**，不是写在提示里的口号；
- 双语对照保留**段号与句子边界**，支持定位回看、逐段修改与引用核对；
- 关系准、可核验作为内置的**强制核验门槛**，任何一项不过即修正后重核。

## 输入与输出

环境提供：`/input/case.json`（`case_id`、任务、材料路径、`output_contract`）、`/input/task.md`（目标语言、范围、格式）、材料文件（PDF/文本，**读实际文件，不凭标签猜内容**）。

工作目录 `/app/work/`，最终产物 `/app/output/`：

| 产物 | 路径 | 说明 |
|---|---|---|
| 原文抽取清单 | `/app/work/source.json` | 每段：段号、页码、章节、类型、句子边界、原文 |
| 锁定术语表 | `/app/output/terminology.tsv` | 源词→译名→首现位置→备注 |
| 双语对照 | `/app/output/bilingual.md` | 段级 + 句级原文/译文对照 |
| 核验报告 | `/app/output/verification.md` | 四查结果（逐项过/不过）与待人工确认清单 |
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
  "change_log": ["锁定术语…", "分批翻译…", "核验修正…"]
}
```

若 `case.json` 声明了 `output_contract`，其**每个字段**原样并入 `main_result`，不得改名、漏项。

## 执行步骤（严格顺序，预算友好）

总预算 64 次请求、900 秒、单响应 ≤16384 token。**先求全文覆盖，再求局部精致**：读入→抽取→术语→分批翻译→对照→核验→输出，每阶段一次或几次请求，不逐段来回。

### 第 1 步：读输入，划边界（1–2 次）
读 `/input/case.json` 与 `/input/task.md`，确定目标语言、翻译范围、输出字段。记录 `case_id` 与材料路径。区间任务先定位起止页/段。

### 第 2 步：抽取并编号（一次完成）
读材料实际文件，抽取全文，写 `/app/work/source.json`。硬要求：
- 按阅读顺序给每个语义段 `para_id`（P1、P2…），跨页/跨栏/跨章节续段**合并**并标注接续；
- `kind` 区分 `body/heading/caption/table/formula/reference`，每类都要覆盖，**小段不可跳过**；
- 每段记录 `page`、`section`、`sentence` 起止（句子边界）。

### 第 3 步：建术语表并锁定（1–2 次）
从标题/摘要/正文/图注/结论抽术语与缩写，定唯一译名，写 `/app/output/terminology.tsv`（格式见 `resources/terminology_schema.md`）。完成后在 `change_log` 记"术语表已锁定（N 条）"。

### 第 4 步：分批翻译（硬约束）
把 `source.json` 的段落**分批**（每批 3–5 段，视单段长度与 token 余量），一批一次请求；批内逐段翻译，批间携带"上一批要点 + 锁定术语表"。每段遵守硬约束（见下）。**先翻完全文，再统一核验**。

### 第 5 步：双语对照输出
每段一行写 `/app/output/bilingual.md`（格式见 `resources/bilingual_schema.md`）：`para_id | 原文 | 译文 | 页码 | 章节 | 类型 | 句子边界 | 备注`。译不准/存疑处显式标注 `【未译】/【待确认】/【OCR 存疑】`。

### 第 6 步：四查核验（强制门槛）
按 `resources/verification_checklist.md` 逐项核验，把**每项的过/不过结果**写进 `/app/output/verification.md`：
1. **术语稳**：抽查标题/摘要/正文/图注/结论五处同一术语译名一致；术语表无空译名、无同源词多译名。
2. **段落全**：`bilingual.md` 的 `para_id` 数量与顺序 = `source.json`；无漏/重/错位。
3. **关系准**：数字/单位/公式/图表与文献编号/否定限定/指代/因果让步逐项与原文一致。
4. **可核验**：每段译文有页码/段落/句子定位；未译与存疑已标注并列入 `uncertainty`。
**发现不过项 → 就地修正 → 重新核验**，直到四查通过或无法判定（无法判定项列入 `uncertainty.ambiguous`）。

### 第 7 步：写结构化结果
写 `/app/output/result.json`。`status`：全完成 `success`；有缺漏/存疑 `partial` 并说明；材料冲突 `cannot_judge`；材料缺失 `refused`。`evidence` 覆盖**每个段落**；`change_log` 记录锁定、分批、回填、核验修正。

## 翻译硬约束（逐项必守）

- **数字与单位**：数值、精度、负号、误差、区间符号（±、~、≤、≥、×、^）原样；不换算、不四舍五入。
- **公式**：公式内容与编号保留，只译包围文字。
- **编号**：文献 `[1]`、图 `Fig. 3`、表 `Table 2`、公式 `Eq. (4)` 原样。
- **否定与限定**：not / only / unless / at least / at most / no / without / approximately / up to 不丢、不反。
- **指代**：this / it / they / former / latter 指代不明时译成显式名词（如"该方法""前者（X）"）。
- **因果与让步**：because / due to / although / despite / whereas / however 关系保留。
- **术语**：一律用锁定译名；缩写首现给全称，之后仅用缩写；专名保留原文。

## 异常与降级

按 `resources/error_handling.md` 处置。预算不足时按优先级降级：**① 全文段落覆盖 → ② 术语一致 → ③ 数字/公式/引用保护 → ④ 逐段证据**；每完成一阶段即写盘，失败仍有部分产物。不编造原文没有的数据或内容。

## 资源

- `resources/terminology_schema.md`：术语表格式、锁定/回填/审计规则
- `resources/bilingual_schema.md`：段号、句子边界、双语对照与 evidence 格式
- `resources/verification_checklist.md`：四查清单
- `resources/error_handling.md`：异常处理手册
- `resources/usage.md`：使用与方法说明、最小调用示例

## 最小调用示例（示意，非正式案例）

输入 `case.json`：`{"case_id": "demo", "task": "翻译摘要为中文"}`；`task.md`：`目标语言=中文，范围=摘要`。
执行：读输入 → 抽摘要段 → 锁术语 → 译 → 四查 → 写结果。
输出 `result.json`：`status:"success"`，`main_result.translation` 为译文，`evidence:[{para_id:"P1",page:1,section:"Abstract",kind:"body",sentence:"S1"}]`。
