import contextlib
import io
from pathlib import Path
import shutil
import time
import warnings


class NQueensCplexCPSolver:
    """Mo hinh N-Queens bang DOcplex CP / IBM CP Optimizer.

    Goi Python `docplex` la chua du; may chay con can executable `cpoptimizer`
    tu IBM ILOG CPLEX Optimization Studio hoac mot IBM runtime co CP Optimizer.
    """

    def __init__(self, n):
        self.n = n

    def solve(self, time_limit=None, num_workers=1, random_seed=0):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            from docplex.cp.config import context
            from docplex.cp.model import CpoModel, all_diff, integer_var

        if context.solver.agent == "local":
            executable = str(context.solver.local.execfile)
            executable_exists = Path(executable).is_file() or shutil.which(executable)
            if not executable_exists:
                raise RuntimeError(
                    "IBM CP Optimizer is not installed: executable file "
                    f"{executable!r} was not found"
                )

        start_time = time.time()
        model = CpoModel(name="nqueens_cplex_cp")
        queens = [
            integer_var(0, self.n - 1, name=f"q_{i}")
            for i in range(self.n)
        ]
        model.add(all_diff(queens))
        model.add(all_diff([queens[i] + i for i in range(self.n)]))
        model.add(all_diff([queens[i] - i for i in range(self.n)]))
        encoding_time = time.time() - start_time

        solve_kwargs = {
            "Workers": int(num_workers),
            "RandomSeed": int(random_seed),
            "LogVerbosity": "Quiet",
        }
        if time_limit is not None:
            solve_kwargs["TimeLimit"] = float(time_limit)

        solve_start = time.time()
        # DOcplex in mot banner dai truoc khi bao thieu executable. Benchmark
        # chi can exception co cau truc, nen giu console sach.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            result = model.solve(**solve_kwargs)
        solve_time = time.time() - solve_start
        total_time = time.time() - start_time
        solver_status = str(result.get_solve_status())
        lowered = solver_status.lower()
        is_sat = result.is_solution()

        if is_sat:
            status_name = "SAT"
        elif "infeasible" in lowered:
            status_name = "UNSAT"
        elif "unknown" in lowered and time_limit is not None:
            status_name = "TIMEOUT"
        else:
            status_name = "CPLEX_CP_UNKNOWN"

        positions = []
        if is_sat:
            positions = [
                (i, int(result.get_value(queens[i]))) for i in range(self.n)
            ]

        stats = {
            "is_sat": is_sat,
            "status": status_name,
            "solver_status": solver_status,
            "num_vars": self.n,
            "num_constraints": 3,
            "encoding_time": encoding_time,
            "solving_time": solve_time,
            "total_time": total_time,
        }
        return positions, stats
