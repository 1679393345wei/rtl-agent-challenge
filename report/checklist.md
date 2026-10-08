# 提交清单（checklist）

> 对应方案阶段4「提交清单检查」：核对工程包、技能包、设计报告、Docker 镜像，确认目录纯英文。
> 更新时间：2026-10-08

## 提交物核对

| # | 提交物 | 要求 | 状态 |
|---|---|---|---|
| 1 | 工程包 | 目录结构规范、纯英文命名、可复现 | 🟡 部分：A 侧源码与证据包已归档（`yangxy_agent_structured_final_20261002.tar.gz`），本仓库 `agent/` 仍为占位，待 A/B 入库 |
| 2 | 技能包 | `skill/` 下踩坑/分析/提示词库/解析机制齐全 | ✅ 完成（见 `skill/README.md`） |
| 3 | 设计报告 | `report/design_report.md` 覆盖方案要求的 8 大章节 | ✅ 完成（已按 10-07 最新进展修订） |
| 4 | Docker 镜像 | 可 `docker build` + 断网沙箱跑通 | ⬜ 待 A 提供 Dockerfile 与验证；需在 ROCm 32GB 实机验收 |
| 5 | 实测结果 | `results/*.csv` 与 FULL05 分层证据留档 | 🟡 C/B 统一口径 CSV 已入库；**A 的 FULL05 CSV 与 traces 仍在服务器/本地，未入库** |

## 纯英文命名检查

- 目录与文件名要求纯英文。当前所有正式提交物（`skill/*.md`、`report/*.md`、`prompts/`、`fewshot/`、`results/`）均满足。
- 注意：根目录 `rtl-agent-challenge-记忆.md` 为个人项目笔记，含中文文件名，**提交前请确认是否纳入仓库**（建议移出仓库或用 `skill/` 下的英文文档替代）。

## 复现路径自检

```bash
# 期望链路：结构化解析命中 → 直接产出；未命中 → vLLM 生成 → iverilog 编译仿真 → 输出 CSV
pip install -r requirements.txt
python run_agent.py            # 结构化解析 + Agent 闭环（STRUCTURED_SPEC=1）
# 对照：STRUCTURED_SPEC=0 python run_agent.py   # 回退纯模型
```

> `results/*.csv` 已被 `.gitignore` 过滤（数据量/敏感性考虑），报告中的关键数据以 `skill/` 与 `report/` 下的 markdown 存档为准。

## 待队友确认项

- [ ] A：`agent/` 下源码（runner.py / structured.py / classifier.py / error_parser.py / prompts.py）与 `tests/` 入库并跑通。
- [ ] A：`Dockerfile` 填写 + Vivado 适配 + ROCm 32GB 断网验证。
- [ ] A：FULL05 的两份 CSV（`val_FULL05A.csv`、`val_FULL05B.csv`）与 `run_config.json` 交付给 C 入库。
- [ ] B：`prompts/` 与 `fewshot/` 模板最终版入库（含 `prompts_b8` 备份）。
- [ ] C：确认 `results/*.csv` 与 `*.log` 是否纳入仓库（当前被 `.gitignore` 忽略），再决定是否 `git push`。

## 数据口径备忘

- 分类口径统一为 `problem_classification.csv`：**组合 81 / 时序 38 / FSM 29 / 综合 8**。
- 两种指标不可混用：`pass@5`（最多五次带反馈尝试）与 `首发通过率 pass_at_1`（首次尝试）。报告引用时须标明。