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


def write_status_table(raw, path):
    counts = raw["Status"].value_counts()
    ordered = ["SAT", "UNSAT", "TIMEOUT", "LICENSE_LIMIT", "KILLED", "OOM", "ERROR"]
    lines = [r"\begin{tabular}{lr}", r"\toprule", r"Trạng thái & Số lượt \\", r"\midrule"]
    for status in ordered:
        count = int(counts.get(status, 0))
        if count:
            lines.append(f"{latex_escape(status)} & {count} \\\\"
            )
    lines.extend([r"\midrule", f"Tổng & {len(raw)} \\\\ ", r"\bottomrule", r"\end{tabular}"])
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
        default=Path("NQueens_BTL1_results/combined"),
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
    write_status_table(raw, generated_dir / "status_table.tex")
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
