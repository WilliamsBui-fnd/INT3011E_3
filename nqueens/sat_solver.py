import time
from pysat.solvers import Glucose3
from .sat_encoder import NQueensSATEncoder

class NQueensSATSolver:
    def __init__(self, n, encoding_type='pairwise'):
        self.n = n
        self.encoding_type = encoding_type
        
    def solve(self):
        start_time = time.time()
        
        # Bước 1: Mã hóa bài toán thành CNF Clauses
        encoder = NQueensSATEncoder(self.n)
        clauses, total_vars = encoder.encode(self.encoding_type)
        encoding_time = time.time() - start_time
        
        # Bước 2: Nạp vào SAT Solver (Glucose3)
        solve_start = time.time()
        solver = Glucose3()
        try:
            for clause in clauses:
                solver.add_clause(clause)

            is_sat = solver.solve()
            solve_time = time.time() - solve_start
            total_time = time.time() - start_time

            stats = {
                'is_sat': is_sat,
                'status': 'SAT' if is_sat else 'UNSAT',
                'num_vars': total_vars,
                'num_clauses': len(clauses),
                'encoding_time': encoding_time,
                'solving_time': solve_time,
                'total_time': total_time
            }

            if is_sat:
                model = solver.get_model()
                # Lọc lấy các biến thực sự thuộc về bàn cờ (từ 1 đến n^2)
                true_vars = [v for v in model if v > 0 and v <= self.n * self.n]
                return true_vars, stats

            return [], stats
        finally:
            solver.delete()
