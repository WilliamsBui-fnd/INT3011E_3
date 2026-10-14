"""Generate LaTeX tables and copy verified figures for the final report."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

import pandas as pd


METHOD_LABELS = {
    "SAT_Pairwise": "SAT Pairwise",
    "SAT_Sequential": "SAT Sequential",
    "SAT_Commander": "SAT Commander",
    "SAT_Product": "SAT Product",
    "SAT_Binary": "SAT Binary",
    "CP_ORTools": "OR-Tools CP-SAT",
    "ILP_Gurobi": "Gurobi MIP",
    "MIP_CPLEX": "CPLEX MIP",
    "CP_CPLEX": "CPLEX CP",
}


def latex_escape(value):
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(char, char) for char in text)


def result_cell(row):
    if row is None:
        return "--"
    successful = int(row["Successful_Runs"])
    total = int(row["Total_Runs"])
    if successful:
        return f"{float(row['Total_Time']):.3f} ({successful}/{total})"
    status = str(row["Status"])
    labels = {
        "TIMEOUT": "TO",
        "LICENSE_LIMIT": "LIC",
        "KILLED": "KILL",
        "OOM": "OOM",
        "UNAVAILABLE": "NA",
    }
    return labels.get(status, latex_escape(status))


def write_sat_table(summary, path):
    n_values = [16, 32, 64, 128, 256, 512, 1000]
    methods = [
        "SAT_Pairwise", "SAT_Sequential", "SAT_Commander",
        "SAT_Product", "SAT_Binary",
    ]
    lookup = {
        (int(row.N), row.Method): row
        for row in summary.itertuples(index=False)
    }
    lines = [
        r"\begin{tabular}{rccccc}",
        r"\toprule",
        r"$N$ & Pairwise & Sequential & Commander & Product & Binary \\",
        r"\midrule",
    ]
    for n in n_values:
        cells = []
        for method in methods:
            row = lookup.get((n, method))
            cells.append(result_cell(row._asdict() if row else None))
        lines.append(f"{n} & " + " & ".join(cells) + r" \\")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fastest_table(summary, path):
    lines = [
        r"\begin{tabular}{rlrr}",
        r"\toprule",
        r"$N$ & Phương pháp nhanh nhất & Trung vị (s) & Thành công \\",
        r"\midrule",
    ]
    for n in [16, 32, 64, 128, 256, 512, 1000]:
        group = summary[(summary["N"] == n) & summary["Total_Time"].notna()]
        if group.empty:
            continue
        row = group.loc[group["Total_Time"].idxmin()]
        lines.append(
            f"{n} & {latex_escape(METHOD_LABELS.get(row['Method'], row['Method']))} "
            f"& {row['Total_Time']:.4f} "
            f"& {int(row['Successful_Runs'])}/{int(row['Total_Runs'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gurobi_comparison_table(summary, path):
    methods = ["ILP_Gurobi", "CP_ORTools", "SAT_Pairwise", "SAT_Product", "SAT_Binary"]
    lookup = {(int(row.N), row.Method): row for row in summary.itertuples(index=False)}
    lines = [
        r"\begin{tabular}{rccccc}",
        r"\toprule",
        r"$N$ & Gurobi MIP & CP-SAT & SAT Pairwise & SAT Product & SAT Binary \\",
        r"\midrule",
    ]
    for n in (64, 128, 256):
        cells = [result_cell(lookup[(n, method)]._asdict()) if (n, method) in lookup else "--"
                 for method in methods]
        lines.append(f"{n} & " + " & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_table(raw, path):
    counts = raw["Status"].value_counts()
    ordered = ["SAT", "UNSAT", "TIMEOUT", "LICENSE_LIMIT", "KILLED", "OOM", "ERROR"]
    lines = [r"\begin{tabular}{lr}", r"\toprule", r"Trạng thái & Số lượt \\", r"\midrule"]
    for status in ordered:
        count = int(counts.get(status, 0))
        if count:
            lines.append(f"{latex_escape(status)} & {count} \\\\"
            )
    lines.extend([r"\midrule", f"Tổng & {len(raw)} \\\\", r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_gurobi_runs(raw, path):
    runs = raw[(raw["Method"] == "ILP_Gurobi") & raw["N"].isin([64, 128, 256])]
    if len(runs) != 13 or not runs["Status"].eq("SAT").all():
        raise SystemExit("Expected 13 successful licensed Gurobi runs")
    lines = [
        r"\begin{tabular}{rrrrr}", r"\toprule",
        r"$N$ & Lượt & Dựng mô hình (s) & Giải (s) & Tổng (s) \\",
        r"\midrule",
    ]
    for row in runs.sort_values(["N", "Run"]).itertuples(index=False):
        lines.append(
            f"{int(row.N)} & {int(row.Run)} & {row.Encoding_Time:.4f} "
            f"& {row.Solving_Time:.4f} & {row.Total_Time:.4f} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_cplex_table(summary, path):
    lines = [
        r"\begin{tabular}{llrrl}", r"\toprule",
        r"Bộ giải & $N$ & Hoàn thành & Trung vị (s) & Trạng thái \\",
        r"\midrule",
    ]
    for method, label in (("MIP_CPLEX", "CPLEX MIP"), ("CP_CPLEX", "CPLEX CP")):
        for n in (8, 16, 32):
            group = summary[(summary["Method"] == method) & (summary["N"] == n)]
            if len(group) != 1:
                raise SystemExit(f"Missing CPLEX summary row: {method}, N={n}")
            row = group.iloc[0]
            median = f"{row.Total_Time:.4f}" if pd.notna(row.Total_Time) else "--"
            status = "SAT" if row.Successful_Runs == row.Total_Runs else latex_escape(row.Status)
            lines.append(
                f"{label} & {n} & {int(row.Successful_Runs)}/{int(row.Total_Runs)} "
                f"& {median} & {status} \\\\"
            )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_sat_scale(summary, path):
    methods = ["SAT_Pairwise", "SAT_Sequential", "SAT_Commander", "SAT_Product", "SAT_Binary"]
    lookup = {(int(row.N), row.Method): row for row in summary.itertuples(index=False)}
    lines = [
        r"\begin{longtable}{rlrrl}",
        r"\caption{Quy mô CNF và trung vị thời gian của từng cấu hình SAT đã chạy. Dấu -- biểu thị không có thống kê do không chạy hoặc run không hoàn thành.}\label{tab:full-sat-scale}\\",
        r"\toprule",
        r"$N$ & Mã hóa & Biến & Clause & Thời gian/Trạng thái \\",
        r"\midrule", r"\endfirsthead",
        r"\multicolumn{5}{c}{Bảng \ref{tab:full-sat-scale} (tiếp theo)}\\",
        r"\toprule",
        r"$N$ & Mã hóa & Biến & Clause & Thời gian/Trạng thái \\",
        r"\midrule", r"\endhead",
        r"\bottomrule", r"\endfoot",
    ]
    for n in (16, 32, 64, 128, 256, 512, 1000):
        for method in methods:
            row = lookup.get((n, method))
            if row is None:
                continue
            variables = f"{int(row.Variables):,}" if pd.notna(row.Variables) else "--"
            clauses = f"{int(row.Clauses):,}" if pd.notna(row.Clauses) else "--"
            lines.append(
                f"{n} & {method.removeprefix('SAT_')} & {variables} & {clauses} "
                f"& {result_cell(row._asdict())} \\\\"
            )
    lines.append(r"\end{longtable}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_environment_macros(environment, path):
    packages = environment.get("packages", {})
    values = {
        "ResultPlatform": environment.get("platform", "not recorded"),
        "ResultPython": str(environment.get("python", "not recorded")).split()[0],
        "ResultCpuCount": environment.get("cpu_count", "not recorded"),
        "ResultPySAT": packages.get("python-sat", "not recorded"),
        "ResultORTools": packages.get("ortools", "not recorded"),
        "ResultGurobi": packages.get("gurobipy", "not recorded"),
        "ResultCPLEX": packages.get("cplex", "not recorded"),
        "ResultPandas": packages.get("pandas", "not recorded"),
    }
    lines = [
        rf"\newcommand{{\{name}}}{{{latex_escape(value)}}}"
        for name, value in values.items()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_inputs(summary, raw):
    if raw.empty or summary.empty:
        raise SystemExit("Result data is empty")
    if raw.duplicated(["Phase", "N", "Method", "Run"]).any():
        raise SystemExit("Combined raw data contains duplicate run keys")
    sat = raw[raw["Status"] == "SAT"]
    if not sat["Solution_Valid"].astype(str).str.lower().eq("true").all():
        raise SystemExit("At least one SAT solution is not marked valid")
    raw_pairs = set(zip(raw["N"], raw["Method"]))
    summary_pairs = set(zip(summary["N"], summary["Method"]))
    if raw_pairs != summary_pairs or summary.duplicated(["N", "Method"]).any():
        raise SystemExit("Summary methods and sizes do not match raw data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir", type=Path,
        default=Path("NQueens_BTL1_results/combined_licensed"),
    )
    parser.add_argument(
        "--environment", type=Path,
        default=Path("NQueens_BTL1_results/standard/environment.json"),
    )
    parser.add_argument("--report-dir", type=Path, default=Path("report"))
    args = parser.parse_args()

    results_dir = args.results_dir.resolve()
    report_dir = args.report_dir.resolve()
    generated_dir = report_dir / "generated"
    figures_dir = report_dir / "figures"
    generated_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(results_dir / "benchmark_results.csv")
    raw = pd.read_csv(results_dir / "benchmark_raw.csv")
    validate_inputs(summary, raw)

    write_sat_table(summary, generated_dir / "sat_performance_table.tex")
    write_fastest_table(summary, generated_dir / "fastest_table.tex")
    write_gurobi_comparison_table(summary, generated_dir / "gurobi_comparison_table.tex")
    write_status_table(raw, generated_dir / "status_table.tex")
    write_full_gurobi_runs(raw, generated_dir / "full_gurobi_runs.tex")
    write_full_cplex_table(summary, generated_dir / "full_cplex_table.tex")
    write_full_sat_scale(summary, generated_dir / "full_sat_scale.tex")
    environment = json.loads(args.environment.read_text(encoding="utf-8"))
    write_environment_macros(environment, generated_dir / "environment.tex")

    for name in ("plot_time.png", "plot_status.png", "plot_variables.png", "plot_clauses.png"):
        source = results_dir / name
        if not source.exists() or source.stat().st_size == 0:
            raise SystemExit(f"Missing figure: {source}")
        shutil.copy2(source, figures_dir / name)

    print(f"Report assets prepared in {report_dir}")


if __name__ == "__main__":
    main()
