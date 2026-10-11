import time
from ortools.sat.python import cp_model

class NQueensCPSolver:
    def __init__(self, n):
        self.n = n
        
    def solve(self, time_limit=None, num_workers=1, random_seed=0):
        start_time = time.time()
        
        model = cp_model.CpModel()
        
        # Biến: queens[i] = j có nghĩa là quân hậu ở hàng i nằm ở cột j
        queens = [model.NewIntVar(0, self.n - 1, f'q_{i}') for i in range(self.n)]
        
        # Ràng buộc: Tất cả các cột phải khác nhau (vì hàng đã tự động khác nhau)
        model.AddAllDifferent(queens)
        
        # Ràng buộc: Tất cả các đường chéo chính và phụ phải khác nhau
        model.AddAllDifferent([queens[i] + i for i in range(self.n)])
        model.AddAllDifferent([queens[i] - i for i in range(self.n)])
        
        encoding_time = time.time() - start_time
        
        solver = cp_model.CpSolver()
        if time_limit is not None:
            solver.parameters.max_time_in_seconds = float(time_limit)
        solver.parameters.num_search_workers = int(num_workers)
        solver.parameters.random_seed = int(random_seed)
        
        solve_start = time.time()
        status = solver.Solve(model)
        solve_time = time.time() - solve_start
        
        total_time = time.time() - start_time
        
        is_sat = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        if is_sat:
            status_name = 'SAT'
        elif status == cp_model.INFEASIBLE:
            status_name = 'UNSAT'
        elif status == cp_model.MODEL_INVALID:
            status_name = 'MODEL_INVALID'
        else:
            status_name = 'TIMEOUT' if time_limit is not None else 'UNKNOWN'
        
        stats = {
            'is_sat': is_sat,
            'status': status_name,
            'solver_status': solver.StatusName(status),
            'encoding_time': encoding_time,
            'solving_time': solve_time,
            'total_time': total_time
        }
        
        positions = []
        if is_sat:
            for i in range(self.n):
                positions.append((i, solver.Value(queens[i])))
                
        return positions, stats
