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
    p_t2.text = "In-Depth Analysis of the Web UI and How It Works"
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
    p_d.text = "An overview of the integrated architecture of the FastAPI DevServer and Angular Material SPA, SSE streaming, hot reload, and visualization tools"
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
    # SLIDE 2: System architecture overview
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_BG_LIGHT)
    add_header(s2, "System Architecture: Integrated Backend and Frontend")

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
    p1.text = "1. Frontend (Angular SPA)"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_PRIMARY

    bullets1 = [
        ("Technology stack", "Angular-based Single Page Application with an Angular Material (M3) theme"),
        ("Prebuilt assets", "Compiled JS/CSS assets are included in the ADK Python package's 'browser/' folder"),
        ("Lightweight deployment", "No Node.js/npm installation required; runs using the Python environment alone"),
        ("Key UI components", "Agent selector, Playground chat, Graphviz viewer, and event trace timeline")
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
    p2.text = "2. Communication Protocols (REST & SSE)"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(16)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_ACCENT_TEAL

    bullets2 = [
        ("REST API", "List agents (/list-apps), create sessions, and synchronize metadata"),
        ("Server-Sent Events", "Real-time chunked streaming through the /run_sse endpoint"),
        ("Event stream handling", "Render thoughts, tool calls, and text tokens separately in real time"),
        ("Security middleware", "OriginCheckMiddleware and local loopback DNS rebinding protection")
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
    p3.text = "3. Backend (DevServer)"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(16)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_ACCENT_PURPLE

    bullets3 = [
        ("FastAPI + Uvicorn", "Async ASGI server bound to port 8000 with static file mounting"),
        ("DevServer class", "Extends the production ApiServer with development (/dev/...) features and the builder"),
        ("Agent loader", "Automatically scans local directories for agents through NestedAgentLoader"),
        ("Local persistence", "SQLite-based sessions and artifacts stored on the local filesystem")
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
    p_bb.text = "💡 Key feature: A single 'adk web' command serves both the backend API and frontend UI; no separate frontend development server is needed."
    p_bb.font.name = FONT_MAIN
    p_bb.font.size = Pt(11.5)
    p_bb.font.bold = True
    p_bb.font.color.rgb = RGBColor(15, 76, 129)

    # ==========================================
    # SLIDE 3: Frontend UI structure and serving
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_BG_LIGHT)
    add_header(s3, "Web UI Asset Packaging and FastAPI Mounting")

    card_w2 = Inches(5.66)
    # Left Box
    create_card(s3, Inches(0.8), Inches(1.6), card_w2, Inches(5.2))
    tb_l = s3.shapes.add_textbox(Inches(1.0), Inches(1.8), card_w2 - Inches(0.4), Inches(4.8))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p_lh = tf_l.paragraphs[0]
    p_lh.text = "1. Angular Static Bundle Directory Structure"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(17)
    p_lh.font.bold = True
    p_lh.font.color.rgb = COLOR_PRIMARY

    left_items = [
        ("Location", "site-packages/google/adk/cli/browser/"),
        ("index.html", "Google Sans web font, M3 dark theme variables (--mat-sys-*), and <app-root> declaration"),
        ("main-*.js / polyfills-*.js", "Compiled Angular application and browser compatibility bundles"),
        ("chunk-*.js", "Route-specific asynchronous modules using code splitting"),
        ("styles-*.css", "Global Google Material 3 styles and layout CSS")
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
    p_rh.text = "2. FastAPI Static Mounting and Runtime Configuration Injection"
    p_rh.font.name = FONT_MAIN
    p_rh.font.size = Pt(17)
    p_rh.font.bold = True
    p_rh.font.color.rgb = COLOR_ACCENT_TEAL

    right_items = [
        ("Path redirection", "Requests to '/' or '/dev-ui' are automatically redirected to '/dev-ui/' with status 307"),
        ("_DevUiStaticFiles mount", "Register app.mount('/dev-ui/', _DevUiStaticFiles(directory=web_assets_dir))"),
        ("Dynamic configuration endpoint", "Serves GET /dev-ui/assets/config/runtime-config.json"),
        ("Injected runtime parameters", "backendUrl, telemetry consent, and custom logos (--logo-text, --logo-image-url)"),
        ("Browser startup sequence", "1) Load index.html -> 2) Fetch runtime-config.json -> 3) Receive agent list from /list-apps")
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
    # SLIDE 4: adk web lifecycle (5 steps)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_BG_LIGHT)
    add_header(s4, "Server Lifecycle: From CLI Invocation to Browser Rendering")

    step_w = Inches(2.2)
    step_gap = Inches(0.18)
    step_top = Inches(1.8)
    step_h = Inches(4.8)

    steps = [
        ("Step 1", "Parse CLI Command", "cli_tools_click.py", [
            "Enter the adk web command",
            "Collect --port 8000 and --host arguments",
            "Resolve the agents_dir path",
            "Configure logging and Click context"
        ], COLOR_PRIMARY),
        ("Step 2", "Initialize DevServer", "fast_api.py", [
            "get_fast_api_app(web=True)",
            "Create DevServer instead of ApiServer",
            "Enable development endpoints (/dev/...)",
            "Register the lifespan context"
        ], COLOR_ACCENT_TEAL),
        ("Step 3", "Scan and Load Agents", "NestedAgentLoader", [
            "Automatically find agents in the specified folder",
            "Load agent.py and root_agent.yaml",
            "Initialize session, memory, and artifact services",
            "Bind local SQLite storage"
        ], COLOR_ACCENT_PURPLE),
        ("Step 4", "Mount Static UI", "api_server.py", [
            "Mount browser/ at /dev-ui/",
            "Register the runtime-config.json route",
            "Automatically redirect the root path (/)",
            "Apply CORS and Origin filters"
        ], COLOR_ACCENT_GREEN),
        ("Step 5", "Start Uvicorn Server", "uvicorn.run()", [
            "Listen on loopback address 127.0.0.1:8000",
            "Start the file-watching reload process",
            "Print the access URL banner in the terminal",
            "Begin handling browser HTTP/SSE requests"
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
    # SLIDE 5: Real-time conversation streaming (/run_sse)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_BG_LIGHT)
    add_header(s5, "Real-Time Conversation Streaming: /run_sse Event Flow")

    # Left: Protocol Diagram Card
    diag_w = Inches(5.66)
    create_card(s5, Inches(0.8), Inches(1.6), diag_w, Inches(5.2))
    tb_dg = s5.shapes.add_textbox(Inches(1.0), Inches(1.8), diag_w - Inches(0.4), Inches(4.8))
    tf_dg = tb_dg.text_frame
    tf_dg.word_wrap = True
    p_dh = tf_dg.paragraphs[0]
    p_dh.text = "Client-Server SSE Communication Flow"
    p_dh.font.name = FONT_MAIN
    p_dh.font.size = Pt(17)
    p_dh.font.bold = True
    p_dh.font.color.rgb = COLOR_PRIMARY

    p_code = tf_dg.add_paragraph()
    p_code.space_before = Pt(14)
    p_code.text = (
        "[Browser UI]                            [DevServer]\n"
        "     │                                       │\n"
        "     │── 1. POST /run_sse ──────────────────>│\n"
        "     │   (RunAgentRequest JSON body)         │\n"
        "     │                                       │\n"
        "     │<── 2. HTTP 200 (text/event-stream) ───│\n"
        "     │                                       │\n"
        "     │<── 3. event: trace (reasoning) ───────│\n"
        "     │<── 4. event: tool_call ───────────────│\n"
        "     │<── 5. event: tool_result ─────────────│\n"
        "     │<── 6. event: chunk (text token) ──────│\n"
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
    p_eh.text = "SSE Event Types and UI Rendering"
    p_eh.font.name = FONT_MAIN
    p_eh.font.size = Pt(17)
    p_eh.font.bold = True
    p_eh.font.color.rgb = COLOR_ACCENT_TEAL

    event_list = [
        ("trace (reasoning)", "Delivers intermediate LLM reasoning and Chain-of-Thought data for display in a collapsible panel"),
        ("tool_call", "Visualizes which tool the agent called and the parameters it used"),
        ("tool_result", "Renders function/tool return values and error states as structured JSON in the UI"),
        ("chunk (text token)", "Streams the final answer in real time with a typing effect"),
        ("session_update (state commit)", "Commits session state (State Delta) to SQLite and updates the UI session history")
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
    # SLIDE 6: Four key developer convenience features
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_BG_LIGHT)
    add_header(s6, "Key ADK Web Developer Features")

    grid_w = Inches(5.66)
    grid_h = Inches(2.45)
    row1_t = Inches(1.6)
    row2_t = Inches(4.35)
    col1_l = Inches(0.8)
    col2_l = Inches(6.87)

    features = [
        (col1_l, row1_t, "1. Agent Graph (Structure Visualization)", COLOR_PRIMARY, [
            "• API: GET /dev/apps/{app_name}/build_graph",
            "• Mechanism: agent_graph.py parses agent classes and generates Graphviz DOT graphs",
            "• Visualization: Diagrams of sub-agent hierarchies, conditional routing, and connected tools"
        ]),
        (col2_l, row1_t, "2. Live Hot Reload (Watchdog)", COLOR_ACCENT_TEAL, [
            "• File monitoring: watchdog.observers.Observer watches for changes in agents_dir",
            "• Cache invalidation: Refreshes the Runner instance cached in memory when code changes",
            "• No interruption: Test changes in a new browser conversation without restarting the server"
        ]),
        (col1_l, row2_t, "3. Agent Builder Assistant", COLOR_ACCENT_PURPLE, [
            "• Visual editing: Interactively edit prompts, models, and tool parameters in the UI",
            "• File synchronization: Apply changes directly to local YAML/Python using /dev/apps/{app_name}/builder/save",
            "• Safeguard: Enabled only on the 127.0.0.1 loopback interface to prevent arbitrary code writes"
        ]),
        (col2_l, row2_t, "4. Evaluation and Event Traces", COLOR_ACCENT_GREEN, [
            "• Trace debugging: Inspect each session's event timeline through /debug/trace",
            "• Eval Runner integration: Run evaluation datasets from the web using /dev/apps/{app_name}/eval-sets",
            "• Artifact management: Download generated files/data by version and preview them in the browser"
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
    # SLIDE 7: adk web vs adk api_server comparison table
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_BG_LIGHT)
    add_header(s7, "Development (adk web) vs. Production (adk api_server) Architecture")

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

    headers = ["Feature", "adk web (local development)", "adk api_server (production deployment)"]
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
        ("Server class", "DevServer (extends ApiServer with development features)", "ApiServer (lightweight core API server)"),
        ("Web UI (/dev-ui)", "Included (mounts the precompiled Angular SPA)", "Not included (static files and UI endpoints disabled)"),
        ("Development endpoints", "Enabled (/dev/... builder, traces, tests, graphs)", "Disabled (prevents external exposure)"),
        ("Code change detection", "Enabled by default (--reload and watchdog-based updates)", "Disabled (runs in a container or immutable process)"),
        ("Default data storage", "Local filesystem and SQLite (--use_local_storage=True)", "Distributed stores such as Cloud SQL, Cloud Storage, and Firestore"),
        ("Security and authentication", "Local loopback only (no authentication; Origin/Host validation)", "OIDC token validation, IAM service accounts, and Cloud Run authentication")
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
    # SLIDE 8: Summary and useful command-line options
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_BG_LIGHT)
    add_header(s8, "Key Takeaways and Useful adk web Options")

    # Left: 3 Key Takeaways
    create_card(s8, Inches(0.8), Inches(1.6), card_w2, Inches(5.2))
    tb_t = s8.shapes.add_textbox(Inches(1.0), Inches(1.8), card_w2 - Inches(0.4), Inches(4.8))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p_th = tf_t.paragraphs[0]
    p_th.text = "🎯 Key Takeaways"
    p_th.font.name = FONT_MAIN
    p_th.font.size = Pt(17)
    p_th.font.bold = True
    p_th.font.color.rgb = COLOR_PRIMARY

    takeaways = [
        ("All-in-one local development", "Serve the Angular M3 SPA included in the Python package without a separate frontend build or dependency setup."),
        ("Real-time streaming conversations", "Receive and render LLM thoughts, tool calls, and text tokens separately through the /run_sse endpoint."),
        ("Built-in developer tools", "Includes Graphviz agent visualization, automatic reload on file changes, and a web-based dataset evaluation runner.")
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
    p_oph.text = "⚙️ Useful CLI Options"
    p_oph.font.name = FONT_MAIN
    p_oph.font.size = Pt(17)
    p_oph.font.bold = True
    p_oph.font.color.rgb = COLOR_ACCENT_TEAL

    cli_options = [
        ("--port <number>", "Change the server port (default: 8000)", "adk web --port 8080"),
        ("--logo-text <text>", "Customize the logo text in the UI header", "--logo-text 'My Custom Agent'"),
        ("--logo-image-url <URL>", "Set the URL of the logo image in the UI header", "--logo-image-url 'https://.../logo.png'"),
        ("--reload / --no-reload", "Enable or disable reload on code changes (default: True)", "adk web --no-reload"),
        ("<agents_dir>", "Target an agent directory instead of the current folder", "adk web ./app")
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
        p_ex.text = f"   Example: {example}"
        p_ex.font.name = "Consolas"
        p_ex.font.size = Pt(9.5)
        p_ex.font.color.rgb = COLOR_PRIMARY

    # Save
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "ADK_Web_Architecture_Guide.pptx"
    create_deck(out_file)
