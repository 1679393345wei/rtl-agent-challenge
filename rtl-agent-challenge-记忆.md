# RTL Agent Challenge — 项目记忆

> 本地记忆文件（团队参考用，不必提交 GitHub）
> 最近更新：2026-10-08

---

## 一、项目要求

### 1.1 基本定位

| 项 | 内容 |
|---|---|
| 赛道 | 3.1 RTL/HLS 本地智能体设计赛道 · RTL 子赛道 |
| 模型 | QiMeng-SALV-7B（LoRA v2 合并权重） |
| 数据集 | VerilogEval v2 · spec-to-rtl，156 题 |
| 评测工具 | iverilog（v12.0）+ vvp；综合后端 Vivado 2025.2 |
| 仓库 | https://github.com/1679393345wei/rtl-agent-challenge |
| 本地路径 | C:\Users\16793\Desktop\rtl-agent-challenge |
| 服务器 | yangxy@10.29.6.121 |
| A 的工作目录 | /home/yangxy/yangxy_agent（模型 + Agent 核心） |
| B 的工作目录 | /home/yangxy/ljr-rtl-agent（提示词 + 评测，**禁止修改**） |

### 1.2 团队分工

| 角色 | 负责内容 |
|---|---|
| A · 杨心雨 | 模型、Agent 核心（runner/structured/classifier/error_parser/prompts）、评测与交付、Vivado 后端、Docker |
| B · 刘嘉睿 | 协作入口、提示模板、评测衔接 |
| C · 我 | 仓库管理、数据集入库、文档/报告、技能包汇总 |

### 1.3 硬性规则（红线）

**文件命名/目录：**
- 目录与文件名必须纯英文（Docker / 赛事平台要求）。
- `.gitignore` 已忽略模型权重（`*.bin`、`*.safetensors`、`*.pt` 等）与 `results/*.csv`、`data/out_baseline/*.v`、`*.log`。

**数据口径（已统一）：**
- 统一以 `problem_classification.csv` 为准：组合 81 / 时序 38 / FSM 29 / 综合 8。
- 所有 results CSV 已同步更新 category 列（2026-09-25）。
- 差异来源：8 道"纯组合 FSM 题"（Prob079/091/099/100/134/135/143/150）原被 results 脚本按名称归为 fsm，实际为纯组合逻辑。

**指标口径（务必区分）：**
- `pass@5`：最多五次带反馈尝试中至少一次通过（Agent 工作流成功率）。
- `首发通过率`（CSV 记作 `pass_at_1`）：第一次尝试即通过。
- 两者都**不能**等同于论文用多次独立采样估计的 `pass@k`。引用时必须标明。

**虚拟机操作红线（SSH 上只读优先）：**
1. 禁止破坏性命令：`rm -rf`、`find -delete`、`git reset --hard`、`mkfs/dd/fdisk`、`chmod -R`、`chown -R`。
2. 模型与权重只读：`models/` 及软链接指向的 `SALV-7B` 目录（尤其 `config.json` 的 `rope_scaling` 字段）禁止任何写操作。
3. 既有结果只读：`results/`（`baseline*.csv`、`agent_verified*.csv` 等）不覆盖、不追加；新结果用全新文件名并先征得同意。
4. 禁止系统级操作：`sudo apt upgrade/remove`、`reboot`、`shutdown`、改系统配置、装/卸系统包。
5. **保护运行进程/GPU：禁止 `pkill -u yangxy -f python` 等全用户击杀**；禁止抢占 GPU 长跑。评测前先查 `nvidia-smi` 与他人占用。
6. 不明文件（`nips/`、`images/`、`agent_eval_wide`、`baseline_evidence` 等）只读，不删不改不搬。
7. 一切破坏性/不可逆操作：先列清单 + 显式确认，绝不自动执行。
8. 数据不外传：虚拟机上的数据/模型/结果禁止上传到外部服务。
9. 探索/核对一律先用 `ls/cat/head/grep/tree` 等只读命令。

**评测约定：**
- 编译需三文件一起：`生成代码.sv + *_ref.sv + *_test.sv`。
- 模块名必须为 `TopModule`；禁用 `always_ff/always_comb/always_latch`（iverilog 支持不完整）。
- 评测脚本自带防覆盖与 `--resume` 断点续跑，勿绕过；使用唯一 `RUN_TAG`，严禁并发评测。

---

## 二、进度

### 2.1 精度（定稿 FULL05，A 侧，2026-10-02）

| 指标 | 基线（纯模型） | FULL05A | FULL05B |
|---|---|---|---|
| 全量 156 题 pass@5 | 60.9%（95/156） | **76.9%（120/156）** | 76.3%（119/156） |
| 未见 49 题 pass@5 | 57.1%（28/49） | **95.9%（47/49）** | 93.9%（46/49） |
| 已见 107 题 pass@5 | 62.6%（67/107） | 68.2%（73/107） | 68.2%（73/107） |
| 未见 49 题首发通过率 | — | 93.9%（46/49） | 89.8%（44/49） |
| 已见 107 题首发通过率 | — | 65.4%（70/107） | 63.6%（68/107） |

> 增益：未见 49 题 **+36.7~38.8pp**；已见 107 题 +5.6pp。全量含训练题记忆，不作泛化主指标。
> **证据限制**：49 道「未见」题未进 LoRA 训练，但已反复参与解析规则开发，属本地诊断成绩，非独立隐藏题成绩。

### 2.2 定稿配置（A 侧）

| 项 | 值 |
|---|---|
| 权重 | `/home/yangxy/salv_lora_v2_merged` |
| 接口 | vLLM chat；模型名 `salv_v2`；`127.0.0.1:8001` |
| 生成预算 | 温度 0.3 × 5；`top_p=0.95`；`max_tokens=1024` |
| 输出约束 | `guided_regex=(?s)module\s+TopModule.*endmodule` |
| 结构化开关 | `STRUCTURED_SPEC=1`（默认）；0 回退纯模型 |
| 后端 | iverilog v12 + vvp；编译 30s、仿真 60s 超时 |
| 运行目录 | `/home/yangxy/yangxy_agent`；conda `ljr-salv` |

### 2.3 增益结构（核心认知更新）

**增益主来源已从「提示词工程」变为「确定性题面解析」。**

| 层 | 机制 | 载体 | 贡献 |
|---|---|---|---|
| 确定性层 | 26 个题面解析器 | `agent/structured.py` | 主要泛化增益 |
| 模型层 | 引导解码 + 分类模板 + 5 轮反馈重试 | `agent/runner.py`、`prompts.py` | 兜底与边际改善 |
| 已证伪 | FSM few-shot / 温度多样化 / 专用提示词 | — | 无稳定收益，已回退 |

### 2.4 评测口径（C/B 侧 · 统一口径 pass@1）

| 项 | 值 |
|---|---|
| 基线（裸模型） | 51.92%（81/156） |
| Agent 定稿（v12） | 58.33%（91/156） |
| 总增益 | +6.41pp（净 +10 题） |
| 稳定性（同模板 3 跑） | 55.13% / 58.97% / 56.41%（平均 56.84%，标准差 1.60%，最大差 3.85%） |

分项通过率（统一口径 81/38/29/8）：

| 类别 | 基线 | Agent | 变化 |
|---|---|---|---|
| 组合（81题） | 70.37%（57/81） | 72.84%（59/81） | +2.47 ↑ |
| 时序（38题） | 36.84%（14/38） | 63.16%（24/38） | +26.32 ↑ |
| FSM（29题） | 31.03%（9/29） | 20.69%（6/29） | **-10.34 ↓（唯一倒退）** |
| 综合（8题） | 12.50%（1/8） | 25.00%（2/8） | +12.50 ↑ |

### 2.5 各负责人进度

**A · 杨心雨：** Agent 主循环、结构化解析（26 函数）、分类器、提示词库、错误解析器、引导解码、iverilog v12 升级、Vivado 后端、双轮评测与证据链、交付打包 —— 全部 100%。**仅剩 ROCm 32GB / Docker 实机验收待做。**

**B · 刘嘉睿：** 提示词 B_v8（B 系列消融内峰值 58.97%）；稳定性三次实验；交付物已入库。

**C · 我：** 文档/技能包 + 交付整理 100%；2026-10-08 依据 A 的 10-07 交接总结完成报告与技能包修订。

### 2.6 已停止的路线（重要负结果）

| 路线 | 结果 |
|---|---|
| 增加 140 条 repair 训练样本 | v3 25/49，51.0%；低于 v2，弃用 |
| LoRA rank 8 → 32 | v4 27/49，55.1%；未提高泛化，弃用 |
| 改重试诊断提示 | 两轮均 26/49，对照 28/49；已回退 |
| 温度多样化、FSM few-shot | 无稳定收益；保留 0.3×5 |
| FSM 专用提示词（C 侧独立复测） | 全部低于无提示词对照（~41% vs 17%~31%），规则越多越差 |

### 2.7 剩余 3 道未解题

| 题目 | 归因 |
|---|---|
| Prob053_m2014_q4d | 无复位 XOR 反馈触发器未指定初值（题面缺失） |
| Prob099_m2014_q6c | 题面/参考输出 Y1/Y3，测试连接 Y2/Y4（测试接口缺陷） |
| Prob136_m2014_q6 | reset 端口存在但题面未明确复位目标 |

---

## 三、2026-10-08 本次修订内容

| 文件 | 修订 |
|---|---|
| `report/design_report.md` | 全文重写：新架构（结构化解析层）、FULL05 分层精度、已证伪路线、3 道剩余题、ROCm/Docker 交付限制 |
| `report/progress_report.md` | 全文重写：补入 FULL05 精度演进、定稿配置、评测可信度修复、停止路线、进度表 |
| `report/checklist.md` | 更新提交物状态；新增 A 侧 FULL05 CSV 待入库项；补指标口径备忘 |
| `README.md` | 目录结构对齐新架构（runner/structured/classifier/error_parser）；新增关键指标 |
| `skill/README.md` | 新增 `structured_parsing.md` 索引；新增「增益结构速览」；补充失效条件 |
| `skill/structured_parsing.md` | **新增**：26 个解析器分类、触发机制、验证方式、失效条件 |
| `skill/prompts_cookbook.md` | 第六节重写：FSM 专用提示词结论反转（独立复测推翻原结论） |
| `skill/pitfalls_phase3.md` | insight-03/05 标注已推翻；经验总结重写（新增「对照口径决定结论」） |
| `rtl-agent-challenge-记忆.md` | 本文件 |

---

## 四、待办

| 事项 | 归属 | 状态 |
|---|---|---|
| A 侧源码入库（runner/structured/classifier/error_parser/prompts + tests/） | A | 待做 |
| FULL05 两份 CSV + `run_config.json` 交付 C 入库 | A | 待做 |
| ROCm 32GB / Docker 实机断网验收 | A | 待做 |
| 独立题集与题面变体验证 | A | 待做（优先级 1） |
| 通用解析器审计与阴性测试 | A | 待做（优先级 3） |
| B 的交付物整理入库 | C | ✅ 已完成（2026-09-25） |
| 分类口径统一 | C | ✅ 已完成（2026-09-25） |
| 报告与技能包按最新进展修订 | C | ✅ 已完成（2026-10-08） |
| .gitignore 调整（results CSV / logs 是否入库） | C | 待确认 |
| git add → commit → push 同步 GitHub | C | 待确认（对外可见，需明确授权） |

---

## 五、注意事项

- `data/out_baseline/`、`fewshot/`、`agent/`、`prompts/` 下目前是 `.gitkeep` 占位，实际内容等 A/B 入库。
- `results/`、`skill/prompts/`、`scripts/`、`logs/` 已有 B 的交付物，但 `.gitignore` 默认忽略 `results/*.csv` 和 `*.log`，如需入库需调整 `.gitignore`。
- 改完文件后需 `git add → git commit → git push` 才能同步到 GitHub；push 是对外可见操作，需用户明确确认。
- 本记忆文件为中文名，提交 GitHub 前决定去留（目录要求纯英文）。
- B 的交付包中 fewshot/ 目录为空（无示例文件），logs/ 仅有 stability_r3.log（r1/r2 缺失）。
- **A 的目录 `/home/yangxy/yangxy_agent` 与 B 的 `/home/yangxy/ljr-rtl-agent` 是两套独立代码**，不要混用；B 目录禁止修改。
- 服务器当前（2026-10-08 查）：两卡 GPU 空闲（1 MiB / 0%），vLLM 未运行，A 侧目录最新代码为 10-02。
- **FULL05 的 CSV 与 traces 不在服务器上**（A 本地），如需入库要向 A 索取。