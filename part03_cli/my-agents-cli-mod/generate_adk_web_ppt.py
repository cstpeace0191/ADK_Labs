import sys
import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path: str):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    COLOR_BG_DARK = RGBColor(15, 23, 42)       # #0F172A Deep Slate Navy
    COLOR_BG_LIGHT = RGBColor(248, 250, 252)   # #F8FAFC Slate 50
    COLOR_CARD_BG = RGBColor(255, 255, 255)    # White
    COLOR_CARD_BORDER = RGBColor(226, 232, 240) # Slate 200
    COLOR_PRIMARY = RGBColor(26, 115, 232)     # Google Blue
    COLOR_PRIMARY_LIGHT = RGBColor(232, 240, 254) # Light Blue Pill
    COLOR_ACCENT_TEAL = RGBColor(14, 165, 233) # Sky Blue / Teal
    COLOR_TEXT_MAIN = RGBColor(30, 41, 59)     # Slate 800
    COLOR_TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
    COLOR_TEXT_WHITE = RGBColor(255, 255, 255)
    COLOR_ACCENT_GREEN = RGBColor(16, 185, 129)
    COLOR_ACCENT_PURPLE = RGBColor(139, 92, 246)
    COLOR_ROW_ALT = RGBColor(241, 245, 249)

    FONT_MAIN = "Malgun Gothic"

    def set_slide_background(slide, color):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, category="ADK WEB ARCHITECTURE"):
        # Category Pill / Supertitle
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11), Inches(0.35))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_bottom = tf_cat.margin_right = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.name = FONT_MAIN
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_PRIMARY

        # Title
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_bottom = tf.margin_right = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = FONT_MAIN
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_MAIN

    def create_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1)
        else:
            card.line.fill.background()
        return card

    # ==========================================
    # SLIDE 1: Title Slide (Dark Theme)
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_BG_DARK)

    # Decorative Badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.5), Inches(3.4), Inches(0.42))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 41, 59)
    badge.line.color.rgb = COLOR_PRIMARY
    badge.line.width = Pt(1.5)
    tf_b = badge.text_frame
    tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_b = tf_b.paragraphs[0]
    p_b.text = "GOOGLE AGENT DEVELOPMENT KIT"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.name = FONT_MAIN
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_ACCENT_TEAL

    # Main Title
    tb_title = s1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.3), Inches(2.0))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_t1 = tf_title.paragraphs[0]
    p_t1.text = "adk web --port 8000"
    p_t1.font.name = "Consolas"
    p_t1.font.size = Pt(36)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_PRIMARY_LIGHT

    p_t2 = tf_title.add_paragraph()
    p_t2.text = "웹 인터페이스 UI 생성 및 동작 원리 심층 분석"
    p_t2.font.name = FONT_MAIN
    p_t2.font.size = Pt(32)
    p_t2.font.bold = True
    p_t2.font.color.rgb = COLOR_TEXT_WHITE
    p_t2.space_before = Pt(8)

    # Subtitle / Overview Description
    tb_desc = s1.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(11.0), Inches(1.5))
    tf_desc = tb_desc.text_frame
    tf_desc.word_wrap = True
    p_d = tf_desc.paragraphs[0]
    p_d.text = "FastAPI 백엔드(DevServer)와 Angular Material 정적 SPA의 결합 구조, SSE 실시간 스트리밍 메커니즘, 핫 리로드 및 시각화 도구의 통합 아키텍처 해설"
    p_d.font.name = FONT_MAIN
    p_d.font.size = Pt(15)
    p_d.font.color.rgb = RGBColor(148, 163, 184)

    # Bottom Metadata Pill
    meta_box = s1.shapes.add_textbox(Inches(1.0), Inches(6.2), Inches(11.0), Inches(0.5))
    tf_m = meta_box.text_frame
    p_m = tf_m.paragraphs[0]
    p_m.text = "Target Port: 8000 | Framework: FastAPI + Uvicorn + Angular M3 | Dev Mode Architecture"
    p_m.font.name = "Consolas"
    p_m.font.size = Pt(11)
    p_m.font.color.rgb = RGBColor(100, 116, 139)

    # ==========================================
    # SLIDE 2: 전체 아키텍처 개요
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_BG_LIGHT)
    add_header(s2, "전체 시스템 아키텍처: 백엔드 & 프론트엔드 결합 구조")

    # 3 Cards Layout
    col_w = Inches(3.64)
    col_gap = Inches(0.4)
    top_pos = Inches(1.6)
    card_h = Inches(4.3)

    # Card 1: Client
    create_card(s2, Inches(0.8), top_pos, col_w, card_h)
    tb1 = s2.shapes.add_textbox(Inches(1.0), Inches(1.8), col_w - Inches(0.4), card_h - Inches(0.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "1. 프론트엔드 (Angular SPA)"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_PRIMARY

    bullets1 = [
        ("기술 스택", "Angular 기반 Single Page Application, Angular Material (M3) 테마"),
        ("사전 빌드 산출물", "ADK 파이썬 패키지 내부 'browser/' 폴더에 컴파일된 JS/CSS 정적 에셋 내장"),
        ("경량 배포", "사용자 PC에 Node.js/npm 설치 불필요, 파이썬 환경만으로 독립 구동"),
        ("주요 UI 컴포넌트", "에이전트 선택창, Playground 대화창, Graphviz 뷰어, 이벤트 트레이스 타임라인")
    ]
    for title, desc in bullets1:
        p = tf1.add_paragraph()
        p.space_before = Pt(10)
        p.text = f"• {title}: "
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_sub = tf1.add_paragraph()
        p_sub.text = f"  {desc}"
        p_sub.font.name = FONT_MAIN
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # Card 2: Communication
    create_card(s2, Inches(0.8) + col_w + col_gap, top_pos, col_w, card_h)
    tb2 = s2.shapes.add_textbox(Inches(1.0) + col_w + col_gap, Inches(1.8), col_w - Inches(0.4), card_h - Inches(0.4))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "2. 통신 프로토콜 (REST & SSE)"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(16)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_ACCENT_TEAL

    bullets2 = [
        ("REST API", "에이전트 목록 조회(/list-apps), 세션 생성 및 메타데이터 동기화"),
        ("Server-Sent Events", "/run_sse 엔드포인트를 통한 청크 단위 실시간 스트리밍"),
        ("이벤트 스트림 분기", "사고 과정(Thought), 도구 호출(Tool Call), 텍스트 토큰을 구분하여 실시간 렌더링"),
        ("보안 미들웨어", "OriginCheckMiddleware 및 로컬 루프백 DNS Rebinding 방지 적용")
    ]
    for title, desc in bullets2:
        p = tf2.add_paragraph()
        p.space_before = Pt(10)
        p.text = f"• {title}: "
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_sub = tf2.add_paragraph()
        p_sub.text = f"  {desc}"
        p_sub.font.name = FONT_MAIN
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # Card 3: Backend
    create_card(s2, Inches(0.8) + (col_w + col_gap) * 2, top_pos, col_w, card_h)
    tb3 = s2.shapes.add_textbox(Inches(1.0) + (col_w + col_gap) * 2, Inches(1.8), col_w - Inches(0.4), card_h - Inches(0.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "3. 백엔드 (DevServer)"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(16)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_ACCENT_PURPLE

    bullets3 = [
        ("FastAPI + Uvicorn", "비동기 ASGI 서버 구조로 8000 포트 바인딩 및 정적 파일 마운트"),
        ("DevServer 클래스", "프로덕션 ApiServer에 개발 전용(/dev/...) 기능 및 빌더 통합"),
        ("에이전트 로더", "NestedAgentLoader를 통해 로컬 디렉터리의 에이전트 자동 스캔"),
        ("로컬 영속성", "SQLite 기반 로컬 세션 및 로컬 파일시스템 기반 아티팩트 관리")
    ]
    for title, desc in bullets3:
        p = tf3.add_paragraph()
        p.space_before = Pt(10)
        p.text = f"• {title}: "
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_sub = tf3.add_paragraph()
        p_sub.text = f"  {desc}"
        p_sub.font.name = FONT_MAIN
        p_sub.font.size = Pt(10)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # Bottom summary box
    bot_card = create_card(s2, Inches(0.8), Inches(6.1), Inches(11.73), Inches(0.75), bg_color=COLOR_PRIMARY_LIGHT, border_color=COLOR_PRIMARY)
    tb_b = s2.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.3), Inches(0.65))
    tf_b = tb_b.text_frame
    p_bb = tf_b.paragraphs[0]
    p_bb.text = "💡 핵심 특징: 별도의 프론트엔드 개발 서버를 띄울 필요 없이, 'adk web' 단일 명령어만으로 백엔드 API와 프론트엔드 UI가 원스톱으로 제공됩니다."
    p_bb.font.name = FONT_MAIN
    p_bb.font.size = Pt(11.5)
    p_bb.font.bold = True
    p_bb.font.color.rgb = RGBColor(15, 76, 129)

    # ==========================================
    # SLIDE 3: 프론트엔드 UI 구성 및 서빙 방식
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_BG_LIGHT)
    add_header(s3, "웹 UI 리소스 패키징 및 FastAPI 마운트 방식")

    card_w2 = Inches(5.66)
    # Left Box
    create_card(s3, Inches(0.8), Inches(1.6), card_w2, Inches(5.2))
    tb_l = s3.shapes.add_textbox(Inches(1.0), Inches(1.8), card_w2 - Inches(0.4), Inches(4.8))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p_lh = tf_l.paragraphs[0]
    p_lh.text = "1. Angular 정적 번들 디렉터리 구조"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(17)
    p_lh.font.bold = True
    p_lh.font.color.rgb = COLOR_PRIMARY

    left_items = [
        ("저장 위치", "site-packages/google/adk/cli/browser/"),
        ("index.html", "Google Sans 웹폰트, M3 다크 테마 변수(--mat-sys-*) 및 <app-root> 선언"),
        ("main-*.js / polyfills-*.js", "컴파일된 Angular 핵심 애플리케이션 및 브라우저 호환성 번들"),
        ("chunk-*.js", "코드 스플리팅(Code Splitting)이 적용된 라우트별 비동기 로딩 모듈"),
        ("styles-*.css", "Google Material 3 전역 스타일 및 레이아웃 CSS")
    ]
    for tag, desc in left_items:
        p = tf_l.add_paragraph()
        p.space_before = Pt(12)
        p.text = f"📂 {tag}"
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_c = tf_l.add_paragraph()
        p_c.text = f"   {desc}"
        p_c.font.name = FONT_MAIN
        p_c.font.size = Pt(10.5)
        p_c.font.color.rgb = COLOR_TEXT_MUTED

    # Right Box
    create_card(s3, Inches(6.87), Inches(1.6), card_w2, Inches(5.2))
    tb_r = s3.shapes.add_textbox(Inches(7.07), Inches(1.8), card_w2 - Inches(0.4), Inches(4.8))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p_rh = tf_r.paragraphs[0]
    p_rh.text = "2. FastAPI 정적 마운트 & 런타임 설정 주입"
    p_rh.font.name = FONT_MAIN
    p_rh.font.size = Pt(17)
    p_rh.font.bold = True
    p_rh.font.color.rgb = COLOR_ACCENT_TEAL

    right_items = [
        ("경로 리다이렉션", "사용자가 '/' 또는 '/dev-ui'로 접속하면 자동으로 '/dev-ui/'로 307 리다이렉트 처리"),
        ("_DevUiStaticFiles 마운트", "app.mount('/dev-ui/', _DevUiStaticFiles(directory=web_assets_dir)) 등록"),
        ("동적 설정 JSON 엔드포인트", "GET /dev-ui/assets/config/runtime-config.json 제공"),
        ("동적 주입 파라미터", "backendUrl, 텔레메트리 동의 정보, 사용자 지정 로고(--logo-text, --logo-image-url)"),
        ("브라우저 구동 순서", "1) index.html 로드 -> 2) runtime-config.json fetch -> 3) /list-apps로 에이전트 목록 수신")
    ]
    for tag, desc in right_items:
        p = tf_r.add_paragraph()
        p.space_before = Pt(12)
        p.text = f"⚡ {tag}"
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_c = tf_r.add_paragraph()
        p_c.text = f"   {desc}"
        p_c.font.name = FONT_MAIN
        p_c.font.size = Pt(10.5)
        p_c.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================
    # SLIDE 4: adk web 실행 라이프사이클 (5단계)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_BG_LIGHT)
    add_header(s4, "서버 구동 라이프사이클: CLI 호출부터 브라우저 렌더링까지")

    step_w = Inches(2.2)
    step_gap = Inches(0.18)
    step_top = Inches(1.8)
    step_h = Inches(4.8)

    steps = [
        ("Step 1", "CLI 명령어 파싱", "cli_tools_click.py", [
            "adk web 커맨드 진입",
            "--port 8000, --host 인자 수집",
            "agents_dir 경로 확인",
            "로깅 및 Click context 설정"
        ], COLOR_PRIMARY),
        ("Step 2", "DevServer 초기화", "fast_api.py", [
            "get_fast_api_app(web=True)",
            "ApiServer 대신 DevServer 생성",
            "개발용 엔드포인트(/dev/...) 활성화",
            "Lifespan 컨텍스트 등록"
        ], COLOR_ACCENT_TEAL),
        ("Step 3", "에이전트 스캔 & 로더", "NestedAgentLoader", [
            "지정 폴더 내 에이전트 자동 검색",
            "agent.py, root_agent.yaml 로드",
            "세션/메모리/아티팩트 서비스 초기화",
            "SQLite 로컬 스토리지 바인딩"
        ], COLOR_ACCENT_PURPLE),
        ("Step 4", "정적 UI 마운트", "api_server.py", [
            "browser/ 경로를 /dev-ui/에 마운트",
            "runtime-config.json 라우트 등록",
            "루트 경로(/) 자동 리다이렉트",
            "CORS 및 Origin 필터 적용"
        ], COLOR_ACCENT_GREEN),
        ("Step 5", "Uvicorn 서버 기동", "uvicorn.run()", [
            "127.0.0.1:8000 루프백 대기",
            "파일 감지(Reload) 프로세스 가동",
            "터미널에 접속 URL 녹색 배너 출력",
            "브라우저 HTTP/SSE 요청 처리 시작"
        ], RGBColor(234, 88, 12))
    ]

    for i, (s_num, s_title, s_file, s_details, col_accent) in enumerate(steps):
        cur_left = Inches(0.8) + (step_w + step_gap) * i
        card = create_card(s4, cur_left, step_top, step_w, step_h)

        # Header Pill
        pill = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cur_left + Inches(0.15), step_top + Inches(0.15), step_w - Inches(0.3), Inches(0.35))
        pill.fill.solid()
        pill.fill.fore_color.rgb = col_accent
        pill.line.fill.background()
        tf_p = pill.text_frame
        tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
        pp = tf_p.paragraphs[0]
        pp.text = s_num
        pp.alignment = PP_ALIGN.CENTER
        pp.font.name = FONT_MAIN
        pp.font.size = Pt(11)
        pp.font.bold = True
        pp.font.color.rgb = COLOR_TEXT_WHITE

        # Step Title
        tb_st = s4.shapes.add_textbox(cur_left + Inches(0.15), step_top + Inches(0.55), step_w - Inches(0.3), Inches(0.75))
        tf_st = tb_st.text_frame
        tf_st.word_wrap = True
        pst = tf_st.paragraphs[0]
        pst.text = s_title
        pst.font.name = FONT_MAIN
        pst.font.size = Pt(13)
        pst.font.bold = True
        pst.font.color.rgb = COLOR_TEXT_MAIN

        pst_f = tf_st.add_paragraph()
        pst_f.text = s_file
        pst_f.font.name = "Consolas"
        pst_f.font.size = Pt(9)
        pst_f.font.color.rgb = COLOR_TEXT_MUTED

        # Step Details
        tb_sd = s4.shapes.add_textbox(cur_left + Inches(0.15), step_top + Inches(1.35), step_w - Inches(0.3), Inches(3.2))
        tf_sd = tb_sd.text_frame
        tf_sd.word_wrap = True
        for d in s_details:
            p = tf_sd.add_paragraph()
            p.space_before = Pt(8)
            p.text = f"• {d}"
            p.font.name = FONT_MAIN
            p.font.size = Pt(10)
            p.font.color.rgb = COLOR_TEXT_MAIN

    # ==========================================
    # SLIDE 5: 실시간 대화 스트리밍 (/run_sse)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_BG_LIGHT)
    add_header(s5, "실시간 대화 스트리밍 프로토콜: /run_sse 이벤트 흐름")

    # Left: Protocol Diagram Card
    diag_w = Inches(5.66)
    create_card(s5, Inches(0.8), Inches(1.6), diag_w, Inches(5.2))
    tb_dg = s5.shapes.add_textbox(Inches(1.0), Inches(1.8), diag_w - Inches(0.4), Inches(4.8))
    tf_dg = tb_dg.text_frame
    tf_dg.word_wrap = True
    p_dh = tf_dg.paragraphs[0]
    p_dh.text = "클라이언트-서버 SSE 통신 흐름"
    p_dh.font.name = FONT_MAIN
    p_dh.font.size = Pt(17)
    p_dh.font.bold = True
    p_dh.font.color.rgb = COLOR_PRIMARY

    p_code = tf_dg.add_paragraph()
    p_code.space_before = Pt(14)
    p_code.text = (
        "[브라우저 UI]                           [DevServer]\n"
        "     │                                       │\n"
        "     │── 1. POST /run_sse ──────────────────>│\n"
        "     │   (RunAgentRequest JSON body)         │\n"
        "     │                                       │\n"
        "     │<── 2. HTTP 200 (text/event-stream) ───│\n"
        "     │                                       │\n"
        "     │<── 3. event: trace (사고 과정) ───────│\n"
        "     │<── 4. event: tool_call (도구 호출) ───│\n"
        "     │<── 5. event: tool_result (도구 결과) ─│\n"
        "     │<── 6. event: chunk (텍스트 토큰) ─────│\n"
        "     │<── 7. event: session_update ──────────│\n"
        "     │                                       │\n"
    )
    p_code.font.name = "Consolas"
    p_code.font.size = Pt(10.5)
    p_code.font.color.rgb = RGBColor(15, 23, 42)

    # Right: 5 Event Stages Breakdown Card
    create_card(s5, Inches(6.87), Inches(1.6), diag_w, Inches(5.2))
    tb_ev = s5.shapes.add_textbox(Inches(7.07), Inches(1.8), diag_w - Inches(0.4), Inches(4.8))
    tf_ev = tb_ev.text_frame
    tf_ev.word_wrap = True
    p_eh = tf_ev.paragraphs[0]
    p_eh.text = "SSE 이벤트 타입 및 UI 렌더링 방식"
    p_eh.font.name = FONT_MAIN
    p_eh.font.size = Pt(17)
    p_eh.font.bold = True
    p_eh.font.color.rgb = COLOR_ACCENT_TEAL

    event_list = [
        ("trace (사고 과정)", "LLM의 중간 추론 및 Chain-of-Thought 데이터를 전달하여 접이식 아코디언 상자에 표시"),
        ("tool_call (도구 호출)", "에이전트가 어떤 도구를 어떤 파라미터로 호출했는지 호출 명세를 시각화"),
        ("tool_result (도구 결과)", "실행된 함수/도구의 반환값 및 에러 상태를 UI에 구조화된 JSON 형태로 렌더링"),
        ("chunk (텍스트 토큰)", "최종 답변 텍스트를 실시간 타이핑 효과(Typing Effect)로 스트리밍 렌더링"),
        ("session_update (상태 커밋)", "대화 종료 시 세션 상태(State Delta)를 SQLite에 커밋하고 UI 세션 기록 갱신")
    ]
    for ev_name, ev_desc in event_list:
        p = tf_ev.add_paragraph()
        p.space_before = Pt(10)
        p.text = f"🔹 {ev_name}"
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_c = tf_ev.add_paragraph()
        p_c.text = f"   {ev_desc}"
        p_c.font.name = FONT_MAIN
        p_c.font.size = Pt(10)
        p_c.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================
    # SLIDE 6: 핵심 개발자 편의 기능 4가지
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_BG_LIGHT)
    add_header(s6, "ADK Web만의 핵심 개발자 도구 (Developer Features)")

    grid_w = Inches(5.66)
    grid_h = Inches(2.45)
    row1_t = Inches(1.6)
    row2_t = Inches(4.35)
    col1_l = Inches(0.8)
    col2_l = Inches(6.87)

    features = [
        (col1_l, row1_t, "1. Agent Graph (구조 시각화)", COLOR_PRIMARY, [
            "• API: GET /dev/apps/{app_name}/build_graph",
            "• 메커니즘: agent_graph.py가 에이전트 클래스를 파싱하여 Graphviz DOT 그래프 생성",
            "• 시각화 내용: 서브에이전트 계층, 조건부 전이 라우팅, 연결된 도구 목록 다이어그램 제공"
        ]),
        (col2_l, row1_t, "2. 실시간 핫 리로드 (Watchdog)", COLOR_ACCENT_TEAL, [
            "• 파일 감지: watchdog.observers.Observer가 agents_dir 변경 모니터링",
            "• 캐시 무효화: 코드 변경 시 메모리에 캐시된 Runner 인스턴스를 즉시 갱신",
            "• 무중단 반영: 서버 재시작 없이 브라우저에서 바로 새 대화를 시작해 로직 테스트 가능"
        ]),
        (col1_l, row2_t, "3. Agent Builder 어시스턴트", COLOR_ACCENT_PURPLE, [
            "• 시각적 조작: UI 상에서 프롬프트, 모델, 도구 파라미터를 대화식으로 수정",
            "• 파일 동기화: /dev/apps/{app_name}/builder/save로 로컬 YAML/Python 코드에 직접 반영",
            "• 안전 장치: 임의 코드 쓰기 방지를 위해 127.0.0.1 로컬 루프백 접속 시에만 활성화"
        ]),
        (col2_l, row2_t, "4. 평가(Eval) & 이벤트 트레이스", COLOR_ACCENT_GREEN, [
            "• 트레이스 디버깅: /debug/trace 엔드포인트로 세션별 모든 이벤트 타임라인 확인",
            "• Eval Runner 연동: /dev/apps/{app_name}/eval-sets로 웹에서 바로 평가 데이터셋 실행",
            "• 아티팩트 관리: 생성된 파일/데이터의 버전별 다운로드 및 브라우저 즉시 미리보기"
        ])
    ]

    for c_left, c_top, f_title, f_col, f_bullets in features:
        create_card(s6, c_left, c_top, grid_w, grid_h)
        tb = s6.shapes.add_textbox(c_left + Inches(0.2), c_top + Inches(0.15), grid_w - Inches(0.4), grid_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = f_title
        pt.font.name = FONT_MAIN
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = f_col

        for b in f_bullets:
            p = tf.add_paragraph()
            p.space_before = Pt(4)
            p.text = b
            p.font.name = FONT_MAIN
            p.font.size = Pt(10.5)
            p.font.color.rgb = COLOR_TEXT_MAIN

    # ==========================================
    # SLIDE 7: adk web vs adk api_server 비교 테이블
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_BG_LIGHT)
    add_header(s7, "개발용(adk web) vs 프로덕션(adk api_server) 아키텍처 비교")

    rows = 7
    cols = 3
    tbl_top = Inches(1.6)
    tbl_left = Inches(0.8)
    tbl_w = Inches(11.73)
    tbl_h = Inches(5.0)

    table_shape = s7.shapes.add_table(rows, cols, tbl_left, tbl_top, tbl_w, tbl_h)
    tbl = table_shape.table
    tbl.columns[0].width = Inches(2.6)
    tbl.columns[1].width = Inches(4.56)
    tbl.columns[2].width = Inches(4.56)

    headers = ["비교 항목", "adk web (로컬 개발용)", "adk api_server (프로덕션 배포용)"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_MAIN
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_WHITE

    table_data = [
        ("서버 클래스", "DevServer (ApiServer를 상속받아 개발 기능 확장)", "ApiServer (경량 순수 코어 API 서버)"),
        ("웹 UI 서빙 (/dev-ui)", "포함 (사전 컴파일된 Angular SPA 마운트)", "미포함 (정적 파일 및 UI 엔드포인트 비활성화)"),
        ("개발용 엔드포인트", "활성화 (/dev/... 빌더, 트레이스, 테스트, 그래프)", "비활성화 (외부 노출 차단)"),
        ("코드 변경 감지", "기본 활성화 (--reload 및 watchdog 기반 실시간 반영)", "비활성화 (컨테이너/불변 프로세스로 구동)"),
        ("기본 데이터 저장소", "로컬 파일시스템 및 SQLite (--use_local_storage=True)", "Cloud SQL, Cloud Storage, Firestore 등 분산 저장소"),
        ("보안 및 인증 모델", "로컬 루프백 전용 (인증 없음, Origin/Host 검증)", "OIDC 토큰 검증, IAM 서비스 계정, Cloud Run 인증")
    ]

    for i, (col1, col2, col3) in enumerate(table_data, start=1):
        bg = COLOR_ROW_ALT if i % 2 == 1 else COLOR_CARD_BG
        for j, val in enumerate([col1, col2, col3]):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_MAIN
            p.font.size = Pt(11)
            if j == 0:
                p.font.bold = True
                p.alignment = PP_ALIGN.CENTER
                p.font.color.rgb = COLOR_TEXT_MAIN
            else:
                p.font.color.rgb = COLOR_TEXT_MAIN

    # ==========================================
    # SLIDE 8: 요약 및 유용한 실행 옵션
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_BG_LIGHT)
    add_header(s8, "핵심 요약 및 유용한 adk web 실행 옵션")

    # Left: 3 Key Takeaways
    create_card(s8, Inches(0.8), Inches(1.6), card_w2, Inches(5.2))
    tb_t = s8.shapes.add_textbox(Inches(1.0), Inches(1.8), card_w2 - Inches(0.4), Inches(4.8))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p_th = tf_t.paragraphs[0]
    p_th.text = "🎯 핵심 요약 (Key Takeaways)"
    p_th.font.name = FONT_MAIN
    p_th.font.size = Pt(17)
    p_th.font.bold = True
    p_th.font.color.rgb = COLOR_PRIMARY

    takeaways = [
        ("올인원 로컬 개발 환경", "추가적인 프론트엔드 빌드나 의존성 설정 없이, 파이썬 패키지 내부의 Angular M3 SPA를 즉시 서빙하여 생산성을 극대화합니다."),
        ("실시간 스트리밍 대화", "/run_sse 엔드포인트를 통해 LLM의 사고 과정(Thought), 도구 호출(Tool Call), 텍스트 토큰을 분리 수신하여 실시간으로 렌더링합니다."),
        ("개발자 친화적 도구 내장", "Graphviz 기반 에이전트 구조 시각화, 파일 수정 시 자동 리로드, 웹 기반 데이터셋 평가 러너를 기본 지원합니다.")
    ]
    for num_t, desc_t in takeaways:
        p = tf_t.add_paragraph()
        p.space_before = Pt(14)
        p.text = f"✔ {num_t}"
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_TEXT_MAIN
        p_c = tf_t.add_paragraph()
        p_c.text = f"   {desc_t}"
        p_c.font.name = FONT_MAIN
        p_c.font.size = Pt(10.5)
        p_c.font.color.rgb = COLOR_TEXT_MUTED

    # Right: CLI Options Reference
    create_card(s8, Inches(6.87), Inches(1.6), card_w2, Inches(5.2))
    tb_op = s8.shapes.add_textbox(Inches(7.07), Inches(1.8), card_w2 - Inches(0.4), Inches(4.8))
    tf_op = tb_op.text_frame
    tf_op.word_wrap = True
    p_oph = tf_op.paragraphs[0]
    p_oph.text = "⚙️ 유용한 CLI 명령어 옵션"
    p_oph.font.name = FONT_MAIN
    p_oph.font.size = Pt(17)
    p_oph.font.bold = True
    p_oph.font.color.rgb = COLOR_ACCENT_TEAL

    cli_options = [
        ("--port <번호>", "서버 바인딩 포트 변경 (기본값: 8000)", "adk web --port 8080"),
        ("--logo-text <텍스트>", "UI 상단 헤더의 로고 텍스트 커스터마이징", "--logo-text 'My Custom Agent'"),
        ("--logo-image-url <URL>", "UI 상단 로고 이미지 URL 지정", "--logo-image-url 'https://.../logo.png'"),
        ("--reload / --no-reload", "코드 변경 시 자동 리로드 여부 제어 (기본: True)", "adk web --no-reload"),
        ("<agents_dir> 지정", "현재 폴더가 아닌 특정 에이전트 디렉터리 타겟팅", "adk web ./app")
    ]
    for opt, desc, example in cli_options:
        p = tf_op.add_paragraph()
        p.space_before = Pt(8)
        p.text = f"• {opt}: {desc}"
        p.font.name = FONT_MAIN
        p.font.bold = True
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_MAIN

        p_ex = tf_op.add_paragraph()
        p_ex.text = f"   예시: {example}"
        p_ex.font.name = "Consolas"
        p_ex.font.size = Pt(9.5)
        p_ex.font.color.rgb = COLOR_PRIMARY

    # Save
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "ADK_Web_Architecture_Guide.pptx"
    create_deck(out_file)

