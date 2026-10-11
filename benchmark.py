"""Benchmark N-Queens theo tung phase, co timeout va checkpoint an toan.

Vi du:
    python benchmark.py --phase smoke
    python benchmark.py --phase standard --output-dir results/standard
    python benchmark.py --phase cplex --output-dir results/cplex
    python benchmark.py --phase large --output-dir results/large

File benchmark_raw.csv duoc append va flush sau moi lan chay. Neu Colab bi
ngat, chay lai cung lenh de tiep tuc cac lan chua hoan thanh.
"""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import json
import math
import multiprocessing
import os
import platform
import queue
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

from nqueens.cp_solver import NQueensCPSolver
from nqueens.ilp_solver import NQueensILPSolver
from nqueens.sat_solver import NQueensSATSolver
from nqueens.utils import get_positions_from_1d_vars, validate_solution


SAT_ENCODINGS = ("pairwise", "sequential", "commander", "product", "binary")
BASE_METHODS = tuple(f"SAT_{name.capitalize()}" for name in SAT_ENCODINGS) + (
    "CP_ORTools",
    "ILP_Gurobi",
)
ALL_METHODS = BASE_METHODS + (
    "MIP_CPLEX",
    "CP_CPLEX",
)

PHASES = {
    "smoke": {
        "n_values": (1, 2, 3, 4, 8),
        "methods": BASE_METHODS,
        "repetitions": 1,
        "timeout": 15.0,
    },
    "standard": {
        "n_values": (16, 32, 64, 128),
        "methods": BASE_METHODS,
        "repetitions": 5,
        "timeout": 60.0,
    },
    # Tranh Pairwise O(N^3) va Gurobi size-limited license theo mac dinh.
    "large": {
        "n_values": (256, 512, 1000),
        "methods": (
            "SAT_Sequential",
            "SAT_Commander",
            "SAT_Product",
            "SAT_Binary",
            "CP_ORTools",
        ),
        "repetitions": 3,
        "timeout": 120.0,
    },
    # Phase rieng vi CP Optimizer can executable/license IBM, khong chi pip.
    "cplex": {
        "n_values": (8, 16, 32),
        "methods": ("MIP_CPLEX", "CP_CPLEX"),
        "repetitions": 3,
        "timeout": 60.0,
    },
}

RAW_FIELDS = (
    "Phase", "N", "Method", "Run", "Seed", "Variables", "Clauses",
    "Constraints", "Encoding_Time", "Solving_Time", "Total_Time",
    "Wall_Time", "Status", "Solution_Valid", "Error_Type",
    "Error_Message", "Exit_Code",
)


def worker_sat(n, encoding, time_limit, num_workers, random_seed):
    del time_limit, num_workers, random_seed  # Glucose3 bi gioi han boi process cha.
    true_vars, stats = NQueensSATSolver(n, encoding_type=encoding).solve()
    positions = get_positions_from_1d_vars(n, true_vars)
    valid = validate_solution(n, positions) if stats["is_sat"] else None
    if stats["is_sat"] and not valid:
        stats["status"] = "INVALID_SOLUTION"
    stats["solution_valid"] = valid
    return stats


def worker_cp(n, time_limit, num_workers, random_seed):
    positions, stats = NQueensCPSolver(n).solve(
        time_limit=time_limit,
        num_workers=num_workers,
        random_seed=random_seed,
    )
    valid = validate_solution(n, positions) if stats["is_sat"] else None
    if stats["is_sat"] and not valid:
        stats["status"] = "INVALID_SOLUTION"
    stats["solution_valid"] = valid
    stats["num_vars"] = n
    stats["num_constraints"] = 3
    return stats


def worker_ilp(n, time_limit, num_workers, random_seed):
    positions, stats = NQueensILPSolver(n).solve(
        time_limit=time_limit,
        num_workers=num_workers,
        random_seed=random_seed,
    )
    valid = validate_solution(n, positions) if stats["is_sat"] else None
    if stats["is_sat"] and not valid:
        stats["status"] = "INVALID_SOLUTION"
    stats["solution_valid"] = valid
    return stats


def worker_cplex_mip(n, time_limit, num_workers, random_seed):
    from nqueens.cplex_mip_solver import NQueensCplexMIPSolver

    positions, stats = NQueensCplexMIPSolver(n).solve(
        time_limit=time_limit,
        num_workers=num_workers,
        random_seed=random_seed,
    )
    valid = validate_solution(n, positions) if stats["is_sat"] else None
    if stats["is_sat"] and not valid:
        stats["status"] = "INVALID_SOLUTION"
    stats["solution_valid"] = valid
    return stats


def worker_cplex_cp(n, time_limit, num_workers, random_seed):
    from nqueens.cplex_cp_solver import NQueensCplexCPSolver

    positions, stats = NQueensCplexCPSolver(n).solve(
        time_limit=time_limit,
        num_workers=num_workers,
        random_seed=random_seed,
    )
    valid = validate_solution(n, positions) if stats["is_sat"] else None
    if stats["is_sat"] and not valid:
        stats["status"] = "INVALID_SOLUTION"
    stats["solution_valid"] = valid
    return stats


def _process_entry(result_queue, target_func, args):
    """Chay trong process con va luon truyen loi ve process cha."""
    try:
        result_queue.put({"kind": "RESULT", "stats": target_func(*args)})
    except BaseException as exc:
        result_queue.put(
            {
                "kind": "ERROR",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(limit=8),
            }
        )


def run_with_timeout(target_func, args, timeout):
    """Tra ve ket qua co phan biet RESULT, TIMEOUT va ERROR."""
    ctx = multiprocessing.get_context("spawn")
    result_queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_process_entry, args=(result_queue, target_func, args))
    wall_start = time.perf_counter()
    process.start()
    process.join(timeout)
    wall_time = time.perf_counter() - wall_start

    if process.is_alive():
        process.terminate()
        process.join(5)
        outcome = {
            "kind": "TIMEOUT",
            "error_type": "ExternalTimeout",
            "error_message": f"Vuot gioi han tong {timeout:.1f} giay",
        }
    else:
        try:
            outcome = result_queue.get(timeout=1)
        except queue.Empty:
            outcome = {
                "kind": "ERROR",
                "error_type": "WorkerExitedWithoutResult",
                "error_message": "Process con ket thuc nhung khong tra ket qua",
            }

    outcome["wall_time"] = wall_time
    outcome["exit_code"] = process.exitcode
    result_queue.close()
    result_queue.join_thread()
    return outcome


def classify_error(error_type, error_message, exit_code=None):
    # multiprocessing reports a process terminated by SIGKILL as -9.  This is
    # commonly caused by the Colab OOM killer, but -9 alone is not enough to
    # prove an out-of-memory condition, so keep the more precise KILLED label.
    if exit_code in (-9, 137):
        return "KILLED"
    text = f"{error_type} {error_message}".lower()
    if (
        ("license" in text and any(word in text for word in ("limit", "large", "size")))
        or "problem size limits exceeded" in text
        or "cplex code=1016" in text
        or "promotional version" in text
    ):
        return "LICENSE_LIMIT"
    if (
        "no module named" in text
        or "not installed" in text
        or "executable file 'cpoptimizer' does not exists" in text
        or "solver executable file is not found" in text
        or "ibm cp optimizer is not installed" in text
    ):
        return "UNAVAILABLE"
    if "out of memory" in text or "memoryerror" in text or "cannot allocate" in text:
        return "OOM"
    return "ERROR"


def method_target(method):
    if method.startswith("SAT_"):
        encoding = method.removeprefix("SAT_").lower()
        if encoding not in SAT_ENCODINGS:
            raise ValueError(f"Encoding khong ho tro: {encoding}")
        return worker_sat, encoding
    if method == "CP_ORTools":
        return worker_cp, None
    if method == "ILP_Gurobi":
        return worker_ilp, None
    if method == "MIP_CPLEX":
        return worker_cplex_mip, None
    if method == "CP_CPLEX":
        return worker_cplex_cp, None
    raise ValueError(f"Phuong phap khong ho tro: {method}")


def make_raw_row(phase, n, method, run_index, seed, outcome):
    row = {field: "" for field in RAW_FIELDS}
    row.update(
        {
            "Phase": phase,
            "N": n,
            "Method": method,
            "Run": run_index,
            "Seed": seed,
            "Wall_Time": outcome["wall_time"],
            "Exit_Code": outcome["exit_code"],
        }
    )
    if outcome["kind"] == "RESULT":
        stats = outcome["stats"]
        row.update(
            {
                "Variables": stats.get("num_vars", ""),
                "Clauses": stats.get("num_clauses", ""),
                "Constraints": stats.get("num_constraints", ""),
                "Encoding_Time": stats.get("encoding_time", ""),
                "Solving_Time": stats.get("solving_time", ""),
                "Total_Time": stats.get("total_time", ""),
                "Status": stats.get("status", "UNKNOWN"),
                "Solution_Valid": stats.get("solution_valid", ""),
            }
        )
    elif outcome["kind"] == "TIMEOUT":
        row.update(
            {
                "Status": "TIMEOUT",
                "Error_Type": outcome["error_type"],
                "Error_Message": outcome["error_message"],
            }
        )
    else:
        error_type = outcome.get("error_type", "UnknownError")
        error_message = outcome.get("error_message", "")
        row.update(
            {
                "Status": classify_error(
                    error_type, error_message, outcome.get("exit_code")
                ),
                "Error_Type": error_type,
                "Error_Message": error_message,
            }
        )
    return row


def append_checkpoint(csv_path, row):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()
        os.fsync(handle.fileno())


def completed_keys(csv_path):
    if not csv_path.exists():
        return set()
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return {
            (row["Phase"], int(row["N"]), row["Method"], int(row["Run"]))
            for row in csv.DictReader(handle)
        }


def aggregate_status(statuses):
    counts = pd.Series(statuses).value_counts().to_dict()
    if len(counts) == 1:
        return next(iter(counts))
    parts = ",".join(f"{name}:{counts[name]}" for name in sorted(counts))
    return f"MIXED({parts})"


def median_or_nan(series):
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.median()) if not values.empty else math.nan


def normalize_statuses(raw):
    """Normalize statuses produced by older benchmark versions.

    Raw checkpoint files remain immutable.  The normalization is applied only
    while aggregating/copying data so legacy worker exits with code -9 are not
    presented as generic program errors.
    """
    normalized = raw.copy()
    if {"Status", "Exit_Code"}.issubset(normalized.columns):
        exit_codes = pd.to_numeric(normalized["Exit_Code"], errors="coerce")
        killed = normalized["Status"].eq("ERROR") & exit_codes.isin([-9, 137])
        normalized.loc[killed, "Status"] = "KILLED"
    return normalized


def write_summary(raw_path, summary_path):
    raw = normalize_statuses(pd.read_csv(raw_path))
    rows = []
    for (n, method), group in raw.groupby(["N", "Method"], sort=True):
        solved = group[group["Status"].isin(["SAT", "UNSAT"])]
        times = pd.to_numeric(solved["Total_Time"], errors="coerce").dropna()
        sat_rows = solved[solved["Status"] == "SAT"]
        total_runs = int(len(group))
        successful_runs = int(len(solved))
        wall_times = (
            pd.to_numeric(group["Wall_Time"], errors="coerce").dropna()
            if "Wall_Time" in group
            else pd.Series(dtype=float)
        )
        known_non_errors = {
            "SAT", "UNSAT", "TIMEOUT", "LICENSE_LIMIT", "UNAVAILABLE",
            "OOM", "KILLED", "INVALID_SOLUTION",
        }
        rows.append(
            {
                "N": int(n),
                "Method": method,
                "Variables": median_or_nan(solved["Variables"]),
                "Clauses": median_or_nan(solved["Clauses"]),
                "Constraints": median_or_nan(solved["Constraints"]),
                "Total_Time": float(times.median()) if not times.empty else math.nan,
                "Min_Time": float(times.min()) if not times.empty else math.nan,
                "Max_Time": float(times.max()) if not times.empty else math.nan,
                "Successful_Runs": successful_runs,
                "Success_Rate": successful_runs / total_runs,
                "Timeout_Runs": int((group["Status"] == "TIMEOUT").sum()),
                "License_Limit_Runs": int(
                    (group["Status"] == "LICENSE_LIMIT").sum()
                ),
                "Unavailable_Runs": int(
                    (group["Status"] == "UNAVAILABLE").sum()
                ),
                "OOM_Runs": int((group["Status"] == "OOM").sum()),
                "Killed_Runs": int((group["Status"] == "KILLED").sum()),
                "Invalid_Runs": int(
                    (group["Status"] == "INVALID_SOLUTION").sum()
                ),
                "Error_Runs": int(
                    (~group["Status"].isin(["SAT", "UNSAT", "TIMEOUT"])).sum()
                ),
                "Other_Error_Runs": int(
                    (~group["Status"].isin(known_non_errors)).sum()
                ),
                "Total_Runs": total_runs,
                "Median_Wall_Time": (
                    float(wall_times.median()) if not wall_times.empty else math.nan
                ),
                "Status": aggregate_status(group["Status"]),
                "All_Solutions_Valid": (
                    bool(sat_rows["Solution_Valid"].astype(str).str.lower().eq("true").all())
                    if not sat_rows.empty else ""
                ),
            }
        )

    summary = pd.DataFrame(rows).sort_values(["N", "Method"])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = summary_path.with_suffix(summary_path.suffix + ".tmp")
    summary.to_csv(temp_path, index=False)
    os.replace(temp_path, summary_path)


def package_version(package_name):
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def detect_cpu_model():
    processor = platform.processor().strip()
    if processor:
        return processor

    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()

    try:
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except OSError:
        return None


def detect_memory_gib():
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        match = re.search(
            r"^MemTotal:\s+(\d+)\s+kB$",
            meminfo.read_text(encoding="utf-8", errors="ignore"),
            flags=re.MULTILINE,
        )
        if match:
            return round(int(match.group(1)) / 1024**2, 2)

    try:
        result = subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            check=False,
            capture_output=True,
            text=True,
        )
        value = result.stdout.strip()
        return round(int(value) / 1024**3, 2) if value else None
    except (OSError, ValueError):
        return None


def write_environment(output_dir, args):
    metadata = {
        "timestamp_local": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "phase": args.phase,
        "n_values": args.n_values,
        "methods": args.methods,
        "repetitions": args.repetitions,
        "timeout_seconds": args.timeout,
        "workers_per_solver": args.workers,
        "base_seed": args.seed,
        "platform": platform.platform(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "cpu_model": detect_cpu_model(),
        "memory_total_gib": detect_memory_gib(),
        "sat_random_seed_applied": False,
        "timing_scope": (
            "Total_Time includes model/encoding construction and solve time; "
            "Wall_Time also includes child-process startup and IPC overhead."
        ),
        "packages": {
            name: package_version(name)
            for name in (
                "python-sat", "ortools", "gurobipy", "cplex", "docplex",
                "pandas", "matplotlib", "seaborn",
            )
        },
    }
    path = output_dir / "environment.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        stable_fields = (
            "phase", "timeout_seconds", "workers_per_solver", "base_seed"
        )
        changed = [
            name for name in stable_fields if previous.get(name) != metadata.get(name)
        ]
        if changed:
            details = ", ".join(
                f"{name}: {previous.get(name)!r} -> {metadata.get(name)!r}"
                for name in changed
            )
            raise SystemExit(
                "Cau hinh resume khac lan chay truoc (" + details + "). "
                "Hay dung lai tham so cu hoac chon --output-dir moi."
            )
        metadata["timestamp_first_run"] = previous.get(
            "timestamp_first_run", previous.get("timestamp_local")
        )
    path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=PHASES, default="smoke")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--n-values", type=int, nargs="+")
    parser.add_argument("--methods", nargs="+", choices=ALL_METHODS)
    parser.add_argument("--include-pairwise-large", action="store_true")
    parser.add_argument("--include-ilp-large", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()

    config = PHASES[args.phase]
    args.n_values = tuple(args.n_values or config["n_values"])
    args.methods = list(args.methods or config["methods"])
    args.repetitions = (
        config["repetitions"] if args.repetitions is None else args.repetitions
    )
    args.timeout = config["timeout"] if args.timeout is None else args.timeout
    args.output_dir = args.output_dir or Path("results") / args.phase

    if args.phase == "large" and args.include_pairwise_large:
        args.methods.insert(0, "SAT_Pairwise")
    if args.phase == "large" and args.include_ilp_large:
        args.methods.append("ILP_Gurobi")
    args.methods = tuple(dict.fromkeys(args.methods))

    if args.repetitions < 1 or args.timeout <= 0 or args.workers < 1:
        parser.error("repetitions, timeout va workers phai lon hon 0")
    if any(n < 1 for n in args.n_values):
        parser.error("Moi N phai >= 1")
    return args


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    raw_path = output_dir / "benchmark_raw.csv"
    summary_path = output_dir / "benchmark_results.csv"

    if args.fresh and raw_path.exists():
        raise SystemExit(
            f"{raw_path} da ton tai. Doi output hoac bo --fresh de resume."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_environment(output_dir, args)
    done = completed_keys(raw_path)
    total = len(args.n_values) * len(args.methods) * args.repetitions
    skipped = sum(
        (args.phase, n, method, run_index) in done
        for n in args.n_values
        for method in args.methods
        for run_index in range(1, args.repetitions + 1)
    )

    print(f"Phase       : {args.phase}")
    print(f"N           : {list(args.n_values)}")
    print(f"Methods     : {list(args.methods)}")
    print(f"Repetitions : {args.repetitions}")
    print(f"Timeout     : {args.timeout:.1f}s / run")
    print(f"Output      : {output_dir}")
    print(f"Resume      : bo qua {skipped}/{total} run da co")

    completed = skipped
    for n in args.n_values:
        print(f"\n--- N = {n} ---")
        for method in args.methods:
            target, encoding = method_target(method)
            for run_index in range(1, args.repetitions + 1):
                key = (args.phase, n, method, run_index)
                if key in done:
                    continue

                run_seed = args.seed + run_index - 1
                if encoding is None:
                    worker_args = (n, args.timeout, args.workers, run_seed)
                else:
                    worker_args = (n, encoding, args.timeout, args.workers, run_seed)

                print(
                    f"[{completed + 1:>3}/{total}] {method:<16} run={run_index}",
                    end=" ", flush=True,
                )
                outcome = run_with_timeout(target, worker_args, args.timeout)
                row = make_raw_row(args.phase, n, method, run_index, run_seed, outcome)
                append_checkpoint(raw_path, row)
                write_summary(raw_path, summary_path)
                completed += 1

                if row["Total_Time"] != "":
                    detail = f" {float(row['Total_Time']):.4f}s"
                elif row["Error_Type"]:
                    detail = f" ({row['Error_Type']})"
                else:
                    detail = ""
                print(f"-> {row['Status']}{detail}")

    write_summary(raw_path, summary_path)
    print("\nHoan tat.")
    print(f"Du lieu tho : {raw_path}")
    print(f"Tong hop    : {summary_path}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
