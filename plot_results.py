"""Create report-ready plots from benchmark summary and raw CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import seaborn as sns


METHOD_ORDER = (
    "SAT_Pairwise", "SAT_Sequential", "SAT_Commander", "SAT_Product",
    "SAT_Binary", "CP_ORTools", "ILP_Gurobi", "MIP_CPLEX", "CP_CPLEX",
)

METHOD_LABELS = {
    "SAT_Pairwise": "SAT Pairwise",
    "SAT_Sequential": "SAT Sequential",
    "SAT_Commander": "SAT Commander",
    "SAT_Product": "SAT Product",
    "SAT_Binary": "SAT Binary",
    "CP_ORTools": "OR-Tools CP-SAT",
    "ILP_Gurobi": "Gurobi MIP",
    "MIP_CPLEX": "CPLEX MIP",
    "CP_CPLEX": "CPLEX CP Optimizer",
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path,
        default=Path("results/standard/benchmark_results.csv"),
        help="Summary CSV produced by benchmark.py or combine_results.py",
    )
    parser.add_argument(
        "--raw", type=Path,
        help="Raw CSV; defaults to benchmark_raw.csv next to --input",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        help="Output directory; defaults to the directory containing --input",
    )
    return parser.parse_args()


def save_figure(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Created: {path}")


def method_palette(methods):
    colors = sns.color_palette("tab10", n_colors=max(10, len(methods)))
    return {method: colors[index] for index, method in enumerate(methods)}


def plot_segmented_metric(ax, data, metric, methods, all_n, palette, marker="o"):
    """Connect only adjacent observed sizes, never across a missing result."""
    n_position = {value: index for index, value in enumerate(all_n)}
    for method in methods:
        group = data[data["Method"] == method].sort_values("N")
        if group.empty:
            continue
        color = palette[method]
        ax.scatter(
            group["N"], group[metric], s=48, marker=marker, color=color,
            edgecolor="white", linewidth=0.6, zorder=3,
            label=METHOD_LABELS.get(method, method),
        )
        values = group[["N", metric]].to_records(index=False)
        for left, right in zip(values, values[1:]):
            n_left, y_left = left
            n_right, y_right = right
            if n_position[int(n_right)] == n_position[int(n_left)] + 1:
                ax.plot(
                    [n_left, n_right], [y_left, y_right], color=color,
                    linewidth=1.8, zorder=2,
                )


def configure_log_axes(ax, all_n, ylabel):
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(all_n)
    ax.set_xticklabels([str(value) for value in all_n], rotation=35)
    ax.set_xlabel("Board size N")
    ax.set_ylabel(ylabel)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.12)


def plot_encoding_metric(sat, metric, title, ylabel, output_path, all_n, palette):
    observed = sat.dropna(subset=[metric])
    observed = observed[observed[metric] > 0]
    if observed.empty:
        return
    methods = [m for m in METHOD_ORDER if m in observed["Method"].unique()]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    plot_segmented_metric(ax, observed, metric, methods, all_n, palette)
    configure_log_axes(ax, all_n, ylabel)
    ax.set_title(title, weight="bold")
    ax.text(
        0.01, 0.01,
        "Lines stop at missing observations; timed-out/killed runs return no size statistics.",
        transform=ax.transAxes, fontsize=8.5, color="#555555",
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True)
    save_figure(fig, output_path)


def plot_time(summary, output_path, all_n, palette):
    solved = summary.dropna(subset=["Total_Time"]).copy()
    solved = solved[solved["Total_Time"] > 0]
    if solved.empty:
        return
    methods = [m for m in METHOD_ORDER if m in solved["Method"].unique()]
    fig, ax = plt.subplots(figsize=(12, 7))
    plot_segmented_metric(
        ax, solved, "Total_Time", methods, all_n, palette, marker="s"
    )
    for method in methods:
        group = solved[solved["Method"] == method]
        if not {"Min_Time", "Max_Time"}.issubset(group.columns):
            continue
        lower = group["Total_Time"] - group["Min_Time"]
        upper = group["Max_Time"] - group["Total_Time"]
        ax.errorbar(
            group["N"], group["Total_Time"],
            yerr=np.vstack([lower.clip(lower=0), upper.clip(lower=0)]),
            fmt="none", ecolor=palette[method], alpha=0.45,
            capsize=2, linewidth=1, zorder=1,
        )
    configure_log_axes(ax, all_n, "Median total time of successful runs (seconds)")
    ax.set_title("N-Queens solver performance", weight="bold")
    ax.text(
        0.01, 0.01,
        "Whiskers show min-max. Missing points mean no successful run; see the status matrix.",
        transform=ax.transAxes, fontsize=8.5, color="#555555",
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True)
    save_figure(fig, output_path)


def abbreviated_status(group):
    total = len(group)
    solved = int(group["Status"].isin(["SAT", "UNSAT"]).sum())
    lines = [f"{solved}/{total}"]
    abbreviations = {
        "TIMEOUT": "TO", "LICENSE_LIMIT": "LIC", "UNAVAILABLE": "NA",
        "OOM": "OOM", "KILLED": "KILL", "INVALID_SOLUTION": "INV",
        "ERROR": "ERR",
    }
    failures = group.loc[
        ~group["Status"].isin(["SAT", "UNSAT"]), "Status"
    ]
    for status, count in failures.value_counts().items():
        lines.append(f"{count} {abbreviations.get(status, status[:4])}")
    return "\n".join(lines)


def plot_status_matrix(raw, output_path, all_n):
    methods = [m for m in METHOD_ORDER if m in raw["Method"].unique()]
    rates = pd.DataFrame(index=methods, columns=all_n, dtype=float)
    labels = pd.DataFrame("", index=methods, columns=all_n, dtype=object)
    for (method, n), group in raw.groupby(["Method", "N"]):
        if method not in rates.index or int(n) not in rates.columns:
            continue
        solved = group["Status"].isin(["SAT", "UNSAT"]).sum()
        rates.loc[method, int(n)] = solved / len(group)
        labels.loc[method, int(n)] = abbreviated_status(group)

    cmap = LinearSegmentedColormap.from_list(
        "success_rate", ["#b91c1c", "#f59e0b", "#15803d"]
    )
    fig_width = max(10, 0.72 * len(all_n) + 4)
    fig, ax = plt.subplots(figsize=(fig_width, 6.8))
    sns.heatmap(
        rates, mask=rates.isna(), annot=labels, fmt="", cmap=cmap,
        vmin=0, vmax=1, linewidths=0.7, linecolor="white",
        cbar_kws={"label": "Successful runs / total runs"}, ax=ax,
    )
    ax.set_title("Run completion matrix", weight="bold")
    ax.set_xlabel("Board size N")
    ax.set_ylabel("")
    ax.set_yticklabels(
        [METHOD_LABELS.get(method, method) for method in methods], rotation=0
    )
    ax.text(
        0, -0.16,
        "TO=timeout, LIC=license limit, NA=unavailable, KILL=SIGKILL, INV=invalid solution.",
        transform=ax.transAxes, fontsize=8.5, color="#555555",
    )
    save_figure(fig, output_path)


def main():
    args = parse_args()
    summary_path = args.input.resolve()
    raw_path = (args.raw or summary_path.with_name("benchmark_raw.csv")).resolve()
    output_dir = (args.output_dir or summary_path.parent).resolve()
    if not summary_path.exists():
        raise SystemExit(f"Missing {summary_path}. Run benchmark.py first.")
    if not raw_path.exists():
        raise SystemExit(f"Missing {raw_path}. It is required for the status matrix.")

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(summary_path)
    raw = pd.read_csv(raw_path)
    for frame in (summary, raw):
        frame["N"] = pd.to_numeric(frame["N"], errors="coerce").astype("Int64")
    for column in ("Variables", "Clauses", "Total_Time", "Min_Time", "Max_Time"):
        if column in summary:
            summary[column] = pd.to_numeric(summary[column], errors="coerce")

    summary = summary.dropna(subset=["N"]).copy()
    raw = raw.dropna(subset=["N"]).copy()
    summary["N"] = summary["N"].astype(int)
    raw["N"] = raw["N"].astype(int)
    all_n = sorted(set(summary["N"]).union(raw["N"]))
    methods = [m for m in METHOD_ORDER if m in summary["Method"].unique()]
    palette = method_palette(methods)

    sns.set_theme(style="whitegrid", context="notebook")
    sat = summary[summary["Method"].str.startswith("SAT_")].copy()
    plot_encoding_metric(
        sat, "Clauses", "SAT encoding clause count", "CNF clauses",
        output_dir / "plot_clauses.png", all_n, palette,
    )
    plot_encoding_metric(
        sat, "Variables", "SAT encoding variable count",
        "Boolean variables (including auxiliaries)",
        output_dir / "plot_variables.png", all_n, palette,
    )
    plot_time(summary, output_dir / "plot_time.png", all_n, palette)
    plot_status_matrix(raw, output_dir / "plot_status.png", all_n)


if __name__ == "__main__":
    main()
