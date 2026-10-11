import os
import math
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Register Vietnamese-compatible TrueType Font from macOS system fonts
FONT_REGULAR = 'Arial'
FONT_BOLD = 'Arial-Bold'
FONT_ITALIC = 'Arial-Italic'

pdfmetrics.registerFont(TTFont(FONT_REGULAR, '/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont(FONT_BOLD, '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
pdfmetrics.registerFont(TTFont(FONT_ITALIC, '/System/Library/Fonts/Supplemental/Arial Italic.ttf'))

# Page geometry (Landscape Letter: 11 x 8.5 inches = 792 x 612 pt)
PAGE_WIDTH, PAGE_HEIGHT = landscape(letter)

# Color Palette
COLOR_BG = colors.HexColor('#F8FAFC')
COLOR_HEADER = colors.HexColor('#0F172A') # Dark Slate
COLOR_PRIMARY = colors.HexColor('#1E3A8A') # Royal Navy
COLOR_SECONDARY = colors.HexColor('#2563EB') # Bright Blue
COLOR_ACCENT = colors.HexColor('#059669') # Emerald Green
COLOR_WARN = colors.HexColor('#D97706') # Amber
COLOR_DANGER = colors.HexColor('#DC2626') # Red
COLOR_CARD_BG = colors.HexColor('#FFFFFF')
COLOR_BORDER = colors.HexColor('#E2E8F0')
COLOR_TEXT = colors.HexColor('#1E293B')
COLOR_MUTED = colors.HexColor('#64748B')

def draw_slide_decorations(canvas, doc):
    canvas.saveState()
    # Top banner background
    canvas.setFillColor(COLOR_HEADER)
    canvas.rect(0, PAGE_HEIGHT - 54, PAGE_WIDTH, 54, fill=True, stroke=False)
    
    # Gold decorative accent line under header banner
    canvas.setFillColor(COLOR_SECONDARY)
    canvas.rect(0, PAGE_HEIGHT - 58, PAGE_WIDTH, 4, fill=True, stroke=False)
    
    # Bottom footer background
    canvas.setFillColor(colors.HexColor('#F1F5F9'))
    canvas.rect(0, 0, PAGE_WIDTH, 28, fill=True, stroke=False)
    
    # Footer text
    canvas.setFont(FONT_REGULAR, 9)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawString(36, 10, "Bài giảng BTL: N-Queens Problem (SAT, CP, ILP)")
    canvas.drawRightString(PAGE_WIDTH - 36, 10, f"Trang {doc.page}")
    canvas.restoreState()

def create_slide_deck():
    project_dir = Path(__file__).resolve().parent
    result_dir = project_dir / "NQueens_BTL1_results" / "combined"
    pdf_filename = str(project_dir / "BaiGiang_NQueens_ChiTiet.pdf")
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=70,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_slide_title = ParagraphStyle(
        'SlideTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=24,
        textColor=COLOR_PRIMARY,
        spaceAfter=0
    )

    style_main_title = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=28,
        leading=34,
        textColor=COLOR_PRIMARY,
        alignment=1, # Centered
        spaceAfter=15
    )

    style_subtitle = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=15,
        leading=20,
        textColor=COLOR_SECONDARY,
        alignment=1,
        spaceAfter=25
    )

    style_h2 = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=COLOR_PRIMARY,
        spaceBefore=8,
        spaceAfter=6
    )

    style_body = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=11,
        leading=16,
        textColor=COLOR_TEXT,
        spaceAfter=6
    )

    style_bullet = ParagraphStyle(
        'BulletText',
        parent=style_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    style_code = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        # Arial giữ được dấu tiếng Việt; Courier dựng sẵn của ReportLab không giữ được.
        fontName=FONT_REGULAR,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F1F5F9'),
        borderColor=COLOR_BORDER,
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )

    style_box_header = ParagraphStyle(
        'BoxHeader',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=15,
        textColor=COLOR_PRIMARY,
        spaceAfter=4
    )

    story = []

    def make_header(title_text):
        return Paragraph(f"<b>{title_text}</b>", style_slide_title)

    # -------------------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------------------
    story.append(make_header("BÀI GIẢNG CHI TIẾT & ĐẦY ĐỦ: BÀI TOÁN N-QUEENS"))
    story.append(Spacer(1, 20))
    story.append(Paragraph("DỰ ÁN NGHIÊN CỨU & SO SÁNH 3 PHƯƠNG PHÁP AI/TỐI ƯU HÓA", style_subtitle))
    story.append(Spacer(1, 10))

    intro_html = """
    <para align="center">
    <b>Chủ đề:</b> Mã hóa SAT (5 Thuật toán AMO), Constraint Programming (CP) và Integer Linear Programming (ILP)<br/><br/>
    <b>Đối tượng:</b> Giảng dạy từ con số 0 dành cho sinh viên / thành viên nhóm chưa có nền tảng.<br/>
    <b>Nội dung:</b> Lý thuyết cốt lõi, Ví dụ trực quan bàn cờ, Công thức toán, Mã nguồn & Phân tích Đồ thị Benchmark.
    </para>
    """
    intro_table = Table([[Paragraph(intro_html, style_body)]], colWidths=[680])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1.5, COLOR_SECONDARY),
        ('PADDING', (0,0), (-1,-1), 18),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 25))

    meta_html = """
    <para align="center">
    <b>Sinh viên:</b> Bùi Đình Cảnh &nbsp;&nbsp; <b>MSSV:</b> 24021392 &nbsp;&nbsp; <b>Lớp:</b> INT3011E_3<br/>
    <b>Email:</b> buidinhcanh2006@gmail.com<br/><br/>
    <b>Bộ giải sử dụng:</b> PySAT/Glucose3, OR-Tools CP-SAT, Gurobi MIP, CPLEX MIP và CPLEX CP Optimizer<br/>
    <b>Môi trường thực nghiệm:</b> Google Colab (2 CPU logic; timeout 15/60/120 giây tùy phase; RAM không được lưu trong metadata)
    </para>
    """
    story.append(Paragraph(meta_html, style_body))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 2: Tổng quan bài toán N-Queens
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 1: GIỚI THIỆU BÀI TOÁN N-QUEENS"))
    story.append(Spacer(1, 10))

    col1_content = [
        Paragraph("<b>1. Khái niệm Bài toán:</b>", style_h2),
        Paragraph("• Đặt <b>N quân Hậu</b> lên bàn cờ kích thước <b>N × N</b>.", style_bullet),
        Paragraph("• Quy tắc quân Hậu: Có thể di chuyển ngang, dọc và chéo không giới hạn ô.", style_bullet),
        Paragraph("• <b>Mục tiêu:</b> Không có 2 quân Hậu nào khống chế lẫn nhau.", style_bullet),
        Spacer(1, 8),
        Paragraph("<b>2. Ba ràng buộc cốt lõi:</b>", style_h2),
        Paragraph("<b>1. Ràng buộc Hàng:</b> Mỗi hàng có đúng 1 quân Hậu.", style_bullet),
        Paragraph("<b>2. Ràng buộc Cột:</b> Mỗi cột có đúng 1 quân Hậu.", style_bullet),
        Paragraph("<b>3. Ràng buộc Đường chéo:</b> Tối đa 1 quân Hậu trên mỗi đường chéo chính và phụ.", style_bullet),
    ]

    ascii_board = """
    BÀN CỜ 4x4 (N=4) VỚI LỜI GIẢI HỢP LỆ:
    +---+---+---+---+
 0  | . | Q | . | . |   -> Hậu tại ô (0, 1)
    +---+---+---+---+
 1  | . | . | . | Q |   -> Hậu tại ô (1, 3)
    +---+---+---+---+
 2  | Q | . | . | . |   -> Hậu tại ô (2, 0)
    +---+---+---+---+
 3  | . | . | Q | . |   -> Hậu tại ô (3, 2)
    +---+---+---+---+
      0   1   2   3
    """
    col2_content = [
        Paragraph("<b>Minh họa Bàn cờ 4 × 4:</b>", style_h2),
        Paragraph(ascii_board.replace('\n', '<br/>').replace(' ', '&nbsp;'), style_code),
        Paragraph("<b>Kiểm tra:</b> Không có 2 quân Hậu nào nằm chung Hàng, Cột hoặc Đường chéo!", style_body)
    ]

    t2 = Table([[col1_content, col2_content]], colWidths=[350, 360])
    t2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (0,0), 1, COLOR_BORDER),
        ('BOX', (1,0), (1,0), 1, COLOR_BORDER),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t2)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 3: Khung tư duy 3 Phương pháp
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 2: BỨC TRANH TỔNG QUAN 3 PHƯƠNG PHÁP GIẢI"))
    story.append(Spacer(1, 10))

    table_data = [
        [
            Paragraph("<b>Tiêu chí</b>", style_box_header),
            Paragraph("<b>1. SAT (Glucose3)</b>", style_box_header),
            Paragraph("<b>2. CP (OR-Tools)</b>", style_box_header),
            Paragraph("<b>3. ILP (Gurobi)</b>", style_box_header)
        ],
        [
            Paragraph("<b>Biểu diễn Biến</b>", style_body),
            Paragraph("Biến Mệnh đề Nhị phân<br/>x<sub>r,c</sub> nhận True hoặc False", style_body),
            Paragraph("Biến Vị trí Cột Nguyên<br/>Q<sub>i</sub> nhận 0 .. N-1", style_body),
            Paragraph("Ma trận Biến 0-1<br/>x<sub>r,c</sub> nhận 0 hoặc 1", style_body)
        ],
        [
            Paragraph("<b>Dạng Ràng buộc</b>", style_body),
            Paragraph("Các mệnh đề CNF (AND của các OR): ALO & AMO", style_body),
            Paragraph("Ràng buộc toàn cục (Global Constraint): <code>AllDifferent</code>", style_body),
            Paragraph("Hệ Phương trình & Bất phương trình Đại số Tuyến tính", style_body)
        ],
        [
            Paragraph("<b>Ưu điểm Cốt lõi</b>", style_body),
            Paragraph("Thuật toán CDCL cực mạnh cho bài toán logic quy mô", style_body),
            Paragraph("Mã nguồn ngắn gọn (chỉ 3 dòng toán), lan truyền ràng buộc tốt", style_body),
            Paragraph("Thuật toán Simplex & Branch-and-Bound tối ưu toán học", style_body)
        ],
        [
            Paragraph("<b>Thử thách</b>", style_body),
            Paragraph("Bùng nổ số lượng mệnh đề nếu chọn mã hóa kém", style_body),
            Paragraph("Bùng nổ không gian tìm kiếm khi N lớn", style_body),
            Paragraph("Bản quyền thương mại giới hạn kích thước biến", style_body)
        ]
    ]

    t3 = Table(table_data, colWidths=[120, 195, 195, 195])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, COLOR_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#F8FAFC')),
    ]))
    story.append(t3)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Quy trình xử lý chung:</b> Bài toán N-Queens -> Chuyển đổi mô hình (Encoding) -> Bộ giải (Solver) -> Trích xuất nghiệm bàn cờ.", style_body))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 4: Chi tiết SAT - CNF, ALO & AMO
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 3: CỐT LÕI CỦA SAT SOLVER VÀ CHUẨN CNF"))
    story.append(Spacer(1, 10))

    sat_info = [
        Paragraph("<b>1. Dạng chuẩn CNF (Conjunctive Normal Form):</b>", style_h2),
        Paragraph("• Mọi bài toán SAT được phát biểu dưới dạng <b>Tích của các Tổng (AND của các OR)</b>.", style_bullet),
        Paragraph("• Cấu trúc: C<sub>1</sub> AND C<sub>2</sub> AND ... AND C<sub>m</sub> (mỗi C<sub>i</sub> là một <b>clause / mệnh đề</b>).", style_bullet),
        Paragraph("• Mỗi ô (r, c) trên bàn cờ tương ứng 1 biến nhị phân: <b>x<sub>r,c</sub> = 1 (True)</b> nếu có Hậu, ngược lại <b>0 (False)</b>.", style_bullet),
        Spacer(1, 8),
        Paragraph("<b>2. Hai loại Ràng buộc Logic bắt buộc:</b>", style_h2),
        Paragraph("<b>A. ALO (At-Least-One - Tối thiểu 1):</b> Ít nhất 1 ô trong hàng có Hậu.", style_bullet),
        Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;=> Mệnh đề CNF cho hàng r: <b>(x<sub>r,0</sub> OR x<sub>r,1</sub> OR ... OR x<sub>r,N-1</sub>)</b>", style_body),
        Paragraph("<b>B. AMO (At-Most-One - Tối đa 1):</b> Nhiều nhất 1 ô có Hậu trên mỗi hàng/cột/đường chéo.", style_bullet),
        Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;=> Đảm bảo không có 2 quân Hậu nào khống chế nhau. Có 5 cách mã hóa AMO khác nhau!", style_body)
    ]

    sat_table = Table([[sat_info]], colWidths=[710])
    sat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (-1,-1), 1, COLOR_SECONDARY),
        ('PADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(sat_table)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 5: 5 Thuật toán Mã hóa AMO
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 4: CHI TIẾT 5 THUẬT TOÁN MÃ HÓA AT-MOST-ONE (AMO)"))
    story.append(Spacer(1, 6))

    amo_data = [
        [Paragraph("<b>Thuật toán AMO</b>", style_box_header), Paragraph("<b>Cách hoạt động & Ý tưởng</b>", style_box_header), Paragraph("<b>Độ phức tạp</b>", style_box_header), Paragraph("<b>Đánh giá Thực nghiệm</b>", style_box_header)],
        [
            Paragraph("<b>1. Pairwise</b><br/>(Cặp đôi)", style_body),
            Paragraph("Xét mọi cặp ô (i, j). Mệnh đề: <b>(NOT x<sub>i</sub> OR NOT x<sub>j</sub>)</b>.", style_body),
            Paragraph("Biến phụ: 0<br/>Mệnh đề: <b>O(N<sup>2</sup>)</b>", style_body),
            Paragraph("Số clause tăng nhanh; không chạy ở phase large để tránh chi phí dự kiến quá lớn.", style_body)
        ],
        [
            Paragraph("<b>2. Sequential</b><br/>(Nối tiếp)", style_body),
            Paragraph("Dùng chuỗi biến phụ s<sub>i</sub> để 'đếm tích lũy' xem từ ô 1 đến i đã có Hậu xuất hiện chưa.", style_body),
            Paragraph("Biến phụ: O(N)<br/>Mệnh đề: <b>O(N)</b>", style_body),
            Paragraph("Nhanh nhất ở N=16, chậm rõ rệt tại N=64 và timeout từ N=128 trong bộ dữ liệu này.", style_body)
        ],
        [
            Paragraph("<b>3. Commander</b><br/>(Chỉ huy)", style_body),
            Paragraph("Chia N ô thành các nhóm nhỏ. Mỗi nhóm tạo 1 'Biến chỉ huy' c<sub>g</sub> đại diện.", style_body),
            Paragraph("Biến phụ: O(N)<br/>Mệnh đề: <b>O(N)</b>", style_body),
            Paragraph("Hoàn thành đến N=512; ba run N=1000 nhận SIGKILL, chưa đủ log để kết luận OOM.", style_body)
        ],
        [
            Paragraph("<b>4. Product</b><br/>(Tích 2D)", style_body),
            Paragraph("Mã hóa vị trí ô bằng giao điểm hàng phụ r<sub>i</sub> và cột phụ c<sub>j</sub> trong lưới 2D (p x q).", style_body),
            Paragraph("Biến phụ: O(sqrt(N))<br/>Mệnh đề: <b>O(sqrt(N))</b>", style_body),
            Paragraph("Timeout ở N=32,64 nhưng hoàn thành cả ba run ở N=1000.", style_body)
        ],
        [
            Paragraph("<b>5. Binary</b><br/>(Nhị phân)", style_body),
            Paragraph("Dùng ceil(log<sub>2</sub> N) bit nhị phân để mã hóa chỉ số vị trí ô chứa quân Hậu.", style_body),
            Paragraph("Biến phụ: <b>O(log N)</b><br/>Mệnh đề: O(N log N)", style_body),
            Paragraph("Hoàn thành N=128, 256, 512 nhưng timeout tại N=64 và N=1000.", style_body)
        ]
    ]

    t_amo = Table(amo_data, colWidths=[110, 290, 110, 200])
    t_amo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_HEADER),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, COLOR_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#FFFFFF')),
    ]))
    story.append(t_amo)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 6: Constraint Programming (CP)
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 5: LẬP TRÌNH RÀNG BUỘC (CP VỚI OR-TOOLS)"))
    story.append(Spacer(1, 10))

    cp_content = [
        Paragraph("<b>1. Tư duy Biểu diễn Biến trong CP:</b>", style_h2),
        Paragraph("• Thay vì dùng N x N biến nhị phân như SAT, CP sử dụng <b>N biến số nguyên</b>.", style_bullet),
        Paragraph("• Đặt <b>Q<sub>i</sub> nhận giá trị 0, 1, ..., N-1</b> là vị trí cột của quân Hậu ở hàng i.", style_bullet),
        Paragraph("• Miền giá trị (Domain): Mỗi biến Q<sub>i</sub> có N giá trị có thể nhận.", style_bullet),
        Spacer(1, 10),
        Paragraph("<b>2. Mã nguồn 3 dòng Toán gọn nhẹ trong Python:</b>", style_h2),
        Paragraph("""
from ortools.sat.python import cp_model<br/>
model = cp_model.CpModel()<br/>
Q = [model.NewIntVar(0, n - 1, f'Q_{i}') for i in range(n)]<br/><br/>
# Ràng buộc 1: Không trùng Cột<br/>
<b>model.AddAllDifferent(Q)</b><br/><br/>
# Ràng buộc 2: Không trùng Đường chéo chính<br/>
<b>model.AddAllDifferent([Q[i] + i for i in range(n)])</b><br/><br/>
# Ràng buộc 3: Không trùng Đường chéo phụ<br/>
<b>model.AddAllDifferent([Q[i] - i for i in range(n)])</b>
        """, style_code),
        Paragraph("<b>Đánh giá:</b> Mô hình rất gọn. OR-Tools hoàn thành 2/3 run tại N=256 với timeout 120 giây, rồi timeout ở N=512 và N=1000.", style_body)
    ]

    t_cp = Table([[cp_content]], colWidths=[710])
    t_cp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (-1,-1), 1, COLOR_SECONDARY),
        ('PADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(t_cp)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 7: Integer Linear Programming (ILP)
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 6: QUY HOẠCH TUYẾN TÍNH NGUYÊN (ILP VỚI GUROBI)"))
    story.append(Spacer(1, 10))

    ilp_content = [
        Paragraph("<b>1. Biểu diễn Bài toán thành Hệ Bất Phương Trình Đại Số:</b>", style_h2),
        Paragraph("• Sử dụng ma trận biến nhị phân <b>x<sub>r,c</sub> nhận 0 hoặc 1</b>.", style_bullet),
        Paragraph("• <b>Tổng theo hàng = 1:</b> sum(x<sub>r,c</sub>, c=0..N-1) = 1 với mọi r.", style_bullet),
        Paragraph("• <b>Tổng theo cột = 1:</b> sum(x<sub>r,c</sub>, r=0..N-1) = 1 với mọi c.", style_bullet),
        Paragraph("• <b>Đường chéo chính &lt;= 1:</b> sum(x<sub>r,c</sub>, r-c=k) &lt;= 1 với mọi k.", style_bullet),
        Paragraph("• <b>Đường chéo phụ &lt;= 1:</b> sum(x<sub>r,c</sub>, r+c=k) &lt;= 1 với mọi k.", style_bullet),
        Spacer(1, 10),
        Paragraph("<b>2. Bộ giải Gurobi & Lỗi Hạn chế Giấy phép (License Limit):</b>", style_h2),
        Paragraph("• Gurobi là bộ giải ILP thương mại hàng đầu thế giới.", style_bullet),
        Paragraph("• <b>Hiện tượng LIMIT tại N &gt;= 64:</b> license hiện dùng giới hạn tối đa <b>2000 biến</b>. Ở N=64 có 64 x 64 = 4096 biến nhị phân nên bộ giải từ chối chạy.", style_bullet)
    ]

    t_ilp = Table([[ilp_content]], colWidths=[710])
    t_ilp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (-1,-1), 1, COLOR_WARN),
        ('PADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(t_ilp)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 8: Kết quả Benchmark & Biểu đồ Thời gian
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 7: KẾT QUẢ BENCHMARK THỜI GIAN CHẠY (SEC)"))
    story.append(Spacer(1, 6))

    img_time_path = str(result_dir / "plot_time.png")
    
    b_data = [
        ["N", "Pairwise", "Sequential", "Commander", "Product", "Binary", "CP (OR-Tools)", "ILP (Gurobi)"],
        ["4", "0.000s", "0.000s", "0.001s", "0.000s", "0.000s", "0.004s", "0.002s"],
        ["8", "0.001s", "0.003s", "0.002s", "0.001s", "0.001s", "0.006s", "0.003s"],
        ["16", "0.015s", "0.008s", "0.151s", "0.397s", "0.129s", "0.015s", "0.010s"],
        ["32", "0.036s", "0.288s", "0.045s", "TIMEOUT", "9.090s", "0.058s", "0.010s"],
        ["64", "0.322s", "18.143s", "0.998s", "TIMEOUT", "TIMEOUT", "0.311s", "LICENSE"],
        ["128", "3.063s", "TIMEOUT", "1.153s", "0.719s", "0.908s", "1.944s", "LICENSE"],
        ["256", "—", "TIMEOUT", "8.309s", "2.704s", "3.147s", "41.473s (2/3)", "—"],
        ["512", "—", "TIMEOUT", "16.003s", "14.004s", "13.158s", "TIMEOUT", "—"],
        ["1000", "—", "TIMEOUT", "KILLED", "28.127s", "TIMEOUT", "TIMEOUT", "—"],
    ]

    t_b = Table(b_data, colWidths=[40, 65, 75, 75, 75, 65, 95, 80])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_HEADER),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#FFFFFF')),
    ]))

    if os.path.exists(img_time_path):
        img_time = Image(img_time_path, width=320, height=230)
        t_slide7 = Table([[t_b, img_time]], colWidths=[380, 330])
        t_slide7.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_slide7)
    else:
        story.append(t_b)

    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 9: Biểu đồ Số Biến & Số Mệnh Đề
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 8: PHÂN TÍCH SỐ LƯỢNG BIẾN VÀ MỆNH ĐỀ SAT"))
    story.append(Spacer(1, 6))

    img_vars_path = str(result_dir / "plot_variables.png")
    img_clauses_path = str(result_dir / "plot_clauses.png")

    imgs = []
    if os.path.exists(img_vars_path):
        imgs.append(Image(img_vars_path, width=340, height=230))
    if os.path.exists(img_clauses_path):
        imgs.append(Image(img_clauses_path, width=340, height=230))

    if len(imgs) == 2:
        t_imgs = Table([[imgs[0], imgs[1]]], colWidths=[355, 355])
        t_imgs.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_imgs)
    
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Nhận xét đồ thị:</b> Pairwise không dùng biến phụ nhưng số clause tăng nhanh. Product dùng nhiều biến phụ hơn, song là encoding duy nhất hoàn thành cả ba run tại N=1000. Run timeout/killed không trả về quy mô encoding nên đường biểu diễn dừng tại điểm thiếu.", style_body))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 10: 3 Hiện tượng Kỹ thuật Đặc biệt
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 9: GIẢI THÍCH 3 HIỆN TƯỢNG KỸ THUẬT ĐẶC BIỆT"))
    story.append(Spacer(1, 10))

    phenom_content = [
        Paragraph("<b>1. Sập Giấy phép Gurobi ILP (License Limit):</b>", style_h2),
        Paragraph("• Gurobi báo lỗi ngắt phép tính ngay lập tức khi N ≥ 64 do vượt ngưỡng <b>2000 biến nhị phân</b> của bản miễn phí.", style_bullet),
        Spacer(1, 8),
        Paragraph("<b>2. Commander bị hệ điều hành dừng tại N=1000:</b>", style_bullet),
        Paragraph("• Ba run có exit code -9 (SIGKILL). Không có log kernel nên chỉ gắn nhãn KILLED, không khẳng định nguyên nhân là hết RAM.", style_bullet),
        Spacer(1, 8),
        Paragraph("<b>3. Hiện tượng 'Đuôi Nặng' (Heavy-Tailed Phenomenon) của Product SAT:</b>", style_h2),
        Paragraph("• Product timeout ở N=32,64 nhưng hoàn thành 3/3 run tại N=1000 với trung vị 28.127 giây.", style_bullet),
        Paragraph("• <b>Diễn giải thận trọng:</b> thời gian CDCL phụ thuộc cấu trúc encoding và heuristic, nên độ khó không nhất thiết tăng đơn điệu theo N. Dữ liệu hiện có không đủ để khẳng định một cơ chế nhân quả cụ thể.", style_bullet)
    ]

    t_ph = Table([[phenom_content]], colWidths=[710])
    t_ph.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
        ('BOX', (0,0), (-1,-1), 1, COLOR_PRIMARY),
        ('PADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(t_ph)
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SLIDE 11: Bí quyết Bảo vệ Bài tập lớn
    # -------------------------------------------------------------------------
    story.append(make_header("SLIDE 10: TỔNG KẾT VÀ CÂU HỎI PHẢN BIỆN HỘI ĐỒNG"))
    story.append(Spacer(1, 10))

    qa_content = [
        Paragraph("<b>1. Tổng kết Phương pháp Tốt nhất:</b>", style_h2),
        Paragraph("• <b>Không có phương pháp thắng ở mọi N:</b> Sequential nhanh nhất tại N=16, Gurobi tại N=32, OR-Tools tại N=64, Product tại N=128/256/1000 và Binary tại N=512.", style_bullet),
        Paragraph("• <b>Khi báo cáo:</b> luôn trình bày thời gian cùng tỷ lệ hoàn thành, timeout, license limit và SIGKILL; không suy rộng ngoài môi trường đã đo.", style_bullet),
        Spacer(1, 10),
        Paragraph("<b>2. Bộ Câu hỏi Phản biện Hội đồng Thường gặp:</b>", style_h2),
        Paragraph("<b>Q1: Em tự viết Solver hay dùng thư viện?</b>", style_box_header),
        Paragraph("=> <i>Trả lời:</i> Em xây dựng pipeline CNF và tích hợp đủ 5 encoding trong <code>sat_encoder.py</code>. Pairwise, Sequential và Binary dùng CardEnc của PySAT; Commander và Product được cài đặt trong project; Glucose3 giải CNF thu được.", style_body),
        Paragraph("<b>Q2: Tại sao CP lại viết code ngắn hơn SAT rất nhiều?</b>", style_box_header),
        Paragraph("=> <i>Trả lời:</i> Vì CP hỗ trợ ràng buộc toàn cục <code>AllDifferent</code>, bộ giải tự lan truyền ràng buộc mức biến nguyên thay vì phải phân rã thành mệnh đề nhị phân như SAT.", style_body)
    ]

    t_qa = Table([[qa_content]], colWidths=[710])
    t_qa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 1.5, COLOR_SECONDARY),
        ('PADDING', (0,0), (-1,-1), 14),
    ]))
    story.append(t_qa)

    # Build Document
    doc.build(story, onFirstPage=draw_slide_decorations, onLaterPages=draw_slide_decorations)
    print("PDF generated successfully:", pdf_filename)

if __name__ == "__main__":
    create_slide_deck()
