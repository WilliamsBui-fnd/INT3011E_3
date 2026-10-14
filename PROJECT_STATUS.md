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
- Bộ dữ liệu gộp 241 run; toàn bộ 182 nghiệm SAT đều hợp lệ.
- Bốn biểu đồ và các bảng báo cáo tái tạo được từ CSV.
- Hai bản báo cáo khoa học `cas-sc`: bản đầy đủ 14 trang và bản ngắn 8 trang;
  slide thuyết trình và cả hai báo cáo đều có thông tin tác giả, mã sinh viên,
  lớp, email và URL repository.
- Unit test: 11 bài chạy được đều pass; 2 test CPLEX skip trên máy local vì
  không cài CPLEX/CP Optimizer. Dữ liệu Colab đã xác nhận hai solver CPLEX.

## License Gurobi và kết quả đo lại

- Academic WLS đã được đặt ở file `gurobi.lic` local, quyền truy cập `600`;
  file này bị Git bỏ qua. Solver tự phát hiện file local; Colab dùng
  `GRB_LICENSE_FILE` theo `COLAB_GUIDE.md`.
- Đã kiểm chứng local bằng mô hình `N=46` (2116 biến): Gurobi trả về SAT và
  nghiệm hợp lệ; benchmark chạy trong process con cũng trả về SAT.
- Đã chạy lại Gurobi Academic WLS: `N=64,128` có 5/5 lượt SAT hợp lệ,
  `N=256` có 3/3 lượt SAT hợp lệ. Trung vị lần lượt là 0.098, 0.194 và
  3.078 giây. Bộ dữ liệu gộp, báo cáo PDF và slide đã cập nhật.
- License Gurobi không thay đổi giới hạn license của CPLEX.

## Hạn chế của bộ dữ liệu hiện tại

- Ba lượt `LICENSE_LIMIT` còn lại thuộc CPLEX MIP tại `N=32`, không thuộc
  Gurobi. Gurobi và các phương pháp khác được đo ở hai phiên Colab khác nhau,
  do đó chỉ so sánh thời gian với lưu ý về môi trường.
- Metadata cũ không lưu model CPU và tổng RAM; metadata phiên Gurobi mới ghi
  2 CPU logic và khoảng 12.67 GiB RAM nhưng không có model CPU chi tiết.
- Ba run Commander tại `N=1000` nhận SIGKILL, chưa có log để khẳng định OOM.
- Glucose3 không nhận seed từ script; các lần lặp SAT đo dao động thời gian,
  không phải các lần tìm kiếm ngẫu nhiên độc lập.

## File chuẩn

- Dữ liệu raw: `NQueens_BTL1_results/combined_licensed/benchmark_raw.csv`
- Bảng tổng hợp: `NQueens_BTL1_results/combined_licensed/benchmark_results.csv`
- Báo cáo đầy đủ, khuyến nghị nộp:
  `report/INT3011E_3_24021392_BuiDinhCanh_Full.pdf`
- Báo cáo ngắn: `report/INT3011E_3_24021392_BuiDinhCanh.pdf`
- Slide: `BaiGiang_NQueens_ChiTiet.pdf`
- Hướng dẫn chạy: `COLAB_GUIDE.md`

