import importlib.util
import shutil
import unittest

from pysat.card import EncType
from pysat.solvers import Glucose3

from nqueens.cp_solver import NQueensCPSolver
from nqueens.ilp_solver import NQueensILPSolver
from nqueens.sat_encoder import NQueensSATEncoder
from nqueens.sat_solver import NQueensSATSolver
from nqueens.utils import get_positions_from_1d_vars, validate_solution


def expected_sat(n):
    return n == 1 or n >= 4


class SolverCorrectnessTests(unittest.TestCase):
    def test_amo_encodings_truth_table(self):
        enc_map = {
            "pairwise": EncType.pairwise,
            "sequential": EncType.seqcounter,
            "binary": EncType.bitwise,
        }
        for encoding in ("pairwise", "sequential", "commander", "product", "binary"):
            with self.subTest(encoding=encoding):
                encoder = NQueensSATEncoder(10)
                variables = [1, 2, 3, 4, 5]
                encoder._at_most_one(variables, encoding, enc_map)
                with Glucose3(bootstrap_with=encoder.clauses) as solver:
                    for mask in range(1 << len(variables)):
                        assumptions = [
                            var if mask & (1 << index) else -var
                            for index, var in enumerate(variables)
                        ]
                        self.assertEqual(
                            solver.solve(assumptions=assumptions),
                            mask.bit_count() <= 1,
                        )

    def test_all_sat_encodings(self):
        encodings = ("pairwise", "sequential", "commander", "product", "binary")
        for n in range(1, 9):
            for encoding in encodings:
                with self.subTest(n=n, encoding=encoding):
                    true_vars, stats = NQueensSATSolver(n, encoding).solve()
                    self.assertEqual(stats["is_sat"], expected_sat(n))
                    if stats["is_sat"]:
                        positions = get_positions_from_1d_vars(n, true_vars)
                        self.assertTrue(validate_solution(n, positions))

    def test_cp_solver(self):
        for n in range(1, 9):
            with self.subTest(n=n):
                positions, stats = NQueensCPSolver(n).solve(
                    time_limit=10, num_workers=1, random_seed=2026
                )
                self.assertEqual(stats["is_sat"], expected_sat(n))
                if stats["is_sat"]:
                    self.assertTrue(validate_solution(n, positions))

    def test_validate_solution_rejects_out_of_bounds_coordinates(self):
        self.assertFalse(validate_solution(1, [(1, 0)]))
        self.assertFalse(validate_solution(1, [(-1, 0)]))

    def test_ilp_solver_small_instances(self):
        for n in range(1, 6):
            with self.subTest(n=n):
                positions, stats = NQueensILPSolver(n).solve(
                    time_limit=10, num_workers=1, random_seed=2026
                )
                self.assertEqual(stats["is_sat"], expected_sat(n))
                if stats["is_sat"]:
                    self.assertTrue(validate_solution(n, positions))

    @unittest.skipUnless(
        importlib.util.find_spec("docplex") and importlib.util.find_spec("cplex"),
        "CPLEX/DOcplex is not installed",
    )
    def test_cplex_mip_small_instances(self):
        from nqueens.cplex_mip_solver import NQueensCplexMIPSolver

        for n in range(1, 6):
            with self.subTest(n=n):
                positions, stats = NQueensCplexMIPSolver(n).solve(
                    time_limit=10, num_workers=1, random_seed=2026
                )
                self.assertEqual(stats["is_sat"], expected_sat(n))
                if stats["is_sat"]:
                    self.assertTrue(validate_solution(n, positions))

    @unittest.skipUnless(
        importlib.util.find_spec("docplex") and shutil.which("cpoptimizer"),
        "IBM CP Optimizer executable is not installed",
    )
    def test_cplex_cp_small_instances(self):
        from nqueens.cplex_cp_solver import NQueensCplexCPSolver

        for n in range(1, 6):
            with self.subTest(n=n):
                positions, stats = NQueensCplexCPSolver(n).solve(
                    time_limit=10, num_workers=1, random_seed=2026
                )
                self.assertEqual(stats["is_sat"], expected_sat(n))
                if stats["is_sat"]:
                    self.assertTrue(validate_solution(n, positions))


if __name__ == "__main__":
    unittest.main()
