# Hướng dẫn chạy N-Queens trên Google Colab

Quy trình gồm bốn phase benchmark (smoke, standard, CPLEX và large). Mỗi
lần chạy được ghi ngay vào
`benchmark_raw.csv`, nên nếu Colab ngắt giữa chừng chỉ cần chạy lại
đúng lệnh cũ. Chương trình sẽ bỏ qua các run đã hoàn thành.

Không chọn GPU. Các solver trong bài này sử dụng CPU và RAM.

## Phase 0 - Chuẩn bị Colab

### 0.1. Lấy project từ GitHub

Repository của project:

```text
https://github.com/WilliamsBui-fnd/INT3011E_3
```

Tạo notebook Colab mới, chọn `Runtime > Change runtime type > CPU`, rồi chạy:

```python
from google.colab import drive
drive.mount("/content/drive")
```

Clone project vào ổ đĩa tạm của Colab:

```python
%cd /content
!git clone https://github.com/WilliamsBui-fnd/INT3011E_3.git
%cd /content/INT3011E_3
```

> Nên chạy mã nguồn trong `/content` cho nhanh, nhưng ghi kết quả trực tiếp
> vào Drive để không mất dữ liệu khi runtime bị reset.

### 0.2. Cài thư viện

```python
!python -m pip install -q -r requirements.txt
```

Nếu Colab yêu cầu restart runtime sau khi cài, hãy restart, mount Drive và
`%cd /content/INT3011E_3` lại.

### 0.3. Chọn thư mục lưu kết quả

```python
RESULT_ROOT = "/content/drive/MyDrive/NQueens_BTL1_results"
```

### 0.4. Chạy unit test

```python
!python -m unittest discover -s tests -v
```

Chỉ chuyển sang Phase 1 khi kết quả cuối cùng hiện `OK`. Test CPLEX CP
có thể hiện `skipped` trên Colab thông thường do không có executable
`cpoptimizer`; đây là giới hạn môi trường IBM, không phải lỗi SAT/CP-SAT.

## Phase 1 - Smoke test

Mục đích: kiểm tra cài đặt, SAT/UNSAT, tính hợp lệ của nghiệm và
khả năng gọi Gurobi. Phase này chạy `N = 1, 2, 3, 4, 8`, mỗi cấu hình
một lần.

```python
!python benchmark.py \
  --phase smoke \
  --output-dir "{RESULT_ROOT}/smoke"
```

Kiểm tra kết quả:

```python
import pandas as pd

smoke = pd.read_csv(f"{RESULT_ROOT}/smoke/benchmark_raw.csv")
display(smoke[["N", "Method", "Status", "Solution_Valid", "Error_Message"]])
print(smoke["Status"].value_counts())
```

Kỳ vọng:

- `N=2` và `N=3`: `UNSAT` cho mọi solver.
- `N=1,4,8`: `SAT`; `Solution_Valid=True`.
- Không có `INVALID_SOLUTION` hay `ERROR`.

## Phase 2 - Benchmark chuẩn

Phase này chạy `N = 16, 32, 64, 128`, đủ năm SAT encoding, CP-SAT và
Gurobi, mỗi cấu hình 5 lần, timeout 60 giây và mỗi solver dùng 1 worker.

```python
!python benchmark.py \
  --phase standard \
  --output-dir "{RESULT_ROOT}/standard"
```

Nếu Colab ngắt, mount Drive, giải nén/cài lại project rồi chạy nguyên lệnh
trên. Dòng `Resume` sẽ cho biết bao nhiêu run đã được bỏ qua.

Kiểm tra nhanh:

```python
standard = pd.read_csv(f"{RESULT_ROOT}/standard/benchmark_results.csv")
display(standard)

raw_standard = pd.read_csv(f"{RESULT_ROOT}/standard/benchmark_raw.csv")
display(pd.crosstab(raw_standard["Method"], raw_standard["Status"]))
```

Với Gurobi license miễn phí, `ILP_Gurobi` từ `N=64` có thể hiện
`LICENSE_LIMIT`. Đây là kết quả hợp lệ về giới hạn môi trường, không phải
`TIMEOUT`.

## Phase 2B - CPLEX MIP và CPLEX CP

```python
!python benchmark.py \
  --phase cplex \
  --output-dir "{RESULT_ROOT}/cplex"
```

Trên Colab tiêu chuẩn, kết quả dự kiến:

- `MIP_CPLEX` chạy được các mô hình nhỏ. Community Edition có thể ghi
  `LICENSE_LIMIT` khi số biến/ràng buộc vượt giới hạn.
- `CP_CPLEX` có thể chạy được hoặc ghi `UNAVAILABLE`, tùy runtime có
  executable `cpoptimizer` hay không. Trong lần chạy ngày 11/10/2026,
  `CP_CPLEX` đã chạy thành công ở `N=8,16,32`.

Để có số liệu CPLEX CP thật cho báo cáo, cần chạy cùng phase trên
IBM Decision Optimization runtime hoặc máy có bản quyền CPLEX Optimization
Studio/CP Optimizer. Không được đổi `UNAVAILABLE` thành `TIMEOUT` hay tự tạo
số liệu.

Nếu muốn CPLEX có cùng 5 lần lặp với phase standard, chạy lại theo
cơ chế resume; chương trình chỉ bổ sung run 4 và 5:

```python
!python benchmark.py \
  --phase cplex \
  --repetitions 5 \
  --output-dir "{RESULT_ROOT}/cplex"
```

## Phase 3 - Benchmark kích thước lớn

Phase này chạy `N = 256, 512, 1000`, 3 lần/cấu hình, timeout 120 giây.
Mặc định loại Pairwise vì nguy cơ hết RAM và loại Gurobi vì license giới hạn.

```python
!python benchmark.py \
  --phase large \
  --output-dir "{RESULT_ROOT}/large"
```

Không thêm `--include-pairwise-large` trên Colab Free. Tùy chọn này chỉ dành
cho máy high-memory và có thể làm sập runtime.

Nếu đã cấu hình Gurobi Academic/WLS và muốn thử riêng `N=256`:

```python
!python benchmark.py \
  --phase large \
  --n-values 256 \
  --methods ILP_Gurobi \
  --repetitions 3 \
  --timeout 120 \
  --output-dir "{RESULT_ROOT}/gurobi_academic_256"
```

Không đưa WLS secret hoặc file `gurobi.lic` lên GitHub.

## Phase 4 - Gộp dữ liệu và vẽ biểu đồ

```python
!python combine_results.py \
  "{RESULT_ROOT}/smoke" \
  "{RESULT_ROOT}/standard" \
  "{RESULT_ROOT}/cplex" \
  "{RESULT_ROOT}/large" \
  --output-dir "{RESULT_ROOT}/combined"
```

```python
!python plot_results.py \
  --input "{RESULT_ROOT}/combined/benchmark_results.csv" \
  --raw "{RESULT_ROOT}/combined/benchmark_raw.csv" \
  --output-dir "{RESULT_ROOT}/combined"
```

Xem ba biểu đồ:

```python
from IPython.display import display, Image

for name in (
    "plot_time.png", "plot_status.png", "plot_variables.png", "plot_clauses.png"
):
    display(Image(filename=f"{RESULT_ROOT}/combined/{name}"))
```

## Các file phải giữ lại cho báo cáo

- `benchmark_raw.csv`: tất cả lần chạy, bao gồm timeout và lỗi.
- `benchmark_results.csv`: median/min/max và tỷ lệ thành công.
- `environment.json`: hệ điều hành, Python, số CPU và phiên bản thư viện.
- Bốn file `plot_*.png`, bao gồm ma trận trạng thái `plot_status.png`.

`Glucose3` trong PySAT không nhận seed từ script này. Vì vậy các lần
lặp SAT đo dao động thời gian của môi trường, không phải các quá trình
tìm kiếm ngẫu nhiên độc lập. Phải nêu rõ điều này trong báo cáo.

Luôn dùng dữ liệu trong `NQueens_BTL1_results/combined` cho báo cáo chính.
