# RTL Agent Challenge

RTL 本地智能体设计赛道 — VerilogEval v2 自动化评测与优化

## 赛道信息

- **赛道：** 3.1 RTL/HLS 本地智能体设计赛道（RTL 子赛道）
- **模型：** QiMeng-SALV-7B（LoRA v2 合并权重）
- **数据集：** VerilogEval v2（dataset_spec-to-rtl，156 题）
- **运行环境：** AMD ROCm 云算力，单卡 32GB

## 环境说明

- **算力平台：** AMD ROCm 云算力（单卡 32GB）
- **推理框架：** vLLM (ROCm 版)，chat 接口，模型名 `salv_v2`
- **仿真工具：** Icarus Verilog v12 + vvp
- **综合工具：** Vivado 2025.2 (xczu3eg-sbva484-1-e, 时钟 5ns)

## 系统架构

增益分两层：**确定性题面解析**（主来源）+ **Agent 闭环**（兜底）。

```
题目 → classifier 分类 → structured 结构化解析
     ├─ 命中 → 直接合成 Verilog（不经模型）
     └─ 未命中 → vLLM chat（引导解码）
   → iverilog v12 编译 + vvp 仿真 → 判分
   → 失败 → 错误摘要注入重试（最多 5 轮，温度 0.3×5）
```

## 目录结构

```
rtl-agent-challenge/
├── data/                  # VerilogEval v2 数据集（156题）
│   ├── spec-to-rtl/       # 原始数据集
│   └── out_baseline/      # baseline 生成的 .v 文件
├── agent/                 # Agent 核心代码（待 A 入库）
│   ├── runner.py          # Agent 主循环（iverilog + Vivado 双后端）
│   ├── structured.py      # 确定性题面解析（26 个解析器）
│   ├── classifier.py      # 题型分类
│   ├── prompts.py         # 分类模板 + 重试提示
│   └── error_parser.py    # 编译/仿真错误解析
├── tests/                 # 变体测试与判分回归（待 A 入库）
├── model/                 # 模型相关配置
├── prompts/               # 提示词模板
├── fewshot/               # few-shot 示例
├── results/               # 评测结果 CSV
├── skill/                 # 技能包 / 踩坑记录 / 解析机制
├── report/                # 设计报告
├── Dockerfile             # Docker 打包
└── requirements.txt       # Python 依赖
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 vLLM（ROCm 版，模型名 salv_v2）

# 3. 评测（结构化解析 + Agent 闭环）
python run_agent.py

# 对照：回退纯模型（关闭结构化解析）
STRUCTURED_SPEC=0 python run_agent.py
```

> 编译需三文件一起：`生成代码.sv + *_ref.sv + *_test.sv`。模块名必须为 `TopModule`，禁用 `always_ff/always_comb/always_latch`。

## 关键指标（定稿 FULL05）

| 指标 | 基线 | FULL05A |
|---|---|---|
| 全量 156 题 pass@5 | 60.9% | **76.9%** |
| 未见 49 题 pass@5 | 57.1% | **95.9%** |

> `pass@5` = 最多五次带反馈尝试中至少一次通过。93.9%~95.9% 为本地诊断与回归成绩，**不是独立隐藏题成绩**。

## 团队分工

| 角色 | 负责内容 |
|------|----------|
| A · 杨心雨 | 模型、Agent 核心（runner/structured/classifier/error_parser/prompts）、评测与交付、Vivado 后端、Docker |
| B · 刘嘉睿 | 协作入口、提示模板、评测衔接 |
| C · 魏梓丞 | 仓库管理、数据集入库、文档/报告、技能包汇总 |