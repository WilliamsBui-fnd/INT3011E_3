import os
import time
from pathlib import Path


def configure_gurobi_license():
    """Use an explicit license path, or the private file next to this project."""
    if os.environ.get("GRB_LICENSE_FILE"):
        return
    local_license = Path(__file__).resolve().parent.parent / "gurobi.lic"
    if local_license.is_file():
        os.environ["GRB_LICENSE_FILE"] = str(local_license)


class NQueensILPSolver:
    def __init__(self, n):
        self.n = n
        
    def solve(self, time_limit=None, num_workers=1, random_seed=0):
        configure_gurobi_license()
        import gurobipy as gp
        from gurobipy import GRB

        start_time = time.time()
        env = None
        model = None
        try:
            # Tạo environment không log ra màn hình
            env = gp.Env(empty=True)
            env.setParam("OutputFlag", 0)
            env.start()
            model = gp.Model("nqueens", env=env)
            model.setParam("Threads", int(num_workers))
            model.setParam("Seed", int(random_seed))
            if time_limit is not None:
                model.setParam("TimeLimit", float(time_limit))

            # Tạo ma trận biến nhị phân N x N
            x = model.addVars(self.n, self.n, vtype=GRB.BINARY, name="x")

            # Mỗi hàng có đúng 1 hậu
            model.addConstrs((x.sum(i, '*') == 1 for i in range(self.n)), name="row")

            # Mỗi cột có đúng 1 hậu
            model.addConstrs((x.sum('*', j) == 1 for j in range(self.n)), name="col")

            # Tối đa 1 hậu trên đường chéo (Top-Left -> Bottom-Right)
            for d in range(1 - self.n, self.n):
                model.addConstr(gp.quicksum(x[i, i - d] for i in range(self.n) if 0 <= i - d < self.n) <= 1)

            # Tối đa 1 hậu trên đường chéo (Top-Right -> Bottom-Left)
            for d in range(2 * self.n - 1):
                model.addConstr(gp.quicksum(x[i, d - i] for i in range(self.n) if 0 <= d - i < self.n) <= 1)

            model.update()
            encoding_time = time.time() - start_time

            solve_start = time.time()
            model.optimize()
            solve_time = time.time() - solve_start
            total_time = time.time() - start_time

            has_solution = model.SolCount > 0
            if has_solution:
                status_name = 'SAT'
            elif model.status == GRB.INFEASIBLE:
                status_name = 'UNSAT'
            elif model.status == GRB.TIME_LIMIT:
                status_name = 'TIMEOUT'
            else:
                status_name = f'GUROBI_STATUS_{model.status}'

            stats = {
                'is_sat': has_solution,
                'status': status_name,
                'solver_status': int(model.status),
                'num_vars': int(model.NumVars),
                'num_constraints': int(model.NumConstrs),
                'encoding_time': encoding_time,
                'solving_time': solve_time,
                'total_time': total_time
            }

            positions = []
            if has_solution:
                for i in range(self.n):
                    for j in range(self.n):
                        if x[i, j].X > 0.5:
                            positions.append((i, j))

            return positions, stats
        finally:
            if model is not None:
                model.dispose()
            if env is not None:
                env.dispose()
