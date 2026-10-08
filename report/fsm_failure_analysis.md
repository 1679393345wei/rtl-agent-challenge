# FSM 失败根因分析（fsm_failure_analysis）

> 分析对象：baseline_v12（通过）与 agent_verified_v12（失败）在 FSM 类别上的 7 道倒退题
> 数据来源：服务器 `data/out_baseline/`（基线通过代码）与 `~/yangxy_agent/out_agent/`（Agent 代码）
> 分析时间：2026-09-22

## 一、现象

FSM 是四类题型中唯一倒退的类别：

- 基线通过率 32.43%（12/37） → Agent 18.92%（7/37），**下跌 13.51 个百分点**
- 7 道倒退题全部是 `pass -> sim_fail`（**行为仿真错，非编译错**）
- FSM 类失败分布：基线 sim_fail 19 → Agent sim_fail 29（行为错误反而大幅增加）

## 二、7 道倒退题列表

| 题号 | 题目 | 根因归类 |
|---|---|---|
| Prob079 | fsm3onehot | 状态转换 if/else 分支反向 |
| Prob121 | 2014_q3bfsm | 复位语义（异步 vs 同步）不一致 |
| Prob127 | lemmings1 | 使用 always_ff/always_comb 风格 + 转向逻辑简化 |
| Prob135 | m2014_q6b | 把纯组合 FSM 题错误做成时序电路 |
| Prob136 | m2014_q6 | 输出状态集合写错（丢了一个状态） |
| Prob138 | 2012_q2fsm | 输出逻辑错误（z=w 被写成 z=1） |
| Prob148 | 2013_q2afsm | 输出/次态逻辑耦合在一个组合块 |

## 三、系统性根因（4 条）

### 根因 1：Agent 统一使用 always_ff / always_comb，违反团队已验证的规范
基线代码一律使用 `always @(posedge clk)` + `always @(*)`，而 Agent 代码大量使用 SystemVerilog 的 `always_ff`、`always_comb`、`assign`。这解释了 FSM 风格为什么与「已验证有效」的团队提示词不一致——**Agent 侧没有沿用 skill/prompts 里「禁用 always_ff」的核心约束**。

### 根因 2：状态转换表逻辑错误（if/else 分支写反）
典型是 Prob079：基线里 State B 的转换是「in==0 → 0100，in==1 → 0010」，Agent 写成了「in==0 → 0010，in==1 → 0100」，**两者分支完全反向**。这是模型生成的「幻觉式逻辑错误」，把真值表记反了。

### 根因 3：把纯组合 FSM 题误做成时序电路
Prob135 属于「纯组合 FSM」题（evaluate.py 会追加提示「勿加时钟/复位」），但 Agent 生成了 `always_ff @(posedge w)` 时钟块 + 状态寄存器 `y_reg`，**把本应只有组合逻辑的电路强行加了时钟**，直接违背题目要求导致 sim_fail。

### 根因 4：输出逻辑写成错误形式
- Prob136：正确输出是「E、F 两个状态下 z=1」，Agent 只写了「F 状态下 z=1」（`assign z = (state==F)?1:0`），**漏掉 E 状态**。
- Prob138：正确是「E/F 状态 z 跟随输入 w」，Agent 写成「E 状态 z 恒为 1」（`assign _z = (state==E)?1:0`），**把 z=w 错当 z=1**。

## 四、复位语义差异（次要根因）

Prob121、Prob148 等题，基线用同步复位 `always @(posedge clk) if(reset)`，Agent 用异步复位 `always_ff @(posedge clk or posedge reset)`。当测试台按同步复位假设时，异步复位会造成时序不对齐，产生额外 mismatch。

## 五、结论

1. **Agent 的 FSM 失败不是语法/工具问题**（能编译通过），而是**行为逻辑错误 + 提示词规范未对齐**。
2. **核心根因**：队友 Agent 没有沿用团队提示词里「禁用 always_ff / always_comb、三段式写法、明确复位语义」的约束，且对 FSM 真值表、纯组合 FSM 的识别能力不足，导致状态转换和输出逻辑写错。
3. ~~**与提示词库结论互相印证**：B_v8 的 FSM 模板（11 条）拿到 FSM 峰值 41.38%；删掉两条后跌到 18.92%，说明更严格的 FSM 约束能显著降低行为错误。~~

> **⚠️ 2026-10-08 修正**：上述第 3 条**已推翻**。C 侧独立对照实验（29 道 FSM 题、统一口径、同温度）显示：**不加专用提示词的对照通过率 ~41%，高于所有 FSM 专用提示词版本**（B_v8 恢复版 31.0%、精简版 17.2%、增强版 ~17%），且规则越多越差。A 侧交接总结亦记录「FSM few-shot 无稳定收益」。
>
> 即：**B_v8 的 41.38% 只是同批消融内的相对最优，不能推出「专用提示词优于无提示词」**。本文件第一~四节的根因分析仍然成立（它描述的是「C/B 统一口径下 FSM 为何倒退」），但**由此推出的提示词建议不成立**——FSM 的实际增益应由 `agent/structured.py` 的确定性解析承担，而非堆提示词规则。详见 `skill/prompts_cookbook.md` 第六节与 `skill/pitfalls_phase3.md`。

## 六、建议（给 A/B）—— 2026-10-08 修订

1. Agent 的提示词统一采用团队 `skill/prompts` 规范，明确：禁用 always_ff/always_comb、case 必须带 default、明确同步/异步复位语义。**（仅作语法层兜底，不要指望它改善行为层）**
2. ~~恢复 B_v8 的 FSM 11 条规则~~ → **不要恢复**。该路线已实测为负收益。
3. 对「纯组合 FSM」题（079/091/099/100/134/135/143/150）加强识别，禁止加时钟与状态寄存器。**（现已由 `structured.py` 的确定性解析覆盖，效果优于提示词）**
4. 温度维持 0.3×5；温度多样化已实测无稳定增益。