# Trạng thái project INT3011E_3

## Thông tin sinh viên

- Họ tên: Bùi Đình Cảnh
- Mã sinh viên: 24021392
- Lớp học phần: INT3011E_3
- Email: buidinhcanh2006@gmail.com
- GitHub: <https://github.com/WilliamsBui-fnd/INT3011E_3>

## Đã hoàn thành

- Đủ năm SAT encoding: Pairwise, Sequential, Commander, Product và Binary.
- Đủ bốn mô hình đối chứng: OR-Tools CP-SAT, Gurobi MIP, CPLEX MIP và CPLEX
  CP Optimizer.
- Benchmark có timeout process, checkpoint/resume, kiểm tra nghiệm và phân
  loại riêng timeout, license limit, unavailable, killed và invalid solution.
- Bộ dữ liệu gộp 238 run; toàn bộ 169 nghiệm SAT đều hợp lệ.
- Bốn biểu đồ và các bảng báo cáo tái tạo được từ CSV.
- Báo cáo khoa học `cas-sc` và slide thuyết trình đã điền đầy đủ thông tin tác
  giả, mã sinh viên, lớp, email và URL repository.
- Unit test: 11 bài chạy được đều pass; 2 test CPLEX skip trên máy local vì
  không cài CPLEX/CP Optimizer. Dữ liệu Colab đã xác nhận hai solver CPLEX.

## License Gurobi mới và việc cần làm

- Academic WLS đã được đặt ở file `gurobi.lic` local, quyền truy cập `600`;
  file này bị Git bỏ qua. Solver tự phát hiện file local; Colab dùng
  `GRB_LICENSE_FILE` theo `COLAB_GUIDE.md`.
- Đã kiểm chứng local bằng mô hình `N=46` (2116 biến): Gurobi trả về SAT và
  nghiệm hợp lệ; benchmark chạy trong process con cũng trả về SAT.
- Bộ dữ liệu 238 run, báo cáo PDF và slide hiện vẫn là kết quả **trước khi**
  có WLS. Chạy lại riêng Gurobi ở `N=64,128`, sau đó cân nhắc `N=256`; gộp
  dữ liệu mới và cập nhật văn bản, hình, bảng trước khi nộp.
- License Gurobi không thay đổi giới hạn license của CPLEX.

## Hạn chế của bộ dữ liệu hiện tại

- Trong bộ dữ liệu cũ, `N=64,128` của Gurobi là `LICENSE_LIMIT`; không dùng
  nhãn đó để mô tả license WLS hiện tại trước khi đo lại.
- Metadata cũ không lưu model CPU và tổng RAM; không tự điền số ước lượng.
- Ba run Commander tại `N=1000` nhận SIGKILL, chưa có log để khẳng định OOM.
- Glucose3 không nhận seed từ script; các lần lặp SAT đo dao động thời gian,
  không phải các lần tìm kiếm ngẫu nhiên độc lập.

## File chuẩn

- Dữ liệu raw: `NQueens_BTL1_results/combined/benchmark_raw.csv`
- Bảng tổng hợp: `NQueens_BTL1_results/combined/benchmark_results.csv`
- Báo cáo: `report/INT3011E_3_24021392_BuiDinhCanh.pdf`
- Slide: `BaiGiang_NQueens_ChiTiet.pdf`
- Hướng dẫn chạy: `COLAB_GUIDE.md`

