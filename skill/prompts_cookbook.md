# 提示词库（prompts_cookbook）

> 来源：服务器 `~/ljr-rtl-agent/skill/prompts/` 及各版本备份目录
> 用途：整理四类题型提示词模板，说明设计思路、版本演化与最佳版本结论。

## 一、正确率最高的版本（结论）

**最佳提示词版本 = B_v8，pass@1 = 58.97%（92/156）**，为全部消融实验的峰值。

- **实验结果文件：** `results/prompt_B_v8.csv`
- **结果生成时间：** 2026-09-21 19:39（以结果文件时间戳为准）
- **对应提示词目录：** `skill/prompts_b8/`
- **关键特征：** 其 `system_fsm.txt` 为 **11 条规则**（比其他版本多 2 条 FSM 规则，见第五节）

> 注意：最终提交方案 `agent_verified_v12.csv` 用的是当前 `skill/prompts`（fsm 9 条），pass@1 = 58.33%，**略低于** B_v8 的 58.97%。差异集中在 FSM 类。

## 二、版本演化对照表

| 版本 | 结果时间戳 | pass@1 | FSM 分项 | FSM 模板规则数 |
|---|---|---|---|---|
| B_v2 | 09-21 11:41 | 44.23% | 10.81% | —（目录未保留） |
| B_v3 | 09-21 12:00 | 46.15% | 21.62% | — |
| B_v5 | 09-21 15:56 | 48.08% | 21.62% | — |
| B_v6 | 09-21 16:16 | 51.28% | 31.03% | —（分类表变更） |
| B_v7 | 09-21 16:36 | 55.77% | 20.69% | — |
| **B_v8** | **09-21 19:39** | **58.97%（峰值）** | **41.38%（FSM 峰值）** | **11** |
| B_v9 | 09-21 20:03 | 58.33% | 31.03% | 9 |
| B_v10 | 09-21 20:24 | 56.41% | 20.69% | 9 |
| B_v11 | 09-21 20:41 | 54.49% | 17.24% | 11（温度 0.2） |
| B_v12 | 09-21 13:54 | 48.72% | 24.32% | —（时间戳早于 v6，命名与顺序不符，需核实） |

> 说明：早期版本（v2~v7）的提示词目录已不在服务器，仅保留 `prompts_b8`、`prompts_b9`、`prompts_b10_current`、`prompts_v11` 与当前 `prompts` 五个目录。

## 三、四个模板（当前 skill/prompts/，作为基线方案）

### system_combo.txt（组合逻辑，6 条）
```
1. Module name MUST be exactly `TopModule`.
2. Port names, directions, and widths MUST match the specification exactly.
3. Use `assign` or `always @(*)` for combinational logic.
4. Assign every output in all branches to avoid latch inference.
5. Do NOT use `always_ff`, `always_comb`, or `always_latch`.
6. Output ONLY the Verilog code, no markdown, no explanation.
```

### system_seq.txt（时序逻辑，5 条）
```
1. Module name MUST be exactly `TopModule`.
2. Port names, directions, and widths MUST match the specification exactly.
3. Use `always @(posedge clk)` for clocked logic.
4. Do NOT use `always_ff`, `always_comb`, or `always_latch`.
5. Output ONLY the Verilog code, no markdown, no explanation.
```

### system_fsm.txt（状态机，9 条）
```
1. Module name MUST be exactly `TopModule`.
2. Port names, directions, and widths MUST match the specification exactly.
3. Use `always @(posedge clk)` for the state register.
4. Use `localparam` for state encoding.
5. Use `case` statements for next-state logic.
6. The `case` statement MUST have a `default` branch.
7. Use non-blocking (`<=`) for state register, blocking (`=`) for next-state.
8. Do NOT use `always_ff`, `always_comb`, or `always_latch`.
9. Output ONLY the Verilog code, no markdown, no explanation.
```

### system_complex.txt（综合，9 条）
```
1. Module name MUST be exactly `TopModule`.
2. Port names, directions, and widths MUST match the specification exactly.
3. Use `always @(posedge clk)` for sequential logic.
4. Use `always @(*)` or `assign` for combinational logic.
5. If hierarchical design, output ALL sub-modules in one file, TopModule LAST.
6. Do NOT use type casts like `int'(x)` or `logic'(x)`.
7. Prefer concise `assign` / `case` over long if-else chains.
8. Do NOT use `always_ff`, `always_comb`, or `always_latch`.
9. Output ONLY the Verilog code, no markdown, no explanation.
```

## 四、分类映射

评测脚本 `evaluate.py` 通过 `results/problem_classification.csv` 决定每题用哪个模板：
- combinational → system_combo.txt
- sequential → system_seq.txt
- fsm → system_fsm.txt
- complex → system_complex.txt

另有两条特殊追加提示（evaluate.py 内置 special hint）：
- 8 道纯组合 FSM 题（079/091/099/100/134/135/143/150）：追加"这是组合 FSM，勿加时钟/复位"。
- 3 道 bug 修复题（062/123/132）：追加"最小改动修 bug，勿整体重写"。

## 五、关键差异：B_v8 的 FSM 模板多出的两条规则

`skill/prompts_b8/system_fsm.txt`（11 条）比当前（9 条）多出下面两条，其余相同：

```
10. Do NOT use `case ... inside` or `casez` with complex patterns. Use simple `case` statements only.
11. Declare ALL ports in the module header. Do NOT use undeclared signals.
```

`skill/prompts_v11/system_fsm.txt` 同样是 11 条（也含这两条）。

## 六、结论与建议（2026-10-08 修订）

### 6.1 原结论

B_v8（含两条额外 FSM 规则）在 B 系列消融中拿到 FSM 分项峰值 41.38%，删掉后（B_v9 起）FSM 跌到 17%~24%，因此当时判断「这两条规则有益，建议恢复」。

### 6.2 独立复测推翻该结论

C 侧在 29 道 FSM 题上做了独立对照实验（统一口径、同温度、同评测脚本）：

| FSM 提示词版本 | 规则数 | FSM 通过率 |
|---|---|---|
| **无专用提示词（对照）** | 0 | **~41%** |
| B_v8 恢复版 | 11 | 31.0% |
| B_v8 + 温度 0.3 | 11 | 17.2% |
| 精简版（只留 5 条核心） | 5 | 17.2% |
| 增强版 v2 | 13 | ~17% |

**结论反转**：FSM 专用提示词的通过率**全部低于**不加专用提示词的对照，且**规则越多越差**。

### 6.3 与 A 侧证据一致

A 侧交接总结（10-07）明确记录：

> 温度多样化、FSM few-shot —— 没有稳定收益；保留 0.3 × 5 与原提示策略。

两条独立链路（B 的消融、C 的对照实验、A 的训练侧）指向同一结论。

### 6.4 最终建议

1. **不要再投入 FSM 专用提示词优化**，该路线已判定为负收益。
2. 分类模板保留仅作**模型兜底**用途；FSM 题的实际增益改由 `structured.py` 的确定性解析承担（见 `structured_parsing.md`）。
3. B_v8 的历史峰值（58.97%）应理解为**同批消融内的相对最优**，而非「FSM 专用提示词优于无提示词」的证据——当时的对照口径与本次独立复测不同。