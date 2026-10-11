from nqueens.sat_solver import NQueensSATSolver
from nqueens.utils import get_positions_from_1d_vars, validate_solution, print_board

def main():
    n = 8  # Chạy thử với bàn cờ 8x8
    encodings = ['pairwise', 'sequential', 'commander', 'product', 'binary']
    
    print(f"--- THỬ NGHIỆM N-QUEENS VỚI N={n} ---")
    
    for enc in encodings:
        print(f"\n[*] Giải bằng thuật toán mã hóa: {enc.upper()}")
        solver = NQueensSATSolver(n, encoding_type=enc)
        true_vars, stats = solver.solve()
        
        print(f"  - Số biến (Variables)  : {stats['num_vars']}")
        print(f"  - Số mệnh đề (Clauses) : {stats['num_clauses']}")
        print(f"  - Thời gian (Total)    : {stats['total_time']:.4f} giây")
        
        if stats['is_sat']:
            positions = get_positions_from_1d_vars(n, true_vars)
            is_valid = validate_solution(n, positions)
            print(f"  - Kết quả hợp lệ?      : {'✅ CÓ' if is_valid else '❌ KHÔNG'}")
            if enc == 'pairwise':  # Chỉ in bàn cờ 1 lần cho đỡ dài
                print_board(n, positions)
        else:
            print("  - KHÔNG TÌM THẤY LỜI GIẢI!")

if __name__ == "__main__":
    main()
