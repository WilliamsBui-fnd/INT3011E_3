"""Gop du lieu tho cua nhieu phase thanh mot bo ket qua."""

import argparse
import os
from pathlib import Path

import pandas as pd

from benchmark import normalize_statuses, write_summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Thu muc phase hoac file benchmark_raw.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/combined"))
    args = parser.parse_args()

    frames = []
    for item in args.inputs:
        path = item / "benchmark_raw.csv" if item.is_dir() else item
        if not path.exists():
            raise SystemExit(f"Khong tim thay: {path}")
        frames.append(pd.read_csv(path))

    combined = normalize_statuses(pd.concat(frames, ignore_index=True))
    combined = combined.drop_duplicates(
        subset=["Phase", "N", "Method", "Run"], keep="last"
    ).sort_values(["N", "Method", "Run"])

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "benchmark_raw.csv"
    temp_path = raw_path.with_suffix(".csv.tmp")
    combined.to_csv(temp_path, index=False)
    os.replace(temp_path, raw_path)
    write_summary(raw_path, output_dir / "benchmark_results.csv")
    print(f"Da gop {len(combined)} run vao {output_dir}")


if __name__ == "__main__":
    main()
