def validate_solution(n, solution):
    """
    Kiểm tra xem giải pháp N-Queens có hợp lệ hay không.
    :param n: Kích thước bàn cờ (n x n).
    :param solution: Danh sách các tọa độ (row, col) của N quân hậu (0-indexed).
    :return: True nếu hợp lệ, ngược lại False.
    """
    if len(solution) != n:
        return False
        
    rows = set()
    cols = set()
    diag1 = set() # Đường chéo chính (row - col)
    diag2 = set() # Đường chéo phụ (row + col)
    
    for r, c in solution:
        if not (0 <= r < n and 0 <= c < n):
            return False
        if r in rows or c in cols or (r - c) in diag1 or (r + c) in diag2:
            return False
        rows.add(r)
        cols.add(c)
        diag1.add(r - c)
        diag2.add(r + c)
        
    return True

def print_board(n, solution):
    """
    In bàn cờ N-Queens ra màn hình console.
    :param n: Kích thước bàn cờ.
    :param solution: Danh sách các tọa độ (row, col) của N quân hậu.
    """
    board = [['.' for _ in range(n)] for _ in range(n)]
    for r, c in solution:
        board[r][c] = 'Q'
        
    for row in board:
        print(" ".join(row))
    print()

def get_positions_from_1d_vars(n, true_vars):
    """
    Chuyển đổi danh sách các biến SAT mang giá trị True (1D) thành tọa độ (row, col).
    Hệ biến mặc định: id = row * n + col + 1 (1-indexed cho PySAT).
    """
    positions = []
    for var in true_vars:
        if var > 0 and var <= n * n:
            val = var - 1
            row = val // n
            col = val % n
            positions.append((row, col))
    return positions
