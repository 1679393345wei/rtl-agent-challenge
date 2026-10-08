# 技能包（skill）汇总

> 本目录汇集 RTL 智能体项目的全部「技能」资产：结构化解析机制、提示词模板、踩坑清单、基线分析、增益数据与提示词库。
> 用于赛事提交的「技能包」部分，配合 `report/design_report.md` 说明适用范围与失效条件。

## 目录索引

| 文件 | 阶段 | 内容 | 状态 |
|---|---|---|---|
| `pitfalls_phase0.md` | 阶段0 | 环境搭建踩坑：ROCm/vLLM/iverilog/模型加载/温度 7 项 | ✅ 完成 |
| `baseline_findings.md` | 阶段1 | 裸模型 156 题基线：总体 pass@1、分项强弱、失败分布 | ✅ 完成 |
| `pitfalls_phase2.md` | 阶段2 | Agent 重试循环踩坑：错误提取/上下文/温度/超时 | ✅ 完成 |
| `gain_visualization.md` | 阶段2 | 基线 vs Agent 增益、逐题翻转、消融、稳定性数据 | ✅ 完成 |
| `structured_parsing.md` | 阶段3+ | **确定性题面解析机制：26 个解析器分类、触发条件、验证与失效条件** | ✅ 新增 |
| `prompts_cookbook.md` | 阶段3 | 四类提示词模板全文 + 版本演化 + 最佳版本结论 | ✅ 完成 |
| `pitfalls_phase3.md` | 阶段3 | 提示词调试经验：有效/无效做法 | ✅ 完成 |

> 提示词模板原文与 few-shot 示例分别位于根目录 `prompts/` 与 `fewshot/`（由队员 B 提供）。
> 失败分析的详细推理在 `report/fsm_failure_analysis.md`（FSM 根因）与 `report/design_report.md`（整体）。

## 增益结构速览

系统的增益分两层，技能包也按此组织：

| 层 | 机制 | 载体 | 贡献 |
|---|---|---|---|
| 确定性层 | 题面结构化解析（26 个解析器） | `agent/structured.py`，见 `structured_parsing.md` | 主要泛化增益（未见 49 题 +36.7~38.8pp） |
| 模型层 | 引导解码 + 分类模板 + 5 轮反馈重试 | `agent/runner.py`、`agent/prompts.py`，见 `prompts_cookbook.md` | 兜底与边际改善 |
| 已证伪 | FSM few-shot / 温度多样化 / 专用提示词 | `pitfalls_phase3.md` | 无稳定收益，已回退 |

## 适用范围与失效条件

- **适用范围**：VerilogEval v2（spec-to-rtl）数据集，QiMeng-SALV-7B（LoRA v2 合并权重），iverilog v12 编译仿真链路。
- **失效条件（需注意）**：
  1. **结构化解析按题面特征触发，不按题号查答案**；但换数据集后，解析器的触发模式可能过宽或失效，需重新审计（阴性测试）。
  2. 换模型或换仿真工具（如 Vivado）后，`always_ff` 等语法约束的有效性可能改变，需重新验证（详见设计报告）。
  3. 提示词模板依赖 `iverilog` 的判题与 VPI 输出格式，切到 Vivado 后错误解析器需适配。
  4. 8 道「纯组合 FSM」题的特殊处理针对当前数据集的固定特征，换数据集需重新识别。
  5. 波形推断类解析器只能得到「与有限观察一致」的候选行为，**不保证唯一电路**。