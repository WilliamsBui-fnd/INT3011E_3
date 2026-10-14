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

### 0.3. Cấu hình Gurobi Academic WLS

Trên máy Mac, project tự tìm file `gurobi.lic` trong thư mục gốc. Trên Colab,
hãy tải file license lên thư mục **riêng tư** của Google Drive, ví dụ
`MyDrive/private_licenses/gurobi.lic`; không đặt file trong repository, notebook
hoặc thư mục kết quả. Sau khi mount Drive, chạy cell sau mỗi lần runtime mới:

```python
import os
import shutil
from pathlib import Path

license_source = Path("/content/drive/MyDrive/private_licenses/gurobi.lic")
assert license_source.is_file(), "Chưa tìm thấy gurobi.lic trong Drive riêng tư"
license_runtime = Path("/content/gurobi.lic")
shutil.copyfile(license_source, license_runtime)
license_runtime.chmod(0o600)
os.environ["GRB_LICENSE_FILE"] = str(license_runtime)
print("Đã cấu hình đường dẫn license Gurobi; không hiển thị nội dung file.")
```

Gurobi cần kết nối mạng để xác thực WLS. Không chạy cell in nội dung license,
không điền ba giá trị WLS vào notebook và không chia sẻ thư mục Drive này.
Biến `GRB_LICENSE_FILE` phải trỏ tới **file**, theo
[hướng dẫn chính thức của Gurobi](https://support.gurobi.com/hc/en-us/articles/360013417211-Where-do-I-place-the-Gurobi-license-file-gurobi-lic).

### 0.4. Chọn thư mục lưu kết quả

```python
RESULT_ROOT = "/content/drive/MyDrive/NQueens_BTL1_results"
```

### 0.5. Chạy unit test và xác nhận license

```python
!python -m unittest discover -s tests -v
```

Chỉ chuyển sang Phase 1 khi kết quả cuối cùng hiện `OK`. Test CPLEX CP
có thể hiện `skipped` trên Colab thông thường do không có executable
`cpoptimizer`; đây là giới hạn môi trường IBM, không phải lỗi SAT/CP-SAT.

Kiểm tra Gurobi ở $N=46$ (2116 biến nhị phân, vượt giới hạn 2000 biến của
license mặc định). Kết quả cần là `SAT` và `Solution_Valid=True`:

```python
!python benchmark.py \
  --phase standard --n-values 46 --methods ILP_Gurobi \
  --repetitions 1 --timeout 45 \
  --output-dir "{RESULT_ROOT}/gurobi_license_check"

import pandas as pd
check = pd.read_csv(f"{RESULT_ROOT}/gurobi_license_check/benchmark_raw.csv")
display(check[["N", "Method", "Status", "Solution_Valid"]])
```

Đây chỉ là kiểm tra license; **không** gộp thư mục này vào số liệu báo cáo.

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

File `standard` cũ đã có các lượt Gurobi `LICENSE_LIMIT` tại $N=64,128$.
Cơ chế resume sẽ bỏ qua chúng; dùng phase chạy lại dưới đây.

### Phase 2A - Chạy lại Gurobi với license mới

Chỉ chạy Gurobi tại $N=64,128$, cùng năm lần lặp và giới hạn 60 giây. Lưu
riêng để giữ nguyên dữ liệu cũ, sau đó gộp theo thứ tự ở Phase 4:

```python
!python benchmark.py \
  --phase standard --n-values 64 128 --methods ILP_Gurobi \
  --repetitions 5 --timeout 60 \
  --output-dir "{RESULT_ROOT}/gurobi_licensed_standard"

gurobi_new = pd.read_csv(f"{RESULT_ROOT}/gurobi_licensed_standard/benchmark_raw.csv")
display(pd.crosstab(gurobi_new["N"], gurobi_new["Status"]))
```

Nếu còn `LICENSE_LIMIT`, dừng trước Phase 3 và kiểm tra license file/tài khoản.
Không sửa CSV cũ bằng tay.

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
Mặc định loại Pairwise và Gurobi vì cả hai có thể tiêu thụ nhiều RAM ở kích
thước lớn. License WLS bỏ giới hạn kích thước mô hình, nhưng không tăng RAM.

```python
!python benchmark.py \
  --phase large \
  --output-dir "{RESULT_ROOT}/large"
```

Không thêm `--include-pairwise-large` trên Colab Free. Tùy chọn này chỉ dành
cho máy high-memory và có thể làm sập runtime.

Sau khi Phase 2A hoạt động, thử Gurobi riêng ở `N=256`:

```python
!python benchmark.py \
  --phase large \
  --n-values 256 \
  --methods ILP_Gurobi \
  --repetitions 3 \
  --timeout 120 \
  --output-dir "{RESULT_ROOT}/gurobi_licensed_large"
```

Chỉ thử `N=512` hoặc `N=1000` trên runtime nhiều RAM, từng kích thước một.
Mô hình MIP dùng $N^2$ biến nhị phân: tương ứng 262144 và 1000000 biến.
Không đưa file `gurobi.lic` lên GitHub.

## Phase 4 - Gộp dữ liệu và vẽ biểu đồ

Gộp các phase cũ trước, sau đó các run Gurobi mới. Khi trùng khóa
`(phase, N, method, run)`, kết quả mới thay thế `LICENSE_LIMIT` cũ trong bộ
tổng hợp; file raw cũ vẫn được giữ nguyên.

```python
import subprocess
from pathlib import Path

inputs = ["smoke", "standard", "cplex", "large"]
inputs += [name for name in ("gurobi_licensed_standard", "gurobi_licensed_large")
           if (Path(RESULT_ROOT) / name / "benchmark_raw.csv").is_file()]
subprocess.run(
    ["python", "combine_results.py",
     *(str(Path(RESULT_ROOT) / name) for name in inputs),
     "--output-dir", str(Path(RESULT_ROOT) / "combined")],
    check=True,
)
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

Sau khi có số liệu mới, chạy `prepare_report.py` và cập nhật các câu số liệu
trong `report/main.tex`, `README.md` và slide trước khi xuất bản bản nộp.
File PDF hiện tại vẫn mô tả dữ liệu 238 run cũ.
