# CaseFlow — Business Case Competition Strategy Agent

CaseFlow 是一个为 Business Case Competition 设计的轻量级 Agent 工作流。它让 Codex 按固定阶段完成读题、研究、策略比较、财务验证、Deck 故事线和答辩压力测试，并在关键决策处等待团队确认。

## 你会得到什么

- 强制区分事实、假设、推论与建议
- 从 Case Brief 到 Issue Tree 的固定流程
- 证据台账、假设台账与决策日志
- 至少三个策略方案的可解释评分
- 财务模型规范与敏感性检查
- Ghost Deck、Rubric Review 与 Q&A Bank
- 三个人工审批 Gate，避免 Agent 擅自决定

## 5 分钟开始

1. 把 Case Brief、规则和评分标准放进 `inputs/case-brief/`。
2. 填写 `competition/rules.yaml` 与 `inputs/team-profile.yaml`。
3. 在终端运行：

```bash
cd CaseFlow
python3 tools/run_workflow.py init --case-name "Competition Case"
python3 tools/run_workflow.py status
```

4. 在 Codex 中输入：

```text
请阅读 AGENTS.md，从 Phase 1 开始。读取 inputs/case-brief/ 的全部材料，只完成 workspace/01_case_facts.md 和 workspace/02_issue_tree.md。完成后停止在 Gate 1，不要继续研究。
```

5. 团队确认问题定义后：

```bash
python3 tools/run_workflow.py gate 1 --approve --by "Team"
```

## 流程与检查点

| 阶段 | 主要产物 | 人工检查点 |
|---|---|---|
| Phase 1 Frame | Case Facts、Issue Tree、Day-1 Hypotheses | Gate 1：问题定义 |
| Phase 2 Research | Research Plan、Evidence Ledger、Assumptions | — |
| Phase 3 Decide | Strategy Options、推荐方案 | Gate 2：最终方向 |
| Phase 4 Build | 财务模型、Ghost Deck、实施方案 | — |
| Phase 5 Defend | Red Team、Rubric Review、Q&A | Gate 3：提交批准 |

## 常用命令

```bash
python3 tools/run_workflow.py status
python3 tools/run_workflow.py check
python3 tools/run_workflow.py gate 1 --approve --by "Hexin"
python3 tools/run_workflow.py gate 2 --approve --by "Team"
python3 tools/run_workflow.py gate 3 --approve --by "Team"
python3 tools/run_workflow.py gate 2 --reopen --by "Team"
```

`check` 检查结构、规则、证据和数字追踪性，但不会替代人工判断。

## 比赛前彩排

建议先用往届公开 Case 完整跑一次：记录每阶段耗时、无用输出、缺失证据和评委最容易攻击的地方。正式比赛前，只优化真实痛点，不扩张成网站或复杂多 Agent 系统。

## AI 使用边界

如果 `competition/rules.yaml` 中的 `ai_policy.status` 仍为 `UNKNOWN` 或为 `PROHIBITED`，校验会失败。正式使用前必须以当届官方规则为准。
