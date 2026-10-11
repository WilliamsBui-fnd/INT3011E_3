import time


class NQueensCplexMIPSolver:
    """Mo hinh N-Queens bang DOcplex MP / IBM CPLEX."""

    def __init__(self, n):
        self.n = n

    def solve(self, time_limit=None, num_workers=1, random_seed=0):
        from docplex.mp.model import Model

        start_time = time.time()
        model = Model(name="nqueens_cplex_mip")
        try:
            model.parameters.threads = int(num_workers)
            model.parameters.randomseed = int(random_seed)
            if time_limit is not None:
                model.parameters.timelimit = float(time_limit)

            x = model.binary_var_matrix(
                range(self.n), range(self.n), name="x"
            )
            model.add_constraints(
                model.sum(x[i, j] for j in range(self.n)) == 1
                for i in range(self.n)
            )
            model.add_constraints(
                model.sum(x[i, j] for i in range(self.n)) == 1
                for j in range(self.n)
            )
            for diagonal in range(1 - self.n, self.n):
                model.add_constraint(
                    model.sum(
                        x[i, i - diagonal]
                        for i in range(self.n)
                        if 0 <= i - diagonal < self.n
                    )
                    <= 1
                )
            for diagonal in range(2 * self.n - 1):
                model.add_constraint(
                    model.sum(
                        x[i, diagonal - i]
                        for i in range(self.n)
                        if 0 <= diagonal - i < self.n
                    )
                    <= 1
                )

            encoding_time = time.time() - start_time
            solve_start = time.time()
            solution = model.solve(log_output=False)
            solve_time = time.time() - solve_start
            total_time = time.time() - start_time
            details_status = str(model.solve_details.status)
            lowered = details_status.lower()

            if solution is not None:
                status_name = "SAT"
            elif "infeasible" in lowered:
                status_name = "UNSAT"
            elif "time limit" in lowered or "timelimit" in lowered:
                status_name = "TIMEOUT"
            else:
                status_name = "CPLEX_UNKNOWN"

            positions = []
            if solution is not None:
                for i in range(self.n):
                    for j in range(self.n):
                        if solution.get_value(x[i, j]) > 0.5:
                            positions.append((i, j))

            stats = {
                "is_sat": solution is not None,
                "status": status_name,
                "solver_status": details_status,
                "num_vars": int(model.number_of_variables),
                "num_constraints": int(model.number_of_constraints),
                "encoding_time": encoding_time,
                "solving_time": solve_time,
                "total_time": total_time,
            }
            return positions, stats
        finally:
            model.end()
