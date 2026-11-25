# 字段字典与证据锚点格式

本文件定义 `slides.json` 的字段与证据锚点格式，供 Agent 抽取论文内容时使用，保证多篇论文可并排比较、每条论断可回到原文。

## 论文卡片字段（留得住）

| 字段 | 说明 | 必填 |
|---|---|---|
| `paper.title` | 论文标题（原文） | 是 |
| `paper.authors` | 作者 | 是 |
| `paper.venue` | 期刊/会议/预印本 | 建议 |
| `paper.year` | 年份 | 建议 |
| `paper.doi` | DOI（原文有才写，不编造） | 否 |
| `summary.research_question` | 研究问题（一句） | 是 |
| `summary.key_finding` | 主要发现（一句） | 是 |
| `summary.contribution` | 贡献 | 建议 |
| `summary.data` | 数据/数据集（名称、规模、来源） | 建议 |
| `summary.methods` | 方法条件（模型、近似、参数、超参） | 是 |

## 幻灯片字段（对得上 / 找得回）

每章至少一页，`section` 必须与论文自身章节名一致，按原文顺序排列。

```json
{
  "title": "页标题",
  "section": "原文对应章节名",
  "bullets": [
    {"text": "关键论断", "anchor": "p.3¶2 · Fig.1", "evidence_status": "reported"}
  ],
  "speaker_notes": "本页讲稿"
}
```

- `evidence_status` 取值：
  - `reported` — 原文明确报告
  - `inferred` — 由原文推断（写明推断依据）
  - `unreported` — 原文未报告（不写成事实）
  - `uncertain` — 无法判断
  - `missing` — 图表/公式缺失

## 证据锚点格式（找得回）

锚点 = 页码 + 段落 + 图表/公式 +（可选）原文短引，用 `·` 分隔，短引用加引号。

```
p.3¶2 · Fig.1 · "The activation energy is 42.7 kJ/mol"
p.5¶1 · Table 2 · "λ = 532 nm"
p.8 · Eq.(4)
```

规则：
- 页码写 `p.N`；段落在页内计数写 `¶N`；图表写 `Fig.N` / `Table N` / `Eq.(N)`。
- 锚点必须指向真实位置；无法定位写 `anchor: null`，并把 `evidence_status` 设为 `unreported` 或 `uncertain`。
- 短引必须逐字来自原文；无原文短引时省略，不编造。

## 局限与边界字段（留得住 + 诚实）

```json
{"text": "…", "anchor": "p.9¶2", "status": "reported|inferred|unreported|uncertain"}
```

把「让结论成立的前提条件」和「原文未报告/无法判断/材料冲突」分开写明，不把推断写成事实。

## result.json 契约

`build_ppt.py` 会读取 `/input/case.json` 的 `output_contract`，把上述字段映射到全部要求的字段名，并附加：

- `case_id`：案例标识（必填，来自 case.json）
- `status`：`success` / `partial` / `unable` + 原因
- `sources` / `evidence`：每条论断的证据锚点
- `uncertainty`：未报告、推断、局限
- `artifacts`：产物路径清单
- `change_records`：做了什么、为什么
