"""VerilogEval v2 spec-to-rtl 评测脚本。

两种模式：
  1) 默认：调 vLLM 生成代码 → 编译仿真 → 判定
  2) --eval-only：只评测 --gen-dir 里已有的 .sv，不调 vLLM
     用途：用统一评测口径重新评测队友 Agent 生成的代码

流程：读 *_prompt.txt → (生成) → iverilog 编译
[生成代码 + *_ref.sv + *_test.sv] → vvp 仿真 → 判定 "Mismatches: 0"。
"""

import argparse
import csv
import re
import subprocess
import traceback
from pathlib import Path

from openai import OpenAI

BASE_DIR = Path("/home/yangxy/ljr-rtl-agent")
DATA_DIR = BASE_DIR / "data/VerilogEval_v2_dataset/dataset_spec-to-rtl"
CLASSIFICATION_CSV = BASE_DIR / "results/problem_classification.csv"
PROMPT_DIR = BASE_DIR / "skill/prompts"

CSV_HEADER = ["prob_id", "category", "status", "error_msg", "finish_reason"]
FINAL_STATUSES = {"pass", "compile_fail", "sim_fail", "missing_files", "no_test"}

CATEGORY_MAP = {
    "combinational": "combo",
    "sequential": "seq",
    "fsm": "fsm",
    "complex": "complex",
}

SYSTEM_PROMPT_FALLBACK = """You are a Verilog design expert. Generate synthesizable Verilog code based on the user's description.

Rules:
1. The module name MUST be exactly `TopModule`.
2. The port names and directions MUST match the specification exactly.
3. Output only the Verilog code, no markdown, no explanation.
4. Use synthesizable constructs only."""

SPECIAL_HINTS = [
    ({"Prob079", "Prob091", "Prob099", "Prob100",
      "Prob134", "Prob135", "Prob143", "Prob150"},
     "This is a combinational FSM problem. Do NOT add a clock or reset. "
     "Only implement the next-state logic and output logic "
     "as combinational equations."),
    ({"Prob062", "Prob123", "Prob132"},
     "The problem provides buggy code. Fix the bug with minimal changes. "
     "Do NOT rewrite the entire module."),
]

MISMATCH_RE = re.compile(r"Mismatches:\s*0\b")
MODULE_RE = re.compile(r"(module\s+\w+.*?endmodule)", re.DOTALL)
MODULE_DECL_RE = re.compile(r"\bmodule\s+\w+")

_PROMPT_CACHE = {}


def special_hint(prob_id):
    for probs, hint in SPECIAL_HINTS:
        if prob_id in probs:
            return f"\n\nNote: {hint}"
    return ""


def load_classification(csv_path):
    if not csv_path.exists():
        print(f"警告：分类表不存在（{csv_path}），category 列将为空", flush=True)
        return {}
    with csv_path.open(encoding="utf-8-sig") as f:
        return {row["prob_id"].strip(): row["category"].strip()
                for row in csv.DictReader(f)}


def load_prompt(category):
    if category in _PROMPT_CACHE:
        return _PROMPT_CACHE[category]
    key = CATEGORY_MAP.get(category, "complex")
    path = PROMPT_DIR / f"system_{key}.txt"
    text = path.read_text(encoding="utf-8") if path.exists() else SYSTEM_PROMPT_FALLBACK
    _PROMPT_CACHE[category] = text
    return text


def strip_code_fence(code):
    code = re.sub(r"^```\w*\n?", "", code.strip())
    code = re.sub(r"\n?```$", "", code).strip()
    matches = MODULE_RE.findall(code)
    if not matches:
        return code
    n_decl = len(MODULE_DECL_RE.findall(code))
    if n_decl > len(matches):
        print(f"警告：检测到 {n_decl} 个 module 声明，只匹配到 {len(matches)} 个完整模块",
              flush=True)
    return "\n\n".join(matches)


def load_existing_results(csv_path):
    if not csv_path.exists():
        return {}
    result = {}
    with csv_path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("status") not in FINAL_STATUSES:
                continue
            pid = row["prob_id"]
            if pid in result:
                print(f"警告：{pid} 在旧 CSV 里重复，以最后一行为准", flush=True)
            result[pid] = row
    return result


def generate_verilog(client, model, prompt, system_prompt, max_tokens, temperature):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    choice = resp.choices[0]
    return strip_code_fence(choice.message.content), choice.finish_reason


def simulate(gen_file, ref_file, test_file, sim_dir, timeout=60):
    sim_dir.mkdir(parents=True, exist_ok=True)
    sim_bin = sim_dir / "sim.out"

    compile_run = subprocess.run(
        ["iverilog", "-g2012", "-o", str(sim_bin),
         str(gen_file.resolve()), str(ref_file.resolve()), str(test_file.resolve())],
        capture_output=True, text=True, timeout=timeout, cwd=str(sim_dir),
    )
    if compile_run.returncode != 0:
        return "compile_fail", compile_run.stderr[:500]

    sim_run = subprocess.run(
        ["vvp", str(sim_bin)],
        capture_output=True, text=True, timeout=timeout, cwd=str(sim_dir),
    )
    if MISMATCH_RE.search(sim_run.stdout):
        return "pass", ""
    return "sim_fail", sim_run.stdout[-500:]


def print_summary(results):
    if not results:
        print("没有题目被评测", flush=True)
        return
    total = len(results)
    passed = sum(r[2] == "pass" for r in results)
    print(f"pass@1 = {passed}/{total} = {passed / total:.2%}", flush=True)

    stats = {}
    for _, category, status, *_ in results:
        category = category or "未分类"
        p, t = stats.get(category, (0, 0))
        stats[category] = (p + (status == "pass"), t + 1)
    for category, (p, t) in sorted(stats.items()):
        note = "（样本少，统计意义有限）" if t < 10 else ""
        print(f"  {category}: {p}/{t} = {p / t:.2%} {note}".rstrip(), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prob", nargs="?", default=None,
                        help="只跑指定题，如 Prob001；不填则跑全量")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--classification-csv", type=Path, default=CLASSIFICATION_CSV)
    parser.add_argument("--out-csv", type=Path,
                        default=BASE_DIR / "results/eval_output.csv")
    parser.add_argument("--gen-dir", type=Path, default=BASE_DIR / "data/out_baseline")
    parser.add_argument("--log-dir", type=Path, default=BASE_DIR / "logs")
    parser.add_argument("--base-url", default="http://localhost:8001/v1")
    parser.add_argument("--model", default="qimeng-salv-7b")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--resume", action="store_true",
                        help="读 --out-csv 已有终态题，跳过；只重跑 error/timeout/truncated")
    parser.add_argument("--eval-only", action="store_true",
                        help="只评测 --gen-dir 里已有的 .sv，不调 vLLM")
    args = parser.parse_args()

    # 防止误覆盖 baseline.csv
    if args.out_csv.name == "baseline.csv" and not args.resume:
        print("错误：--out-csv 指向 baseline.csv，会覆盖基线数据。")
        print("请改用其他文件名，如 results/prompt_B.csv，或加 --resume。")
        return

    for d in (args.gen_dir, args.out_csv.parent, args.log_dir):
        d.mkdir(parents=True, exist_ok=True)

    if not PROMPT_DIR.exists() and not args.eval_only:
        print(f"警告：提示词目录不存在（{PROMPT_DIR}），将使用通用提示词", flush=True)

    classification = load_classification(args.classification_csv)
    client = OpenAI(base_url=args.base_url, api_key="dummy", timeout=120)

    existing = load_existing_results(args.out_csv) if args.resume else {}
    if existing:
        print(f"--resume: 从 {args.out_csv} 读到 {len(existing)} 题终态，将跳过", flush=True)

    prompt_files = sorted(args.data_dir.glob("*_prompt.txt"))
    if args.prob:
        prompt_files = [f for f in prompt_files if args.prob in f.name]
        if not prompt_files:
            print(f"未找到匹配 {args.prob} 的题目", flush=True)
            return

    def prob_id_of(pf):
        return pf.name[: -len("_prompt.txt")].split("_", 1)[0]

    if existing:
        prompt_files = [f for f in prompt_files if prob_id_of(f) not in existing]

    mode = "eval-only" if args.eval_only else "generate+eval"
    print(f"模式：{mode}，待跑 {len(prompt_files)} 题", flush=True)

    with args.out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)

        for row in existing.values():
            writer.writerow([row.get(h, "") for h in CSV_HEADER])
        f.flush()

        results = [[row.get(h, "") for h in CSV_HEADER] for row in existing.values()]

        for prompt_file in prompt_files:
            stem = prompt_file.name[: -len("_prompt.txt")]
            prob_id = stem.split("_", 1)[0]
            ref_file = prompt_file.with_name(f"{stem}_ref.sv")
            test_file = prompt_file.with_name(f"{stem}_test.sv")
            category = classification.get(prob_id, "")
            sim_dir = args.log_dir / stem
            sim_dir.mkdir(parents=True, exist_ok=True)

            finish_reason = ""
            try:
                if args.eval_only:
                    gen_file = args.gen_dir / f"{stem}.sv"
                    if not gen_file.exists():
                        status, detail = "no_output", ""
                    elif not ref_file.exists() or not test_file.exists():
                        status = "missing_files"
                        detail = f"ref={ref_file.exists()} test={test_file.exists()}"
                    else:
                        status, detail = simulate(gen_file, ref_file, test_file, sim_dir)
                    finish_reason = "eval_only"
                else:
                    system_prompt = load_prompt(category)
                    prompt = prompt_file.read_text() + special_hint(prob_id)
                    code, finish_reason = generate_verilog(
                        client, args.model, prompt, system_prompt,
                        args.max_tokens, args.temperature)
                    gen_file = args.gen_dir / f"{stem}.sv"
                    gen_file.write_text(code)
                    if finish_reason == "length":
                        status, detail = "truncated", ""
                    elif not ref_file.exists() or not test_file.exists():
                        status = "missing_files"
                        detail = f"ref={ref_file.exists()} test={test_file.exists()}"
                    else:
                        status, detail = simulate(gen_file, ref_file, test_file, sim_dir)
            except subprocess.TimeoutExpired as exc:
                status, detail = "timeout", str(exc)[:500]
                (sim_dir / "traceback.log").write_text(traceback.format_exc())
            except Exception as exc:
                status, detail = "error", str(exc)[:500]
                (sim_dir / "traceback.log").write_text(traceback.format_exc())

            row = [prob_id, category, status, detail, finish_reason]
            results.append(row)
            writer.writerow(row)
            f.flush()
            print(f"{prob_id}: {status}", flush=True)

    print_summary(results)
    print(f"结果已写入 {args.out_csv}", flush=True)


if __name__ == "__main__":
    main()
    