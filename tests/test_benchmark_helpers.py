import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from benchmark import (
    classify_error,
    completed_keys,
    make_raw_row,
    normalize_statuses,
    write_summary,
)
from nqueens.ilp_solver import configure_gurobi_license


class BenchmarkHelperTests(unittest.TestCase):
    def test_explicit_license_path_takes_precedence(self):
        with patch.dict("os.environ", {"GRB_LICENSE_FILE": "/private/test.lic"}):
            configure_gurobi_license()
            self.assertEqual(os.environ["GRB_LICENSE_FILE"], "/private/test.lic")

    def test_gurobi_error_status_survives_redaction(self):
        outcome = {
            "kind": "ERROR", "wall_time": 0.1, "exit_code": 0,
            "error_type": "GurobiError",
            "error_message": "Gurobi LICENSE_LIMIT; details suppressed",
            "status": "LICENSE_LIMIT",
        }
        row = make_raw_row("standard", 64, "ILP_Gurobi", 1, 2026, outcome)
        self.assertEqual(row["Status"], "LICENSE_LIMIT")
        self.assertEqual(row["Error_Message"], outcome["error_message"])

    def test_error_classification(self):
        self.assertEqual(
            classify_error(
                "GurobiError", "Model too large for size-limited license"
            ),
            "LICENSE_LIMIT",
        )
        self.assertEqual(
            classify_error("MemoryError", "cannot allocate memory"), "OOM"
        )
        self.assertEqual(
            classify_error("ModuleNotFoundError", "No module named x"),
            "UNAVAILABLE",
        )
        self.assertEqual(
            classify_error("WorkerExitedWithoutResult", "", exit_code=-9),
            "KILLED",
        )

    def test_normalize_legacy_sigkill(self):
        raw = pd.DataFrame(
            [
                {"Status": "ERROR", "Exit_Code": -9},
                {"Status": "ERROR", "Exit_Code": 1},
                {"Status": "TIMEOUT", "Exit_Code": -15},
            ]
        )
        normalized = normalize_statuses(raw)
        self.assertEqual(normalized["Status"].tolist(), ["KILLED", "ERROR", "TIMEOUT"])

    def test_summary_keeps_timeout_measurements_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw = Path(temp_dir) / "benchmark_raw.csv"
            fields = [
                "Phase", "N", "Method", "Run", "Variables", "Clauses",
                "Constraints", "Total_Time", "Status", "Solution_Valid",
            ]
            with raw.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "Phase": "standard", "N": 16,
                        "Method": "SAT_Pairwise", "Run": 1,
                        "Variables": 256, "Clauses": 6352,
                        "Total_Time": 0.1, "Status": "SAT",
                        "Solution_Valid": True,
                    }
                )
                writer.writerow(
                    {
                        "Phase": "standard", "N": 32,
                        "Method": "SAT_Pairwise", "Run": 1,
                        "Status": "TIMEOUT",
                    }
                )

            summary_path = Path(temp_dir) / "benchmark_results.csv"
            write_summary(raw, summary_path)
            summary = pd.read_csv(summary_path)
            timeout_row = summary[summary["N"] == 32].iloc[0]
            self.assertTrue(pd.isna(timeout_row["Variables"]))
            self.assertTrue(pd.isna(timeout_row["Clauses"]))
            self.assertTrue(pd.isna(timeout_row["Total_Time"]))
            self.assertEqual(timeout_row["Status"], "TIMEOUT")
            self.assertEqual(timeout_row["Success_Rate"], 0.0)
            self.assertEqual(timeout_row["Timeout_Runs"], 1)

    def test_completed_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "raw.csv"
            path.write_text(
                "Phase,N,Method,Run\nsmoke,4,SAT_Pairwise,1\n",
                encoding="utf-8",
            )
            self.assertEqual(
                completed_keys(path), {("smoke", 4, "SAT_Pairwise", 1)}
            )


if __name__ == "__main__":
    unittest.main()
