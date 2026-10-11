from nqueens.sat_solver import NQueensSATSolver
from nqueens.cp_solver import NQueensCPSolver
from nqueens.ilp_solver import NQueensILPSolver
from nqueens.utils import get_positions_from_1d_vars, validate_solution, print_board

def main():
    n = 16  # Test với bàn cờ N=16 để thấy sự khác biệt về thời gian
    
    print(f"=====================================")
    print(f"--- THỬ NGHIỆM N-QUEENS VỚI N={n} ---")
    print(f"=====================================\n")
    
    # 1. SAT Solver (dùng Product - một trong các thuật toán nén tốt nhất)
    print("[*] Giải bằng SAT Solving (PySAT - Product Encoding)...")
    sat_solver = NQueensSATSolver(n, encoding_type='product')
    true_vars, sat_stats = sat_solver.solve()
    if sat_stats['is_sat']:
        sat_pos = get_positions_from_1d_vars(n, true_vars)
        print(f"  -> Lời giải hợp lệ? : {'✅' if validate_solution(n, sat_pos) else '❌'}")
    print(f"  -> Thời gian Encode : {sat_stats['encoding_time']:.4f} giây")
    print(f"  -> Thời gian Giải   : {sat_stats['solving_time']:.4f} giây")
    print(f"  -> TỔNG THỜI GIAN   : {sat_stats['total_time']:.4f} giây\n")
        
    # 2. CP Solver (OR-Tools)
    print("[*] Giải bằng Constraint Programming (Google OR-Tools)...")
    cp_solver = NQueensCPSolver(n)
    cp_pos, cp_stats = cp_solver.solve()
    if cp_stats['is_sat']:
        print(f"  -> Lời giải hợp lệ? : {'✅' if validate_solution(n, cp_pos) else '❌'}")
    print(f"  -> Thời gian Encode : {cp_stats['encoding_time']:.4f} giây")
    print(f"  -> Thời gian Giải   : {cp_stats['solving_time']:.4f} giây")
    print(f"  -> TỔNG THỜI GIAN   : {cp_stats['total_time']:.4f} giây\n")

    # 3. ILP Solver (Gurobi)
    print("[*] Giải bằng Integer Linear Programming (Gurobi)...")
    ilp_solver = NQueensILPSolver(n)
    ilp_pos, ilp_stats = ilp_solver.solve()
    if ilp_stats['is_sat']:
        print(f"  -> Lời giải hợp lệ? : {'✅' if validate_solution(n, ilp_pos) else '❌'}")
    print(f"  -> Thời gian Encode : {ilp_stats['encoding_time']:.4f} giây")
    print(f"  -> Thời gian Giải   : {ilp_stats['solving_time']:.4f} giây")
    print(f"  -> TỔNG THỜI GIAN   : {ilp_stats['total_time']:.4f} giây\n")

if __name__ == "__main__":
    main()
