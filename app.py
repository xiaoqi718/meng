"""
meng - AI 简历优化器
Streamlit 前端主程序
"""

import base64
import html
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.resume_analyzer import analyze_resume
from src.resume_parser import extract_text_from_pdf

# 加载 .env 文件
load_dotenv()


@dataclass
class ChangeBlock:
    """AI 输出的逐段修改块"""

    section: str
    original: str
    modified: str
    reason: str


def get_background_css() -> str:
    """
    读取 assets/background.* 图片并转为 base64 CSS 背景
    支持 png / jpg / jpeg / webp
    如果图片不存在，返回空字符串（使用默认背景色）
    """
    candidates = ["assets/background.png", "assets/background.jpg", "assets/background.jpeg", "assets/background.webp"]

    for candidate in candidates:
        image_path = Path(candidate)
        if not image_path.exists():
            continue

        data = image_path.read_bytes()
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            mime = "image/png"
        elif data.startswith(b"\xff\xd8"):
            mime = "image/jpeg"
        elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            mime = "image/webp"
        else:
            continue

        encoded = base64.b64encode(data).decode()
        return f"url('data:{mime};base64,{encoded}')"

    return ""


# 页面配置
st.set_page_config(
    page_title="meng - AI 简历优化器",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

bg_image = get_background_css()

# 自定义样式：深色玻璃拟态 + 简历精修页风格
st.markdown(
    f"""
    <style>
    /* 页面背景：深色 + 星空图 */
    .stApp {{
        background:
            radial-gradient(ellipse at top, rgba(15, 23, 42, 0.78), rgba(2, 6, 23, 0.95)),
            {bg_image if bg_image else "linear-gradient(180deg, #020617 0%, #0F172A 100%)"}
            center/cover no-repeat fixed;
        color: #F8FAFC;
    }}

    /* 隐藏 Streamlit 底部和多余元素 */
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none !important;}}
    #MainMenu {{visibility: hidden;}}

    /* 主容器 */
    .main .block-container {{
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}

    /* 玻璃卡片 */
    .glass-card {{
        background: rgba(15, 23, 42, 0.58);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 28px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        margin-bottom: 28px;
    }}

    .card-title {{
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: -0.3px;
    }}

    .card-subtitle {{
        font-size: 0.95rem;
        color: #94A3B8;
        line-height: 1.6;
    }}

    /* Hero 区域 */
    .hero {{
        text-align: center;
        margin-bottom: 2.5rem;
        padding: 1.5rem 0 1rem 0;
    }}

    .hero-topbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto 2rem auto;
        padding: 0 1rem;
    }}

    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(217, 179, 120, 0.12);
        border: 1px solid rgba(217, 179, 120, 0.25);
        color: #D9B378;
        font-size: 0.85rem;
        font-weight: 600;
    }}

    .hero-view-toggle {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #CBD5E1;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: default;
    }}

    .hero-eyebrow {{
        font-size: 0.85rem;
        font-weight: 500;
        color: #D9B378;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }}

    .hero-title {{
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -2px;
        margin-bottom: 0.75rem !important;
        background: linear-gradient(135deg, #F8FAFC 0%, #D9B378 50%, #C9A86C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .hero-subtitle {{
        font-size: 1.15rem;
        color: #94A3B8;
        line-height: 1.6;
        max-width: 560px;
        margin: 0 auto;
    }}

    /* 统计区 */
    .stats-row {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 64px;
        margin: 2.5rem 0 1rem 0;
        flex-wrap: wrap;
    }}

    .stat-item {{
        text-align: center;
        min-width: 120px;
    }}

    .stat-number {{
        font-size: 2.4rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1;
        margin-bottom: 0.4rem;
        background: linear-gradient(135deg, #F8FAFC 0%, #D9B378 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .stat-label {{
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
    }}

    .stat-divider {{
        width: 1px;
        height: 48px;
        background: rgba(255, 255, 255, 0.10);
    }}

    /* 步骤卡片 */
    .steps-row {{
        display: flex;
        gap: 20px;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }}

    .step-card {{
        flex: 1;
        min-width: 260px;
        background: rgba(15, 23, 42, 0.50);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        transition: all 0.25s ease;
    }}

    .step-card.active {{
        border: 1px solid rgba(59, 130, 246, 0.55);
        background: rgba(59, 130, 246, 0.12);
        box-shadow: 0 0 24px rgba(59, 130, 246, 0.20);
    }}

    .step-card.completed {{
        border-color: rgba(16, 185, 129, 0.40);
    }}

    .step-number {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.08);
        color: #CBD5E1;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 14px;
    }}

    .step-card.active .step-number {{
        background: linear-gradient(135deg, #3B82F6 0%, #6366F1 100%);
        color: #fff;
    }}

    .step-card.completed .step-number {{
        background: rgba(16, 185, 129, 0.20);
        color: #34D399;
    }}

    .step-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 8px;
    }}

    .step-desc {{
        font-size: 0.88rem;
        color: #94A3B8;
        line-height: 1.6;
    }}

    /* 上传区 */
    .stFileUploader {{
        background: rgba(15, 23, 42, 0.40) !important;
        backdrop-filter: blur(12px);
        border: 2px dashed rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px;
        padding: 2rem;
    }}

    .stFileUploader:hover {{
        border-color: rgba(59, 130, 246, 0.60) !important;
        background: rgba(15, 23, 42, 0.50) !important;
    }}

    .stFileUploader label,
    .stFileUploader > div > div,
    .stFileUploader small {{
        color: #CBD5E1 !important;
    }}

    /* 按钮 */
    .stButton > button {{
        width: 100%;
        border-radius: 12px;
        height: 3rem;
        font-size: 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #3B82F6 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.30);
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.45);
    }}

    .stButton > button:active {{
        transform: translateY(0);
    }}

    .stButton > button:disabled {{
        background: rgba(148, 163, 184, 0.30) !important;
        box-shadow: none;
    }}

    /* 评分区 */
    .score-metric {{
        text-align: center;
    }}

    .score-number {{
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }}

    .score-label {{
        font-size: 0.9rem;
        color: #94A3B8;
        font-weight: 500;
    }}

    .verdict-box {{
        background: rgba(15, 23, 42, 0.40);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        height: 100%;
    }}

    .verdict-title {{
        font-size: 0.85rem;
        color: #94A3B8;
        margin-bottom: 0.5rem;
    }}

    .verdict-text {{
        font-size: 1.05rem;
        color: #F8FAFC;
        font-weight: 600;
        line-height: 1.5;
    }}

    /* 标签 */
    .badge {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
    }}

    .badge-success {{ background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.25); }}
    .badge-info {{ background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.25); }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.25); }}
    .badge-danger {{ background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.25); }}

    /* 对比区 */
    .compare-section {{
        margin-top: 1.5rem;
    }}

    .compare-card {{
        background: rgba(15, 23, 42, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 20px;
    }}

    .section-badge {{
        display: inline-block;
        padding: 5px 14px;
        border-radius: 999px;
        background: rgba(59, 130, 246, 0.15);
        color: #60A5FA;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 16px;
    }}

    .compare-label {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #94A3B8;
        margin-bottom: 8px;
    }}

    .original-box, .modified-box {{
        background: rgba(2, 6, 23, 0.45);
        border-radius: 12px;
        padding: 18px;
        font-size: 0.92rem;
        line-height: 1.75;
        white-space: pre-wrap;
        color: #CBD5E1;
        min-height: 80px;
        font-family: inherit;
    }}

    .modified-box {{
        border-left: 3px solid #3B82F6;
        color: #F8FAFC;
        background: rgba(59, 130, 246, 0.08);
    }}

    .reason-box {{
        margin-top: 16px;
        padding: 16px 18px;
        border-radius: 12px;
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.20);
        color: #E2E8F0;
        font-size: 0.92rem;
        line-height: 1.7;
    }}

    .reason-label {{
        color: #FBBF24;
        font-weight: 700;
        margin-right: 8px;
    }}

    /* 简历预览 */
    .resume-preview {{
        background: rgba(15, 23, 42, 0.50);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        line-height: 1.75;
        color: #E2E8F0;
        font-size: 0.95rem;
    }}

    .resume-preview h1,
    .resume-preview h2,
    .resume-preview h3 {{
        color: #F8FAFC !important;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }}

    .resume-preview p {{
        margin-bottom: 0.5rem;
    }}

    /* 小字说明 */
    .hint-text {{
        font-size: 0.85rem;
        color: #64748B;
        margin-top: 0.5rem;
    }}

    /* 提示框 */
    .stAlert {{
        background: rgba(15, 23, 42, 0.60) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
    }}

    .stAlert [data-testid="stMarkdownContainer"] p {{
        color: #F8FAFC !important;
    }}

    /* 分隔线 */
    hr {{
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin: 1.5rem 0 !important;
    }}

    /* 响应式 */
    @media (max-width: 768px) {{
        .hero-title {{ font-size: 2.2rem !important; }}
        .stats-row {{ gap: 32px; }}
        .stat-divider {{ display: none; }}
        .step-card {{ min-width: 100%; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_score_section(text: str) -> tuple[str, str]:
    """
    从 AI 输出中提取评分部分
    返回 (评分部分, 剩余内容)
    """
    score_match = re.search(r"#{1,3}\s*简历评分[:：]\s*(\d{1,3}/100)", text)
    if score_match:
        score = score_match.group(1)
        rest = text[score_match.end():].strip()
        return score, rest
    return "", text


def split_analysis_result(text: str) -> tuple[str, str]:
    """
    把 AI 输出分成：分析部分 和 优化后的简历部分
    """
    # 新格式：用标记包裹
    match = re.search(
        r"===OPTIMIZED_RESUME_START===(.*?)===OPTIMIZED_RESUME_END===",
        text,
        re.DOTALL,
    )
    if match:
        analysis_part = text[: match.start()].strip()
        resume_part = match.group(1).strip()
        return analysis_part, resume_part

    # 兼容旧格式
    match = re.search(r"##\s*优化后的简历\s*\n(.*)", text, re.DOTALL)
    if match:
        analysis_part = text[: match.start()].strip()
        resume_part = match.group(1).strip()
        return analysis_part, resume_part

    return text, ""


def parse_change_blocks(text: str) -> list[ChangeBlock]:
    """
    从 AI 输出中解析逐段修改块
    """
    blocks = []
    pattern = re.compile(r"===CHANGE_BLOCK_START===(.*?)===CHANGE_BLOCK_END===", re.DOTALL)
    field_patterns = {
        "section": re.compile(r"===SECTION===\s*(.*?)\s*(?====[A-Z]+===|$)", re.DOTALL),
        "original": re.compile(r"===ORIGINAL===\s*(.*?)\s*(?====[A-Z]+===|$)", re.DOTALL),
        "modified": re.compile(r"===MODIFIED===\s*(.*?)\s*(?====[A-Z]+===|$)", re.DOTALL),
        "reason": re.compile(r"===REASON===\s*(.*?)\s*(?====[A-Z]+===|$)", re.DOTALL),
    }

    for match in pattern.finditer(text):
        raw = match.group(1)
        fields = {}
        for key, field_pattern in field_patterns.items():
            field_match = field_pattern.search(raw)
            fields[key] = field_match.group(1).strip() if field_match else ""

        if any(fields.values()):
            blocks.append(ChangeBlock(**fields))

    return blocks


def get_api_key() -> str:
    """
    获取 DeepSeek API Key
    线上优先从 Streamlit Secrets 读取，本地从 .env 环境变量读取
    """
    # 线上环境：Streamlit Cloud Secrets
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except (KeyError, AttributeError):
        pass

    # 本地环境：.env 文件
    return os.getenv("DEEPSEEK_API_KEY", "")


def get_score_badge(score_num: int) -> str:
    """根据分数返回评级标签 HTML"""
    if score_num >= 85:
        return '<span class="badge badge-success">钻石级</span>'
    elif score_num >= 70:
        return '<span class="badge badge-info">黄金级</span>'
    elif score_num >= 60:
        return '<span class="badge badge-warning">白银级</span>'
    else:
        return '<span class="badge badge-danger">青铜级</span>'


def render_hero():
    """渲染顶部 Hero，复刻参考图风格"""
    st.markdown(
        '''
        <div class="hero-topbar">
            <div class="hero-badge">◆ 简历精修</div>
            <div class="hero-view-toggle">面试官视角</div>
        </div>
        <div class="hero">
            <div class="hero-eyebrow">RESUME OPTIMIZATION</div>
            <div class="hero-title">简历精修优化</div>
            <div class="hero-subtitle">让你的简历 · 不再石沉大海</div>
            <div class="stats-row">
                <div class="stat-item"><div class="stat-number">AI</div><div class="stat-label">实时分析</div></div>
                <div class="stat-divider"></div>
                <div class="stat-item"><div class="stat-number">3 步</div><div class="stat-label">完成优化</div></div>
                <div class="stat-divider"></div>
                <div class="stat-item"><div class="stat-number">24h</div><div class="stat-label">随时可用</div></div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_steps(active: int = 0):
    """渲染三个步骤卡片，active 为当前激活步骤（1/2/3）"""
    steps = [
        ("1", "全面诊断", "逐条审查找出硬伤，出具详细分析报告"),
        ("2", "精修优化", "提炼亮点数据表达，亲手帮你改到满意"),
        ("3", "岗位匹配", "行业定向关键词优化，通过 ATS 机器筛选"),
    ]

    cards_html = '<div class="steps-row">'
    for i, (num, title, desc) in enumerate(steps, 1):
        cls = "step-card"
        if i == active:
            cls += " active"
        elif i < active:
            cls += " completed"
        cards_html += (
            f'<div class="{cls}">'
            f'<div class="step-number">{num}</div>'
            f'<div class="step-title">{title}</div>'
            f'<div class="step-desc">{desc}</div>'
            f'</div>'
        )
    cards_html += '</div>'

    st.markdown(cards_html, unsafe_allow_html=True)


def render_upload_section():
    """渲染上传区"""
    st.markdown('<div class="glass-card" style="text-align: center; max-width: 720px; margin: 0 auto 2rem auto;">', unsafe_allow_html=True)

    st.markdown(
        '''
        <div class="card-title" style="margin-bottom: 0.5rem;">📄 上传你的简历</div>
        <div class="card-subtitle" style="margin-bottom: 1.5rem;">
            支持 PDF 格式。AI 会从 HR 和业务负责人双视角分析，指出问题并输出优化后的完整简历。
        </div>
        ''',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "拖拽或点击上传 PDF 简历",
        type=["pdf"],
        help="请上传文字版 PDF，扫描件/图片可能无法识别",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        st.success(f"已上传：**{uploaded_file.name}**")
    else:
        st.markdown('<div class="hint-text">未选择文件</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return uploaded_file


def render_analyze_button(uploaded_file):
    """渲染分析按钮"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        disabled = uploaded_file is None
        button_label = "开始分析" if uploaded_file else "请先上传简历"
        return st.button(
            button_label,
            type="primary",
            disabled=disabled,
            use_container_width=True,
        )


def render_score_section(score: str, analysis_text: str):
    """渲染评分和摘要"""
    try:
        score_num = int(score.split("/")[0])
    except ValueError:
        score_num = 0

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(
            f'''
            <div class="score-metric">
                <div class="score-number">{score_num}</div>
                <div class="score-label">简历评分 / 100</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col2:
        # 提取评分理由
        reason_match = re.search(r"简历评分[:：]\s*\d{{1,3}}/100\s*\n+(.+?)(?:\n|$)", analysis_text)
        reason = reason_match.group(1).strip() if reason_match else ""

        st.markdown(
            f'''
            <div class="verdict-box">
                <div class="verdict-title">综合评级</div>
                <div class="verdict-text" style="margin-bottom: 0.75rem;">{get_score_badge(score_num)}</div>
                <div class="verdict-title">评分理由</div>
                <div class="verdict-text" style="font-weight: 500; color: #CBD5E1;">{html.escape(reason)}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col3:
        if score_num >= 85:
            advice = "竞争力很强，可直接投递"
        elif score_num >= 70:
            advice = "稍作修改即可投递"
        elif score_num >= 60:
            advice = "建议按诊断重点优化"
        else:
            advice = "需要较大幅度修改"

        st.markdown(
            f'''
            <div class="verdict-box">
                <div class="verdict-title">投递建议</div>
                <div class="verdict-text">{advice}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )


def render_change_block_card(block: ChangeBlock, index: int):
    """渲染单个改前改后对比卡片"""
    section = html.escape(block.section)
    original = html.escape(block.original)
    modified = html.escape(block.modified)
    reason = html.escape(block.reason).replace("\n", "<br>")

    st.markdown(
        f'<div class="compare-card"><div class="section-badge">{section}</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="compare-label">❌ 改前</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="original-box">{original}</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="compare-label">✅ 改后</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="modified-box">{modified}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="reason-box"><span class="reason-label">HR 判断</span>{reason}</div></div>',
        unsafe_allow_html=True,
    )


def render_copy_button(text: str, key: str):
    """渲染原生 JS 一键复制按钮"""
    escaped_text = json.dumps(text)
    html_code = f"""
    <div style="text-align: right; margin-bottom: 12px;">
        <button id="copy-btn-{key}"
                style="
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 8px 16px;
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.15);
                    background: rgba(15, 23, 42, 0.60);
                    color: #CBD5E1;
                    font-size: 0.85rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-family: inherit;
                "
                onmouseover="this.style.background='rgba(59, 130, 246, 0.20)';this.style.color='#FFFFFF';this.style.borderColor='rgba(59, 130, 246, 0.40)'"
                onmouseout="this.style.background='rgba(15, 23, 42, 0.60)';this.style.color='#CBD5E1';this.style.borderColor='rgba(255,255,255,0.15)'"
        >
            📋 复制优化后简历
        </button>
    </div>
    <script>
        document.getElementById('copy-btn-{key}').addEventListener('click', function() {{
            var text = {escaped_text};
            var btn = this;
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(text).then(function() {{
                    btn.innerHTML = '✓ 已复制';
                    btn.style.color = '#34D399';
                    btn.style.borderColor = 'rgba(16, 185, 129, 0.40)';
                    setTimeout(function() {{
                        btn.innerHTML = '📋 复制优化后简历';
                        btn.style.color = '#CBD5E1';
                        btn.style.borderColor = 'rgba(255,255,255,0.15)';
                    }}, 2000);
                }}).catch(function(err) {{
                    console.error('Copy failed:', err);
                    fallbackCopy(text, btn);
                }});
            }} else {{
                fallbackCopy(text, btn);
            }}
            function fallbackCopy(textToCopy, button) {{
                var textarea = document.createElement('textarea');
                textarea.value = textToCopy;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                try {{
                    var successful = document.execCommand('copy');
                    if (successful) {{
                        button.innerHTML = '✓ 已复制';
                        button.style.color = '#34D399';
                        setTimeout(function() {{
                            button.innerHTML = '📋 复制优化后简历';
                            button.style.color = '#CBD5E1';
                        }}, 2000);
                    }} else {{
                        button.innerHTML = '❌ 复制失败';
                    }}
                }} catch (err) {{
                    button.innerHTML = '❌ 复制失败';
                }}
                document.body.removeChild(textarea);
            }}
        }});
    </script>
    """
    components.html(html_code, height=50)


def render_resume_tab(resume_text: str):
    """渲染优化后简历 tab"""
    render_copy_button(resume_text, key="resume-copy")

    st.markdown(
        '''
        <div class="resume-preview">
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(resume_text)
    st.markdown('</div>', unsafe_allow_html=True)


def render_results(result_text: str):
    """渲染完整结果：评分 + 改前改后对比 + 优化后简历"""
    analysis_part, resume_part = split_analysis_result(result_text)
    score, _ = extract_score_section(analysis_part)
    change_blocks = parse_change_blocks(analysis_part)

    # 评分区
    st.markdown('<div class="glass-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
    if score:
        render_score_section(score, analysis_part)
    else:
        st.info("未识别到评分，下面是完整分析结果：")
    st.markdown('</div>', unsafe_allow_html=True)

    # 改前改后对比区
    if change_blocks:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-bottom: 0.25rem;">🔍 逐段精修对比</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle" style="margin-bottom: 1rem;">下面是每一处改动的原文、优化版本和 HR 判断依据。</div>', unsafe_allow_html=True)
        for i, block in enumerate(change_blocks):
            render_change_block_card(block, i)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.info("未识别到结构化的逐段修改，下面是完整分析内容：")
        st.markdown(analysis_part)
        st.markdown('</div>', unsafe_allow_html=True)

    # 完整优化简历
    if resume_part:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="margin-bottom: 1rem;">✨ 完整优化后简历</div>', unsafe_allow_html=True)
        render_resume_tab(resume_part)
        st.markdown('</div>', unsafe_allow_html=True)


def init_session():
    """初始化 session_state"""
    defaults = {
        "stage": "idle",
        "resume_text": "",
        "result": None,
        "error": None,
        "filename": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    init_session()
    render_hero()

    uploaded_file = render_upload_section()
    analyze_button = render_analyze_button(uploaded_file)

    # 如果上传了新文件，清空之前的结果
    if uploaded_file is not None and uploaded_file.name != st.session_state.filename:
        st.session_state.filename = uploaded_file.name
        st.session_state.stage = "idle"
        st.session_state.result = None
        st.session_state.error = None

    # 显示错误并重置
    if st.session_state.error:
        st.error(st.session_state.error)
        st.session_state.error = None

    # 点击分析按钮：校验并进入 parsing 阶段
    if analyze_button:
        api_key = get_api_key()
        if not api_key:
            st.error(
                "⚠️ 未配置 DeepSeek API Key。"
                "线上请在 Streamlit Cloud Secrets 中配置；"
                "本地请在 .env 文件中配置。"
            )
            return

        if uploaded_file is None:
            st.error("⚠️ 请先上传简历 PDF")
            return

        st.session_state.stage = "parsing"
        st.session_state.error = None
        st.rerun()

    # 阶段 1：读取 PDF
    if st.session_state.stage == "parsing":
        render_steps(active=1)
        with st.spinner("正在读取 PDF..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                resume_text = extract_text_from_pdf(tmp_path)
                Path(tmp_path).unlink(missing_ok=True)

                if len(resume_text.strip()) < 50:
                    raise ValueError("简历内容太短，可能 PDF 无法提取文字，请上传文字版 PDF")

                st.session_state.resume_text = resume_text
                st.session_state.stage = "analyzing"
                st.rerun()

            except Exception as e:
                st.session_state.error = f"❌ 简历读取失败：{e}"
                st.session_state.stage = "idle"
                st.rerun()

    # 阶段 2：AI 分析
    if st.session_state.stage == "analyzing":
        render_steps(active=2)
        with st.spinner("AI 正在审阅简历..."):
            try:
                result = analyze_resume(
                    resume_text=st.session_state.resume_text,
                    api_key=get_api_key(),
                    model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
                    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                )
                st.session_state.result = result
                st.session_state.stage = "done"
                st.rerun()

            except Exception as e:
                st.session_state.error = f"❌ AI 分析失败：{e}"
                st.session_state.stage = "idle"
                st.rerun()

    # 阶段 3：完成并展示结果
    if st.session_state.stage == "done":
        render_steps(active=3)
        if st.session_state.result:
            render_results(st.session_state.result)
        else:
            st.session_state.stage = "idle"
            st.rerun()


if __name__ == "__main__":
    main()
