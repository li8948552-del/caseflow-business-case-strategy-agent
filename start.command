#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "CaseFlow — Business Case Competition Strategy Agent"
echo
python3 tools/run_workflow.py status
echo
echo "下一步："
echo "1. 把 Case Brief 和规则放入 inputs/case-brief/"
echo "2. 填写 competition/rules.yaml"
echo "3. 复制 prompts/phase_prompts.md 中的 Phase 1 提示词给 Codex"
echo
read -r -p "按回车关闭..." _
