# Phase Prompts

以下提示词可以直接复制给 Codex。每次只运行一个阶段。

## Phase 1 — Frame

```text
阅读 AGENTS.md、competition/ 和 inputs/ 的全部内容。执行 Phase 1：完成 workspace/01_case_facts.md 与 workspace/02_issue_tree.md。所有陈述使用 FACT、ASSUMPTION、INFERENCE 或 RECOMMENDATION 标签。不得开展大规模外部研究。完成后运行 status，并停止在 Gate 1。
```

## Phase 2 — Research

```text
先确认 workspace/gates.yaml 中 Gate 1 已批准。执行 Phase 2：按决策价值填写研究计划、证据台账和假设台账。优先一手来源，逐条记录每个来源支持的结论。不要生成最终策略，完成后汇报最关键的证据缺口。
```

## Phase 3 — Decide

```text
基于已批准的问题定义和证据台账执行 Phase 3。提出至少三个实质不同的方案，先固定权重再评分，引用 Evidence ID，并填写 workspace/06_strategy_options.md。说明推荐方案与淘汰理由，然后停止在 Gate 2。
```

## Phase 4 — Build

```text
先确认 Gate 2 已批准。执行 Phase 4：定义可复算的财务模型，生成结论式 Ghost Deck，并补齐实施路线、KPI、风险和缓解措施。每个数字必须引用事实或 Assumption ID。
```

## Phase 5 — Defend

```text
执行 Phase 5。先以怀疑型评委身份寻找最可能导致淘汰的漏洞，再完成 Q&A Bank 和 Rubric Review。运行 python3 tools/run_workflow.py check。修复 ERROR；列出仍存在的 WARNING。停止在 Gate 3，不得自行批准提交。
```

## 研究任务分配

```text
根据 inputs/team-profile.yaml 和 workspace/03_research_plan.md 分配任务。避免重复研究；每个任务必须写明 owner、截止时间、预期来源、交付格式和停止条件。优先分配会改变策略选择的高价值问题。
```

## Red Team

```text
忽略礼貌性反馈，以淘汰评审视角审查当前方案。分别从问题定义、数据可信度、因果推理、财务模型、执行能力、风险、伦理和替代方案提出攻击。每个问题标记严重度、现有证据、缺口与最低修复动作。
```

