# RTL Agent Challenge

RTL 本地智能体设计赛道 — VerilogEval v2 自动化评测与优化

## 赛道信息

- **赛道：** 3.1 RTL/HLS 本地智能体设计赛道（RTL 子赛道）
- **模型：** QiMeng-SALV-7B（基于 Qwen2.5-Coder-7B 的 Verilog 强化学习模型）
- **数据集：** VerilogEval v2（dataset_spec-to-rtl，156 题）
- **运行环境：** AMD ROCm 云算力，单卡 32GB

## 环境说明

- **算力平台：** AMD ROCm 云算力（单卡 32GB）
- **推理框架：** vLLM (ROCm 版)
- **模型：** QiMeng-SALV-7B (Qwen2.5-Coder-7B)
- **仿真工具：** Icarus Verilog v12
- **综合工具：** Vivado 2025.2 (xczu3eg-sbva484-1-e, 时钟 5ns)

## 目录结构

```
rtl-agent-challenge/
├── data/                  # VerilogEval v2 数据集（156题）
│   ├── spec-to-rtl/       # 原始数据集
│   └── out_baseline/      # baseline 生成的 .v 文件
├── agent/                 # Agent 核心代码
│   ├── baseline.py        # 基线生成脚本
│   ├── evaluate.py        # 评测脚本
│   ├── agent.py           # Agent 重试循环
│   └── error_parser.py    # 错误解析器
├── model/                 # 模型相关配置
├── prompts/               # 提示词模板
├── fewshot/               # few-shot 示例
├── results/               # 评测结果（baseline.csv, agent.csv 等）
├── skill/                 # 技能包 / 踩坑记录
├── report/                # 设计报告
├── Dockerfile             # Docker 打包
└── requirements.txt       # Python 依赖
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 基线测试
python agent/baseline.py

# 3. 评测
python agent/evaluate.py

# 4. Agent 重试
python agent/agent.py
```

## 团队分工

| 角色 | 负责内容 |
|------|----------|
| A | 模型部署、baseline.py、agent.py、Vivado适配、Docker打包 |
| B | evaluate.py、提示词设计、few-shot、失败分析 |
| C | 仓库管理、数据集入库、文档/报告、技能包汇总 |
