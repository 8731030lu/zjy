# 文献翻译 Skill（玻尔产品周赛·北化分站赛第一期）

可被 Agent 调用的科研论文翻译 Skill，把论文翻译为**可核验的双语对照结果**。

## 核心能力
- **术语稳**：术语表锁定 + 全篇回填，同一术语全文使用同一译名
- **段落全**：段落级对齐，跨页/跨栏/跨章节续段合并，不漏不重不错位
- **关系准**：数字/单位/公式/图表编号/文献编号/否定限定/指代逐项保护
- **可核验**：每段译文指回原文页码/段落/句子，未译与存疑显式标注

## 文件
- `SKILL.md`：Skill 本体（七步工作流 + 硬约束）
- `resources/terminology_schema.md`：术语表格式与锁定规则
- `resources/bilingual_schema.md`：段落编号、对齐与双语对照格式
- `resources/verification_checklist.md`：四查核验清单
- `resources/error_handling.md`：异常处理手册
- `resources/usage.md`：使用与方法说明、最小调用示例
