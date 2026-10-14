# INT3011E_3 — N-Queens bằng SAT, CP và MIP

Bài tập lớn số 1 môn Các vấn đề hiện đại, lớp
[INT3011E_3](https://portal.uet.vnu.edu.vn/courses/7157), Trường Đại học
Công nghệ, Đại học Quốc gia Hà Nội.

| Thông tin | Giá trị |
|---|---|
| Sinh viên | Bùi Đình Cảnh |
| Mã sinh viên | 24021392 |
| Lớp học phần | INT3011E_3 |
| Email | buidinhcanh2006@gmail.com |
| Repository | <https://github.com/WilliamsBui-fnd/INT3011E_3> |

## Mục tiêu

Project mô hình hóa và giải bài toán N-Queens bằng nhiều phương pháp chính
xác, tập trung đánh giá ảnh hưởng của cách mã hóa ràng buộc At-Most-One
(AMO) đối với SAT. Mục tiêu là tìm một cấu hình hợp lệ hoặc chứng minh không
có nghiệm, không phải đếm toàn bộ nghiệm.

Các phương pháp đã triển khai:

- SAT bằng PySAT/Glucose3 với năm AMO encoding: Pairwise, Sequential,
  Commander, Product và Binary.
- Constraint Programming bằng OR-Tools CP-SAT.
- Integer/Mixed-Integer Programming bằng Gurobi MIP và CPLEX MIP.
- Constraint Programming bằng IBM CPLEX CP Optimizer.

## Cấu trúc project

```text
.
├── benchmark.py                 # Chạy benchmark theo phase, timeout và resume
├── combine_results.py           # Gộp dữ liệu từ các phase
├── plot_results.py              # Sinh bốn biểu đồ báo cáo
├── prepare_report.py            # Sinh bảng/hình cho báo cáo LaTeX
├── nqueens/
│   ├── sat_encoder.py           # Năm AMO encoding
│   ├── sat_solver.py            # PySAT/Glucose3
│   ├── cp_solver.py             # OR-Tools CP-SAT
│   ├── ilp_solver.py            # Gurobi MIP
│   ├── cplex_mip_solver.py      # CPLEX MIP
│   ├── cplex_cp_solver.py       # CPLEX CP Optimizer
│   └── utils.py                 # Chuyển đổi và kiểm tra nghiệm
├── tests/                       # Unit test và truth-table AMO
├── NQueens_BTL1_results/        # Dữ liệu thực nghiệm theo phase
│   ├── combined/                # Bộ dữ liệu trước khi cấp Academic WLS
│   └── combined_licensed/       # Bộ dữ liệu chuẩn dùng trong báo cáo cuối
├── report/                      # Báo cáo Elsevier cas-sc và tài liệu tham khảo
├── full_report_template.tex      # Entry point bản báo cáo đầy đủ
├── report_template.tex           # Entry point bản báo cáo ngắn
├── COLAB_GUIDE.md               # Hướng dẫn chạy từng phase trên Google Colab
└── PROJECT_STATUS.md            # Trạng thái hoàn thiện và hạn chế còn lại
```

## Cài đặt

Khuyến nghị dùng Google Colab vì các phase lớn cần nhiều CPU/RAM và một số
solver thương mại cần license riêng.

```bash
git clone https://github.com/WilliamsBui-fnd/INT3011E_3.git
cd INT3011E_3
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
```

Xem quy trình Colab đầy đủ tại [COLAB_GUIDE.md](COLAB_GUIDE.md).

## Chạy benchmark

Benchmark được chia thành các phase và ghi checkpoint sau từng run. Nếu Colab
bị ngắt, chạy lại đúng lệnh cũ để tiếp tục.

```bash
python3 benchmark.py --phase smoke
python3 benchmark.py --phase standard
python3 benchmark.py --phase cplex
python3 benchmark.py --phase large
```

Các trạng thái quan trọng:

- `SAT`, `UNSAT`: solver kết thúc bình thường.
- `TIMEOUT`: vượt giới hạn thời gian.
- `LICENSE_LIMIT`: mô hình vượt giới hạn license Gurobi/CPLEX.
- `UNAVAILABLE`: thiếu thư viện hoặc executable của solver.
- `KILLED`: process nhận SIGKILL; không tự suy diễn thành OOM nếu thiếu log.
- `INVALID_SOLUTION`: nghiệm trả về không qua bộ kiểm tra độc lập.

`benchmark_raw.csv` là dữ liệu cấp run. `benchmark_results.csv` chứa trung vị,
min/max, tỷ lệ thành công và số lần theo từng trạng thái. Số đo thiếu được để
trống, không thay bằng 0.

## Kết quả thực nghiệm

Bộ dữ liệu chuẩn tại `NQueens_BTL1_results/combined_licensed` gồm 241 lượt chạy:

| Trạng thái | Số lượt |
|---|---:|
| SAT | 182 |
| UNSAT | 14 |
| TIMEOUT | 39 |
| LICENSE_LIMIT | 3 |
| KILLED | 3 |

- Tất cả 182 nghiệm SAT đều vượt qua bộ kiểm tra N-Queens độc lập.
- Các kết quả UNSAT đều thuộc `N=2` và `N=3`.
- Product là SAT encoding duy nhất hoàn thành cả ba run tại `N=1000`, trung
  vị 28.127 giây trong môi trường đã đo.
- Với Academic WLS, Gurobi hoàn thành 5/5 lượt tại `N=64,128` và 3/3 lượt
  tại `N=256`. Trung vị lần lượt là 0.098, 0.194 và 3.078 giây. Bộ dữ liệu
  gộp thay thế các lượt `LICENSE_LIMIT` cũ bằng kết quả đo lại, giữ nguyên
  dữ liệu gốc trước khi cấp license trong `combined`.
- CPLEX CP Optimizer hoàn thành `N=8,16,32`; CPLEX MIP gặp license limit tại
  `N=32` (ba lượt). Academic WLS của Gurobi không cấp phép cho CPLEX.

Không suy rộng các kết quả trên thành thứ hạng tuyệt đối giữa solver: Colab là
môi trường chia sẻ, các lượt Gurobi bổ sung được đo trong phiên Colab khác,
số lần lặp khác nhau giữa phase và các run timeout không trả lại thống kê mô
hình.

## Tái tạo bảng và biểu đồ

File raw và bảng tổng hợp của bộ dữ liệu cuối đã được lưu tại
`NQueens_BTL1_results/combined_licensed`. Vì gói kết quả chuyển về máy chỉ
chứa CSV gộp cùng metadata của hai phase Gurobi mới, không cần chạy lại bước
gộp để tái tạo hình và bảng. Nếu muốn gộp lại từ các phase riêng, hãy dùng
những thư mục phase gốc còn lưu trên Drive theo [COLAB_GUIDE.md](COLAB_GUIDE.md).

```bash
python3 plot_results.py \
  --input NQueens_BTL1_results/combined_licensed/benchmark_results.csv \
  --raw NQueens_BTL1_results/combined_licensed/benchmark_raw.csv \
  --output-dir NQueens_BTL1_results/combined_licensed

python3 prepare_report.py
```

Bốn hình đầu ra là `plot_time.png`, `plot_status.png`, `plot_variables.png`
và `plot_clauses.png`.

## Báo cáo và thuyết trình

- Báo cáo nguồn chung: `report/main.tex`; nội dung mở rộng ở `report/full/`.
- PDF đầy đủ, khuyến nghị nộp:
  `report/INT3011E_3_24021392_BuiDinhCanh_Full.pdf` (14 trang).
- PDF ngắn để tham khảo:
  `report/INT3011E_3_24021392_BuiDinhCanh.pdf` (8 trang).
- Slide bổ trợ: `BaiGiang_NQueens_ChiTiet.pdf`.

Báo cáo dùng lớp Elsevier `cas-sc` và cần biên dịch bằng XeLaTeX. Từ thư mục
gốc, dùng `full_report_template.tex` cho bản đầy đủ hoặc
`report_template.tex` cho bản ngắn; chạy BibTeX rồi biên dịch lại để cập nhật
tài liệu tham khảo. Cả hai PDF và slide đều dựa trên bộ dữ liệu 241 lượt đã
gộp kết quả Gurobi Academic WLS. Chỉ nộp một PDF báo cáo; bản đầy đủ là lựa
chọn phù hợp hơn nếu thầy muốn bài viết tương tự mẫu nghiên cứu.

## License thương mại và bảo mật

Project không kèm license Gurobi hoặc CPLEX. Trên máy local, Gurobi solver tự
dùng `gurobi.lic` ở thư mục gốc project nếu file tồn tại; `GRB_LICENSE_FILE`
được đặt sẵn sẽ luôn được ưu tiên. Trên Colab, đặt license trong Drive riêng
tư rồi làm theo [Phase 0.3](COLAB_GUIDE.md). Không ghi nội dung license vào
mã nguồn, notebook, CSV, log hoặc Git. `.gitignore` chặn mọi file `*.lic`;
kiểm tra trước khi commit bằng `git status --short` và
`git check-ignore -v gurobi.lic`. File local nên có quyền `600`.

Chỉ file license được thay đổi; điều này không mở khóa CPLEX MIP/CP Optimizer,
vì chúng dùng hệ thống cấp phép riêng của IBM.

## Kiểm thử

```bash
python3 -m unittest discover -s tests -v
python3 test_phase2.py
python3 test_phase3.py
```

Các test CPLEX có thể được skip trên máy không cài CPLEX/CP Optimizer; đây là
kiểm tra dependency chứ không phải che giấu lỗi test.

