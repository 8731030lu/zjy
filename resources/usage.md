# 使用与方法说明

## 是什么
`literature-translation` 是一个把科研论文翻译为**可核验双语对照**的 Skill：锁定术语表并全篇回填、段落级对齐、保护数字/单位/公式/文献编号、逐段指回原文证据。验收四口径：术语稳、段落全、关系准、可核验。

## 适用场景
- 科研论文全文 / 摘要 / 章节 / 指定段落区间的翻译；
- 双语段落对照、术语一致性翻译、长文分段续译；
- 译文核验与修改建议。

## 调用方式
1. 环境挂载输入：`/input/case.json`（`case_id` + 任务 + 材料路径 + `output_contract`）、`/input/task.md`（目标语言、范围、格式）、材料 PDF/文本。
2. 加载本 Skill（`SKILL.md` + `resources/`）。
3. Agent 按 SKILL 七步执行：读输入 → 抽原文编号 → 建术语表锁定 → 逐段翻译 → 双语对照 → 四查核验 → 写 `result.json`。

## 输入要求
- 材料为 PDF（含文字层）或纯文本；扫描件走 OCR（质量差处标注）。
- `task.md` 需写清：目标语言、翻译范围、输出字段（如有）。

## 输出
- `/app/output/bilingual.md`：段级原文/译文对照。
- `/app/output/terminology.tsv`：锁定术语表。
- `/app/output/verification.md`：四查报告 + 待人工确认清单。
- `/app/output/result.json`：结构化结果（`case_id`、`status`、`main_result`、`evidence`、`uncertainty`、`verification`、`change_log`）。

## 关键方法
1. **术语表锁定 + 回填**：先抽术语定唯一译名，翻译只用表内译名，遇新术语回填后再用（保证术语稳）。
2. **段落级对齐**：按阅读顺序编号 `para_id`，跨页/跨栏/跨章节续段合并（保证段落全）。
3. **硬约束翻译**：数字单位、公式、图表/文献编号、否定限定、指代、因果让步逐项保护（保证关系准）。
4. **证据定位 + 显式标注**：每段译文指回页码/段落/句子，未译与存疑显式标注（保证可核验）。

## 限制与失败处理
- 无文字层/模糊扫描件 → OCR，存疑标注；公式/表格为图片 → 保留并标注；参考文献无法解析 → 原样保留。
- 原文残缺 → `status: partial` 并写明限制；材料缺失 → `status: refused`。
- 不编造原文没有的数据或内容。

## 自查方法
- 按 `resources/verification_checklist.md` 四查：术语稳、段落全、关系准、可核验。
- 抽查标题/摘要/正文/图注/结论五处术语译名一致性。

## 最小调用示例（示意，非正式案例）

输入 `/input/case.json`：
```json
{ "case_id": "demo-001", "task": "翻译摘要", "material": "demo.pdf" }
```

输入 `/input/task.md`：
```
目标语言：中文；范围：摘要；输出：译文 + 术语表 + 证据定位。
```

Agent 执行后，`/app/output/result.json`（示意输出）：
```json
{
  "case_id": "demo-001",
  "status": "success",
  "status_reason": "摘要翻译完成",
  "main_result": { "translation": "（摘要译文）……" },
  "evidence": [ { "para_id": "P1", "page": 1, "section": "Abstract", "kind": "body", "sentence": "S1" } ],
  "uncertainty": { "unreported": [], "ambiguous": [], "untranslated": [] },
  "verification": { "terminology_ok": true, "paragraph_ok": true, "relation_ok": true },
  "change_log": ["锁定术语：beamforming→波束成形"]
}
```

> 以上输入与输出均为**示例**，用于说明接口与流程，不冒充正式案例结果。
