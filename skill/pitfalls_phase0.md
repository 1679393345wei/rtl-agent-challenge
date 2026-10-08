# 阶段0 踩坑记录

> 记录 ROCm 安装、vLLM 部署、iverilog 配置中遇到的问题和解决方案。
> **截图存放：** `assets/pitfalls/` 目录，命名格式 `phase0_<关键词>_<序号>.png`

---

## 算力平台 / 驱动

### pitfall-01: CUDA 12.8 与 vLLM 版本不匹配

**现象：**
```
ImportError: libcudart.so.13: cannot open shared object file
```

**根因：**
新版 vLLM 默认需要 CUDA 13，而当前环境是 CUDA 12.8，运行库版本对不上。

**解决：**
1. 用官方 cu128 索引安装 vLLM。
2. 确认 torch 后缀为 `+cu128`（与 CUDA 12.8 匹配）。

**耗时：** 约 30 分钟

---

## vLLM 部署

### pitfall-01: SALV-7B 的 rope_scaling 字段为 null 导致加载报错

**现象：**
```
AssertionError（vLLM 加载模型 config.json 时报错）
```

**根因：**
模型 `config.json` 中 `rope_scaling` 字段为 `null`，vLLM 无法解析。

**解决：**
手动修改 `config.json`：
- `rope_scaling` 类型改为 `yarn`
- `factor` 设为 `4.0`
- `original_max_position_embeddings` 设为 `32768`

**耗时：** 约 40 分钟

### pitfall-02: HuggingFace 下载锁文件残留

**现象：**
下载中断后重试，一直卡在等待锁，进度不前进。

**根因：**
下载中断后 `.lock` 文件未清理，重试时一直等锁。

**解决：**
删除 `~/.cache/huggingface/download/` 下的 `*.lock` 文件后重试。

---

## iverilog 配置

### pitfall-01: iverilog 不支持 always_ff

**现象：**
`-g2012` 下使用 `always_ff` 编译报 syntax error（EXIT=6）。

**根因：**
Icarus Verilog 对 SystemVerilog 的 `always_ff` / `always_comb` / `always_latch` 支持不完整。

**解决：**
所有提示词模板明确禁用 `always_ff` / `always_comb` / `always_latch`，改用 `always @(posedge clk)` 或 `always @(*)`。改后编译失败从约 70 题降到 8 题。

**耗时：** 约 1 小时（影响面大，需逐模板排查）

### pitfall-02: 模块名必须为 TopModule

**现象：**
生成代码编译失败，官方测试台无法例化。

**根因：**
官方测试台硬编码 `TopModule` 例化，模块名不符即编译失败。

**解决：**
提示词第 1 条明确："Module name MUST be exactly `TopModule`"。

### pitfall-03: *_ref.sv 必须一起编译

**现象：**
只编译生成代码时，测试台报 RefModule 未定义。

**根因：**
测试台同时例化 `RefModule`（参考实现），缺 `*_ref.sv` 编译失败。

**解决：**
用 iverilog 三文件一起编译：`生成代码.sv + *_ref.sv + *_test.sv`。

---

## 参数调优（后续阶段，一并归档）

### pitfall-01: temperature 对 FSM 敏感

**现象：**
temperature=0.6 下 FSM 通过率在 41% ~ 14% 之间大幅波动。

**根因：**
FSM 题对生成随机性敏感，高温下状态机逻辑更容易写飘。

**解决：**
稳定性实验改用 temperature=0.3 或更低（最终方案见 gain_visualization.md）。